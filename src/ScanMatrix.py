import scapy.all as scapy
import nmap
import json
import requests
import netifaces
import asyncio
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging
import random
from threading import Lock
import argparse
import csv
import time
import progressbar
import ipaddress
from colorama import Fore, Style, init
from tkinter import Tk, Label, Entry, Button, Checkbutton, IntVar, StringVar, messagebox
from jinja2 import Environment, Template, FileSystemLoader
from typing import List, Dict
import os

# Scapy ayarları: Broadcast uyarılarını bastır ve libpcap kullan
scapy.conf.checkIPaddr = False
scapy.conf.use_pcap = True
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# Colorama'yı başlat
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def search_cve(software: str, version: str) -> List[Dict]:
    """
    NVD API üzerinden yazılım ve versiyon için CVE sorgusu yapar.
    """
    api_key = "#APIKEY"
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    software_clean = software.lower().replace(' ', '').replace('-', '')
    # Versiyonu ana sürüm için sadeleştir (örn. 4.7p1 -> 4.7)
    version_clean = version.split(' ')[0].split('-')[0].split('p')[0]
    params = {
        "keywordSearch": f"{software} {version_clean}",
        "resultsPerPage": 50
    }
    headers = {"apiKey": api_key}
    try:
        time.sleep(0.2)  # API limitine uymak için gecikme
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])
            filtered_cves = []
            for vuln in vulnerabilities:
                cve_data = vuln.get("cve", {})
                description = cve_data.get("descriptions", [{}])[0].get("value", "").lower()
                cpe_match = False
                for cpe_data in cve_data.get("configurations", [{}])[0].get("nodes", []):
                    for cpe_match_data in cpe_data.get("cpeMatch", []):
                        if software_clean in cpe_match_data.get("cpeName", "").lower():
                            cpe_match = True
                            break
                    if cpe_match:
                        break
                if cpe_match or software.lower() in description or version_clean in description:
                    severity = "N/A"
                    metrics = cve_data.get("metrics", {})
                    cvss_v31 = metrics.get("cvssMetricV31", [])
                    cvss_v2 = metrics.get("cvssMetricV2", [])
                    if cvss_v31 and isinstance(cvss_v31, list) and len(cvss_v31) > 0:
                        severity = cvss_v31[0].get("cvssData", {}).get("baseSeverity", "N/A")
                    elif cvss_v2 and isinstance(cvss_v2, list) and len(cvss_v2) > 0:
                        severity = cvss_v2[0].get("baseSeverity", "N/A")
                    filtered_cves.append({
                        "id": cve_data.get("id", "N/A"),
                        "summary": cve_data.get("descriptions", [{}])[0].get("value", "No description"),
                        "severity": severity
                    })
            if filtered_cves:
                logger.info(f"{Fore.GREEN}[+] {software} {version_clean} için {len(filtered_cves)} CVE bulundu.{Fore.RESET}")
                return filtered_cves[:5]
            logger.warning(f"{Fore.YELLOW}[-] {software} {version_clean} için CVE bulunamadı.{Fore.RESET}")
            return []
        else:
            logger.error(f"{Fore.RED}[-] CVE API isteği başarısız: {response.status_code}{Fore.RESET}")
            return []
    except Exception as e:
        logger.error(f"{Fore.RED}[-] CVE sorgulama hatası: {str(e)}{Fore.RESET}")
        return []

class NetworkScanner:
    def __init__(self, target: str, ports: str = "0-65535", rate: int = 100, proxy_list: List[str] = None, verbose: bool = False, stealth: bool = False):
        self.target = target
        self.ports = ports
        self.rate = rate
        self.interface = self._get_default_interface()
        self.proxy_list = proxy_list or []
        self.verbose = verbose
        self.stealth = stealth
        self.results = {
            'hosts': [],
            'ports': [],
            'mac_info': [],
            'topology': [],
            'version_info': [],
            'os_info': [],
            'vuln_info': []
        }
        self.lock = Lock()
        self.nm = nmap.PortScanner()
        self.start_time = datetime.now()
        self.progress = None
        self.cve_cache = {}  # Tekrarlı CVE sorgularını önlemek için önbellek

    def _get_default_interface(self) -> str:
        try:
            gateways = netifaces.gateways()
            default_gateway = gateways.get('default', {}).get(netifaces.AF_INET)
            if default_gateway:
                return default_gateway[1]
            raise ValueError("No default interface found.")
        except Exception as e:
            logger.error(f"Failed to get default interface: {e}")
            raise

    def arp_scan(self) -> List[Dict]:
        logger.info(f"Starting ARP scan on {self.target}")
        try:
            arp_request = scapy.ARP(pdst=self.target)
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            if self.stealth:
                broadcast.src = self._spoof_mac()
            arp_request_broadcast = broadcast / arp_request
            answered_list = scapy.srp(arp_request_broadcast, timeout=0.3, retry=2, verbose=0)[0]

            hosts = []
            self.progress = progressbar.ProgressBar(maxval=len(answered_list))
            self.progress.start()
            for i, (sent, received) in enumerate(answered_list):
                mac = received.hwsrc
                ip = received.psrc
                vendor = self._get_mac_vendor(mac)
                hosts.append({'ip': ip, 'mac': mac, 'vendor': vendor})
                self.results['mac_info'].append({'ip': ip, 'mac': mac, 'vendor': vendor})
                self.results['topology'].append({'source': 'scanner', 'target': ip})
                self.progress.update(i + 1)
            self.progress.finish()

            logger.info(f"Found {len(hosts)} hosts via ARP")
            return hosts
        except Exception as e:
            logger.error(f"ARP scan failed: {e}")
            return []

    def _spoof_mac(self) -> str:
        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])

    def _get_mac_vendor(self, mac: str) -> str:
        try:
            oui = mac.upper()[:8].replace(':', '')
            response = requests.get(f"https://api.macvendors.com/{oui}", timeout=5)
            return response.text if response.status_code == 200 else "Unknown"
        except Exception as e:
            logger.error(f"Error fetching MAC vendor: {e}")
            return "Unknown"

    def nmap_ping_scan(self) -> List[Dict]:
        logger.info("Starting Nmap ping scan")
        try:
            self.nm.scan(hosts=self.target, arguments='-sn')
            hosts_list = self.nm.all_hosts()
            hosts = []
            for host in hosts_list:
                mac = self.nm[host]['addresses'].get('mac', 'Unknown')
                vendor = self._get_mac_vendor(mac) if mac != 'Unknown' else 'Unknown'
                hosts.append({'ip': host, 'mac': mac, 'vendor': vendor})
            logger.info(f"Found {len(hosts)} hosts via Nmap ping scan")
            return hosts
        except Exception as e:
            logger.error(f"Nmap ping scan failed: {e}")
            return []

    async def discover_hosts(self) -> List[Dict]:
        logger.info("Starting host discovery")
        try:
            scapy.arping(self.target, timeout=0.05, verbose=0)
        except Exception as e:
            logger.warning(f"ARP pre-scan failed: {e}")

        arp_hosts = await asyncio.to_thread(self.arp_scan)
        nmap_hosts = await asyncio.to_thread(self.nmap_ping_scan)
        
        all_hosts = {}
        for host in arp_hosts:
            all_hosts[host['ip']] = host
        for host in nmap_hosts:
            if host['ip'] not in all_hosts:
                all_hosts[host['ip']] = host
            elif all_hosts[host['ip']]['mac'] == 'Unknown' and host['mac'] != 'Unknown':
                all_hosts[host['ip']]['mac'] = host['mac']
                all_hosts[host['ip']]['vendor'] = host['vendor']
        
        active_hosts = sorted(all_hosts.values(), key=lambda x: ipaddress.ip_address(x['ip']))
        logger.info(f"{Fore.CYAN}Total active hosts found: {len(active_hosts)}{Fore.RESET}")
        logger.info(f"{Fore.CYAN}Active hosts: {', '.join(host['ip'] for host in active_hosts)}{Fore.RESET}")
        self.results['hosts'] = active_hosts
        return active_hosts

    async def port_scan(self) -> List[Dict]:
        logger.info(f"Starting port scan on {self.target} for ports {self.ports}")
        live_hosts = [host['ip'] for host in self.results['hosts']]
        if not live_hosts:
            logger.warning("No host IPs found in the target network")
            return []
        logger.info(f"Scanning {len(live_hosts)} IPs")
        ports_list = self._parse_ports(self.ports)
        logger.info(f"Scanning {len(ports_list)} ports per host")
        open_ports = []

        async def scan_host(ip: str):
            chunk_size = 15
            scanned_ports = set()
            for i in range(0, len(ports_list), chunk_size):
                chunk = ports_list[i:i + chunk_size]
                try:
                    src_port = random.randint(1024, 65535)
                    pkts = [scapy.IP(dst=ip) / scapy.TCP(sport=src_port, dport=port, flags="S") for port in chunk]
                    ans, _ = await asyncio.to_thread(scapy.sr, pkts, timeout=0.08, retry=2, verbose=0)
                    for sent, received in ans:
                        if received.haslayer(scapy.TCP) and received[scapy.TCP].flags == 0x12:
                            port = sent[scapy.TCP].dport
                            with self.lock:
                                open_ports.append({'ip': ip, 'port': port, 'state': 'open', 'protocol': 'tcp'})
                                logger.info(f"{Fore.GREEN}Port {port} open on {ip} (TCP){Fore.RESET}")
                    scanned_ports.update(chunk)
                except Exception:
                    pass

                # Eksik portlar için ek tarama
                missing_ports = [p for p in chunk if p not in scanned_ports]
                if missing_ports:
                    try:
                        src_port = random.randint(1024, 65535)
                        pkts = [scapy.IP(dst=ip) / scapy.TCP(sport=src_port, dport=port, flags="S") for port in missing_ports]
                        ans, _ = await asyncio.to_thread(scapy.sr, pkts, timeout=0.03, retry=2, verbose=0)
                        for sent, received in ans:
                            if received.haslayer(scapy.TCP) and received[scapy.TCP].flags == 0x12:
                                port = sent[scapy.TCP].dport
                                with self.lock:
                                    open_ports.append({'ip': ip, 'port': port, 'state': 'open', 'protocol': 'tcp'})
                                    logger.info(f"{Fore.GREEN}Port {port} open on {ip} (TCP){Fore.RESET}")
                    except Exception:
                        pass

        try:
            with ThreadPoolExecutor(max_workers=50) as executor:
                tasks = [scan_host(ip) for ip in live_hosts]
                await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Port scan failed: {e}")

        self.results['ports'] = sorted(open_ports, key=lambda x: (x['ip'], x['port']))
        return self.results['ports']

    def _parse_ports(self, ports: str) -> List[int]:
        try:
            if '-' in ports:
                start, end = map(int, ports.split('-'))
                return list(range(max(0, start), min(65535, end + 1)))
            return [int(p) for p in ports.split(',') if 0 <= int(p) <= 65535]
        except Exception as e:
            logger.error(f"Invalid port specification: {ports} - {e}")
            return []

    def nmap_version_scan(self) -> List[Dict]:
        logger.info("Starting Nmap version, OS, and vulnerability scan for detected open ports")
        version_info = []
        os_info = []
        vuln_info = []
        host_ports = {}
        
        # Host ve portları grupla
        for port in self.results['ports']:
            ip = port['ip']
            if ip not in host_ports:
                host_ports[ip] = []
            host_ports[ip].append(port['port'])

        self.progress = progressbar.ProgressBar(maxval=len(host_ports))
        self.progress.start()
        for i, (ip, ports) in enumerate(sorted(host_ports.items())):
            try:
                ports_str = ','.join(map(str, sorted(ports)))
                proxy_arg = f"--proxy {random.choice(self.proxy_list)}" if self.proxy_list else ""
                # Kapsamlı betikler ve optimize parametreler
                try:
                    self.nm.scan(ip, ports_str, arguments=f"-sS -sV -O --version-intensity 1 -Pn {proxy_arg} --min-rate 100 --max-rate 500 --max-retries 5 --host-timeout 600s --script-timeout 30s --script vuln")
                except nmap.PortScannerError as e:
                    logger.error(f"Nmap scan failed for {ip}:{ports_str}: {str(e)}")
                    continue
                if ip not in self.nm.all_hosts():
                    logger.warning(f"No Nmap data returned for {ip}:{ports_str}. Falling back to Scapy results.")
                    continue
                for host in self.nm.all_hosts():
                    # Her port için ayrı hata yakalama
                    for proto in self.nm[host].all_protocols():
                        for scanned_port in self.nm[host][proto].keys():
                            try:
                                service = self.nm[host][proto][scanned_port].get('name', 'unknown')
                                product = self.nm[host][proto][scanned_port].get('product', 'unknown')
                                version = self.nm[host][proto][scanned_port].get('version', 'unknown')
                                with self.lock:
                                    version_info.append({
                                        'ip': host,
                                        'port': scanned_port,
                                        'protocol': proto,
                                        'service': service,
                                        'product': product,
                                        'version': version
                                    })
                                logger.info(f"Nmap verified port {scanned_port}/{proto} on {host}")
                                # CVE sorgusu
                                if product != 'unknown' and version != 'unknown':
                                    cache_key = f"{product.lower()}:{version}"
                                    if cache_key not in self.cve_cache:
                                        cve_results = search_cve(product, version)
                                        self.cve_cache[cache_key] = cve_results
                                    for cve in self.cve_cache[cache_key]:
                                        with self.lock:
                                            vuln_info.append({
                                                'ip': host,
                                                'port': scanned_port,
                                                'script_id': f'cve_api_{cve["id"]}',
                                                'output': f'{cve["summary"]} (Severity: {cve["severity"]})'
                                            })
                                            logger.info(f"CVE bulundu: {cve['id']} on {host}:{scanned_port}")
                            except Exception as e:
                                logger.error(f"Failed to process version info for {host}:{scanned_port}/{proto}: {e}")
                                continue
                            # Nmap zafiyet bilgileri
                            try:
                                if 'script' in self.nm[host][proto][scanned_port]:
                                    for script_id, output in self.nm[host][proto][scanned_port]['script'].items():
                                        if any(keyword in output.lower() for keyword in ['cve', 'vulnerable', 'exploit', 'weak', 'insecure', 'issue']):
                                            with self.lock:
                                                vuln_info.append({
                                                    'ip': host,
                                                    'port': scanned_port,
                                                    'script_id': script_id,
                                                    'output': output[:200]
                                                })
                                            logger.info(f"Zafiyet bulundu: {script_id} on {host}:{scanned_port}")
                                        else:
                                            logger.debug(f"Betik çıktısı filtreden geçmedi: {script_id} on {host}:{scanned_port}: {output[:100]}")
                            except Exception as e:
                                logger.error(f"Failed to process vuln info for {host}:{scanned_port}/{proto}: {e}")
                    # OS bilgileri
                    if 'osmatch' in self.nm[host] and isinstance(self.nm[host]['osmatch'], list):
                        for osmatch in self.nm[host]['osmatch']:
                            try:
                                osclass = osmatch.get('osclass', [{}])[0] if isinstance(osmatch.get('osclass', [{}]), list) else osmatch.get('osclass', {})
                                with self.lock:
                                    os_info.append({
                                        'ip': host,
                                        'os_name': osmatch.get('name', 'unknown'),
                                        'os_accuracy': osmatch.get('accuracy', 'unknown'),
                                        'os_vendor': osclass.get('vendor', 'unknown'),
                                        'os_family': osclass.get('osfamily', 'unknown'),
                                        'os_gen': osclass.get('osgen', 'unknown')
                                    })
                            except Exception as e:
                                logger.error(f"Failed to process OS info for {host}: {e}")
                logger.info(f"Nmap scan completed for {ip}:{ports_str}")
            except Exception as e:
                logger.error(f"Nmap version/OS/vuln scan failed for {ip}:{ports_str}: {e}")
            self.progress.update(i + 1)
        self.progress.finish()

        self.results['version_info'] = sorted(version_info, key=lambda x: (x['ip'], x['port']))
        self.results['os_info'] = sorted(os_info, key=lambda x: x['ip'])
        self.results['vuln_info'] = sorted(vuln_info, key=lambda x: (x['ip'], x['port']))
        return version_info

    def visualize_topology(self):
        logger.info("Generating network topology visualization")
        try:
            G = nx.Graph()
            for host in self.results['hosts']:
                G.add_node(host['ip'], label=f"{host['ip']}\n{host['vendor']}")
            for port in self.results['ports']:
                G.add_edge('scanner', port['ip'], label=f"Port {port['port']}")

            pos = nx.spring_layout(G)
            plt.figure(figsize=(10, 8))
            nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=10)
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
            plt.savefig(f"topology_{self.start_time.strftime('%Y%m%d_%H%M%S')}.png")
            plt.close()
            logger.info("Topology visualization saved as PNG")
        except Exception as e:
            logger.error(f"Failed to generate topology visualization: {e}")

    def generate_html_report(self):
        logger.info("Generating HTML report")
        try:
            env = Environment(loader=FileSystemLoader('.'))
            template = env.from_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Network Scan Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333; }
                    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                </style>
            </head>
            <body>
                <h1>Network Scan Report</h1>
                <p><strong>Target:</strong> {{ target }}</p>
                <p><strong>Scan Time:</strong> {{ scan_time }}</p>
                <p><strong>Total Hosts:</strong> {{ hosts|length }}</p>
                <h2>Active Hosts</h2>
                <table>
                    <tr><th>IP</th><th>MAC</th><th>Vendor</th></tr>
                    {% for host in hosts %}
                    <tr><td>{{ host.ip }}</td><td>{{ host.mac }}</td><td>{{ host.vendor }}</td></tr>
                    {% endfor %}
                </table>
                <h2>Scapy Detected Ports</h2>
                <table>
                    <tr><th>IP</th><th>Port</th><th>Protocol</th><th>State</th></tr>
                    {% for port in ports %}
                    <tr><td>{{ port.ip }}</td><td>{{ port.port }}</td><td>{{ port.protocol }}</td><td>{{ port.state }}</td></tr>
                    {% endfor %}
                </table>
                <h2>Nmap Verified Ports</h2>
                <table>
                    <tr><th>IP</th><th>Port</th><th>Protocol</th><th>State</th><th>Service</th><th>Product</th><th>Version</th></tr>
                    {% for port in version_info %}
                    <tr><td>{{ port.ip }}</td><td>{{ port.port }}</td><td>{{ port.protocol }}</td><td>open</td><td>{{ port.service }}</td><td>{{ port.product }}</td><td>{{ port.version }}</td></tr>
                    {% endfor %}
                </table>
                <h2>Operating Systems</h2>
                <table>
                    <tr><th>IP</th><th>OS Name</th><th>Accuracy</th><th>Vendor</th><th>Family</th><th>Generation</th></tr>
                    {% for os in os_info %}
                    <tr><td>{{ os.ip }}</td><td>{{ os.os_name }}</td><td>{{ os.os_accuracy }}</td><td>{{ os.os_vendor }}</td><td>{{ os.os_family }}</td><td>{{ os.os_gen }}</td></tr>
                    {% endfor %}
                </table>
                <h2>Vulnerabilities</h2>
                <table>
                    <tr><th>IP</th><th>Port</th><th>Script ID</th><th>Output</th></tr>
                    {% for vuln in vuln_info %}
                    <tr><td>{{ vuln.ip }}</td><td>{{ vuln.port }}</td><td>{{ vuln.script_id }}</td><td>{{ vuln.output }}</td></tr>
                    {% endfor %}
                </table>
            </body>
            </html>
            """)
            report_data = {
                'target': self.target,
                'scan_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'hosts': self.results['hosts'],
                'ports': self.results['ports'],
                'version_info': self.results['version_info'],
                'os_info': self.results['os_info'],
                'vuln_info': self.results['vuln_info']
            }
            report_html = template.render(**report_data)
            report_file = f"report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.html"
            with open(report_file, 'w') as f:
                f.write(report_html)
            logger.info(f"HTML report saved as {report_file}")
            return report_file
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return None

    def print_results(self):
        logger.info(f"{Fore.CYAN}=== Scan Results ==={Fore.RESET}")
        print(f"\n{Fore.CYAN}Active Hosts:{Fore.RESET}")
        print(f"{Fore.WHITE}{'IP':<16} {'MAC':<18} {'Vendor':<20}{Fore.RESET}")
        print(f"{Fore.WHITE}{'-'*16} {'-'*18} {'-'*20}{Fore.RESET}")
        for host in self.results['hosts']:
            print(f"{Fore.GREEN}{host['ip']:<16} {host['mac']:<18} {host['vendor'][:19]:<20}{Fore.RESET}")

        print(f"\n{Fore.CYAN}Scapy Detected Ports:{Fore.RESET}")
        print(f"{Fore.WHITE}{'IP':<16} {'Port':<8} {'Protocol':<10} {'State':<12}{Fore.RESET}")
        print(f"{Fore.WHITE}{'-'*16} {'-'*8} {'-'*10} {'-'*12}{Fore.RESET}")
        for port in self.results['ports']:
            color = Fore.GREEN if port['protocol'] == 'tcp' else Fore.YELLOW
            print(f"{color}{port['ip']:<16} {port['port']:<8} {port['protocol']:<10} {port['state']:<12}{Fore.RESET}")

        print(f"\n{Fore.CYAN}Nmap Verified Ports:{Fore.RESET}")
        print(f"{Fore.WHITE}{'IP':<16} {'Port':<8} {'Protocol':<10} {'State':<12} {'Service':<12} {'Product':<20} {'Version':<15}{Fore.RESET}")
        print(f"{Fore.WHITE}{'-'*16} {'-'*8} {'-'*10} {'-'*12} {'-'*12} {'-'*20} {'-'*15}{Fore.RESET}")
        for port in self.results['version_info']:
            color = Fore.GREEN if port['protocol'] == 'tcp' else Fore.YELLOW
            print(f"{color}{port['ip']:<16} {port['port']:<8} {port['protocol']:<10} open{' '*8} {port['service'][:11]:<12} {port['product'][:19]:<20} {port['version'][:14]:<15}{Fore.RESET}")

        print(f"\n{Fore.CYAN}Operating Systems:{Fore.RESET}")
        print(f"{Fore.WHITE}{'IP':<16} {'OS Name':<30} {'Accuracy':<10} {'Vendor':<15} {'Family':<15} {'Generation':<15}{Fore.RESET}")
        print(f"{Fore.WHITE}{'-'*16} {'-'*30} {'-'*10} {'-'*15} {'-'*15} {'-'*15}{Fore.RESET}")
        for os in self.results['os_info']:
            print(f"{Fore.GREEN}{os['ip']:<16} {os['os_name'][:29]:<30} {os['os_accuracy']:<10} {os['os_vendor'][:14]:<15} {os['os_family'][:14]:<15} {os['os_gen'][:14]:<15}{Fore.RESET}")

        print(f"\n{Fore.CYAN}Vulnerabilities:{Fore.RESET}")
        print(f"{Fore.WHITE}{'IP':<16} {'Port':<8} {'Script ID':<20} {'Output':<50}{Fore.RESET}")
        print(f"{Fore.WHITE}{'-'*16} {'-'*8} {'-'*20} {'-'*50}{Fore.RESET}")
        for vuln in self.results['vuln_info']:
            print(f"{Fore.RED}{vuln['ip']:<16} {vuln['port']:<8} {vuln['script_id'][:19]:<20} {vuln['output'][:49]:<50}{Fore.RESET}")

    def save_results(self, output_format: str = 'json'):
        try:
            timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
            output_files = []
            if output_format in ('json', 'both'):
                json_file = f'scan_results_{timestamp}.json'
                with open(json_file, 'w') as f:
                    json.dump(self.results, f, indent=2)
                output_files.append(json_file)
            if output_format in ('csv', 'both'):
                hosts_file = f'scan_results_hosts_{timestamp}.csv'
                with open(hosts_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['ip', 'mac', 'vendor'])
                    writer.writeheader()
                    writer.writerows(self.results['hosts'])
                output_files.append(hosts_file)
                ports_file = f'scan_results_ports_{timestamp}.csv'
                with open(ports_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['ip', 'port', 'state', 'protocol'])
                    writer.writeheader()
                    writer.writerows(self.results['ports'])
                output_files.append(ports_file)
                nmap_ports_file = f'scan_results_nmap_ports_{timestamp}.csv'
                with open(nmap_ports_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['ip', 'port', 'state', 'protocol', 'service', 'product', 'version'])
                    writer.writeheader()
                    writer.writerows(self.results['version_info'])
                output_files.append(nmap_ports_file)
                os_file = f'scan_results_os_{timestamp}.csv'
                with open(os_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['ip', 'os_name', 'os_accuracy', 'os_vendor', 'os_family', 'os_gen'])
                    writer.writeheader()
                    writer.writerows(self.results['os_info'])
                output_files.append(os_file)
                vuln_file = f'scan_results_vuln_{timestamp}.csv'
                with open(vuln_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['ip', 'port', 'script_id', 'output'])
                    writer.writeheader()
                    writer.writerows(self.results['vuln_info'])
                output_files.append(vuln_file)
            logger.info(f"Results saved in {output_format} format")
            return output_files
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return []

    async def run(self):
        logger.info("Starting network scan")
        try:
            await self.discover_hosts()
            await self.port_scan()
            self.nmap_version_scan()
            self.print_results()
            output_files = self.save_results('both')
            self.visualize_topology()
            html_report = self.generate_html_report()
            if html_report:
                output_files.append(html_report)
            logger.info(f"Scan completed in {datetime.now() - self.start_time}")
            return self.results
        except KeyboardInterrupt:
            logger.warning("Scan interrupted by user; saving partial results")
            self.save_results('both')
            self.print_results()
            return self.results
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return self.results

class ScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Scanner")
        self.root.geometry("600x400")

        Label(root, text="Target IP/Range:").grid(row=0, column=0, padx=5, pady=5)
        self.target_entry = Entry(root, width=30)
        self.target_entry.grid(row=0, column=1, padx=5, pady=5)

        Label(root, text="Port Range (e.g., 0-1000):").grid(row=1, column=0, padx=5, pady=5)
        self.ports_entry = Entry(root, width=30)
        self.ports_entry.grid(row=1, column=1, padx=5, pady=5)

        self.stealth_var = IntVar()
        Checkbutton(root, text="Stealth Mode", variable=self.stealth_var).grid(row=2, column=0, padx=5, pady=5)

        self.verbose_var = IntVar()
        Checkbutton(root, text="Verbose Output", variable=self.verbose_var).grid(row=2, column=1, padx=5, pady=5)

        self.status_var = StringVar(value="Ready")
        Label(root, textvariable=self.status_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        Button(root, text="Start Scan", command=self.start_scan).grid(row=4, column=0, columnspan=2, pady=10)

    def start_scan(self):
        target = self.target_entry.get()
        ports = self.ports_entry.get() or "0-65535"
        stealth = bool(self.stealth_var.get())
        verbose = bool(self.verbose_var.get())

        if not target:
            messagebox.showerror("Error", "Target IP/Range is required!")
            return

        self.status_var.set("Scanning...")
        self.root.update()

        async def run_scan():
            scanner = NetworkScanner(target=target, ports=ports, stealth=stealth, verbose=verbose)
            results = await scanner.run()
            self.status_var.set("Scan Completed!")
            messagebox.showinfo("Success", f"Scan completed! Results saved in scan_results_{scanner.start_time.strftime('%Y%m%d_%H%M%S')}.json/csv")

        asyncio.run(run_scan())

def main():
    parser = parse_arguments()
    if parser.gui:
        root = Tk()
        app = ScannerGUI(root)
        root.mainloop()
    else:
        async def run_scan():
            scanner = NetworkScanner(
                target=parser.target,
                ports=parser.ports,
                rate=parser.rate,
                proxy_list=parser.proxies,
                verbose=parser.verbose,
                stealth=parser.stealth
            )
            await scanner.run()

        asyncio.run(run_scan())

def parse_arguments():
    parser = argparse.ArgumentParser(description="Network Scanner for Host and Port Detection")
    parser.add_argument('-t', '--target', required=True, help="Target IP or range (e.g., 192.168.147.0/24)")
    parser.add_argument('-p', '--proxies', nargs='*', default=[], help="List of proxy servers (e.g., http://proxy:8080)")
    parser.add_argument('--ports', default="0-65535", help="Port range or list (e.g., 0-1000 or 80,443)")
    parser.add_argument('--rate', type=int, default=100, help="Initial scan rate (packets per second)")
    parser.add_argument('--output', choices=['json', 'csv', 'both'], default='both', help="Output format")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    parser.add_argument('-s', '--stealth', action='store_true', help="Enable stealth mode (IP fragmentation, MAC spoofing)")
    parser.add_argument('--gui', action='store_true', help="Run with GUI")
    return parser.parse_args()

if __name__ == "__main__":
    main()
