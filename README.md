<div align="center">
  <img src="https://img.shields.io/github/languages/count/samethankull/Project?style=flat-square&color=blueviolet" alt="Language Count">
  <img src="https://img.shields.io/github/languages/top/samethankull/Project?style=flat-square&color=1e90ff" alt="Top Language">
  <img src="https://img.shields.io/github/last-commit/samethankull/Project?style=flat-square&color=ff69b4" alt="Last Commit">
  <img src="https://img.shields.io/github/license/samethankull/Project?style=flat-square&color=yellow" alt="License">
  <img src="https://img.shields.io/badge/Status-Active-green?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/Contributions-Welcome-brightgreen?style=flat-square" alt="Contributions">
</div>

# ScanMatrix
Python tabanlı ağ güvenliği aracı, ağ tarama ve analiz süreçlerini otomatikleştiren, kapsamlı ve kullanıcı dostu bir çözümdür. Araç, açık port tarama, banner grabbing, sistem ve versiyon bilgisi toplama , CVE veritabanından güvenlik açığı tarama gibi özellikler sunar. Grafana tarzı görselleştirme ile veriler düzenli ve görsel olarak sunulurken, sistem güvenilirliğini low, medium, high, critical olarak derecelendirir. MAC adresi tespiti ve ilk 6 hanesinden hizmet türü belirleme, firewall varlığı kontrolü ve proxy listeleriyle firewall bypass yetenekleri içerir. Esnek, güvenli ve kullanıcı odaklı bu araç, ağ güvenliği analizlerini kolaylaştırır ve potansiyel tehditleri proaktif bir şekilde tespit eder..

---

## Features / Özellikler

- *Feature 1:*  Host Keşfi
-  *Özellik 1: *ARP Taraması: Scapy ile IP/MAC/vendor, stealth mod, ~1-2 sn.
  Nmap Ping: Nmap -sn ile host/MAC, ~4-6 sn.
  Sıralı Çıktı: IP’ler artan sırayla..*
- *Feature 2:*  Port Taraması  
  *Özellik 2: TCP SYN: Scapy, 15 port/grup, timeout 0.08/0.03 sn, ~0.4-3 sn.
  Atlamasız: Retry=2 ile eksik port tarama.
Sıralı: IP/port artan sırayla.*
- *Feature 3:* Servis ve OS Tespiti.  
  *Özellik 3: Nmap Taraması: -sV (servis), -O (OS), proxy, ~3-5 sn.
  Veri İşleme: Servis/OS bilgisi, hata kontrolü.
  Sıralı: IP/port/OS sıralı.
- *Feature 4:*  Zafiyet Taraması
- *Özellik 4:  Nmap NSE: CVE tespiti, ~5-10 sn.
  Çıktı: Kırmızı tablo, CSV/HTML/JSON.
  Hata Önleme: NSE hata yakalama.  
- *Feature 5:*  Vendor Bilgileri 
- *Özellik 5: API: macvendors.com ile vendor, ~0.1 sn.
  Hata Yedekleme: Hata durumunda "Unknown".
- *Feature 6:*  Çıktı ve Raporlama
- *Özellik 6: Terminal: Yeşil/sarı bilgi, kırmızı zafiyet, cyan başlık.
    JSON: Dosyaya yazılır (hosts, ports, vuln).
    CSV: Host/port/OS/vuln için ayrı dosyalar.
    HTML: Jinja2 ile biçimli rapor.
    Topoloji: NetworkX ile PNG, ~0.5 sn.
- *Feature 7:*  Güvenlik ve Gizlilik
- *Özellik 7:Stealth Modu: Sahte MAC ile gizlilik.
  Proxy: Nmap için proxy desteği.
  Loglama: Hatalar network_scanner.log’a.
- *Feature 8:* Hata Önleme ve Stabilite
- *Özellik 8: Hata Yakalama: Tarama/API için try-except.
  Nmap Kontrolü: Veri tipi hataları önleme.
  İlerleme Çubuğu: Progressbar ile takip



---

## Team / Ekip

- Member 1 - Name Surname:  
  Ad Soyad: Samethan Kül
- Member 2 - Name Surname:   
  Ad Soyad: Eren Ergün
- Member 3 - Name Surname:  
  Ad Soyad: İbrahim Yiğit Çetin
---

## Roadmap / Yol Haritası

See our plans in [ROADMAP.md](ROADMAP.md).  
Yolculuğu görmek için [ROADMAP.md](ROADMAP.md) dosyasına göz atın.

---

## Research / Araştırmalar

| Topic / Başlık        | Link                                    | Description / Açıklama                        |
|-------------------------|-----------------------------------------|------------------------------------------------|
| ScanMatrix DeepSearch    | [researchs/deepsearch.01.result.md](researchs/deepsearch.01.result.md) | Araç hakkında deepsearch bilgisi.* |
| Example Research Pdf  | [researchs/deepsearch.01.md](researchs/deepsearch.01.result.pdf) | Araştırma sonucunda oluşturulan pdf dosyası* |
| Add More Research       | Link to your other research files     | Description of the research                  |

---

## Installation / Kurulum
1. *Clone the Repository / *Depoyu Klonlayın:  
   bash
   [git clone https://github.com/samethankull/ScanMatrix.git]
   cd ScanMatrix
   

2. *Set Up Virtual Environment / *Sanal Ortam Kurulumu** (Recommended):  
   bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   

3. *Install Dependencies / *Bağımlılıkları Yükleyin:  
   bash
   pip install -r requirements.txt
   

---

## Usage / Kullanım

Run the project:  
 bash
   python ScanMatrix.py
   



*Steps*:  
1. Prepare input data (explain data needed).  
2. Run the script with arguments (explain key arguments).  
3. Check output (explain where to find results).  

Adımlar:  
1. Giriş verilerini hazırlayın (ne tür verilere ihtiyaç duyulduğunu açıklayın).  
2. Betiği argümanlarla çalıştırın (önemli argümanları açıklayın).  
3. Çıktıyı kontrol edin (sonuçları nerede bulacağınızı açıklayın).

---

## Contributing / Katkıda Bulunma

We welcome contributions! To help:  
1. Fork the repository.  
2. Clone your fork (git clone git@github.com:YOUR_USERNAME/YOUR_REPO.git).  
3. Create a branch (git checkout -b feature/your-feature).  
4. Commit changes with clear messages.  
5. Push to your fork (git push origin feature/your-feature).  
6. Open a Pull Request.  

Follow our coding standards (see [CONTRIBUTING.md](CONTRIBUTING.md)).  

Topluluk katkilerini memnuniyetle karşılıyoruz! Katkıda bulunmak için yukarıdaki adımları izleyin ve kodlama standartlarımıza uyun.

---

## License / Lisans

Licensed under the [MIT License](LICENSE.md).  
MIT Lisansı altında lisanslanmıştır.

---

## Acknowledgements / Teşekkürler (Optional)

Thanks to:  
- Awesome Library: For enabling X.  
- Inspiration Source.  
- Special thanks to...  

Teşekkürler: Harika kütüphaneler ve ilham kaynakları için.

---

## Contact / İletişim (Optional)

[Samethan Kül] - [samethan.kul@istinye.edu.tr]

[Eren Ergün] - [eren.ergun@istinye.edu.tr] 

[İbrahim Yiğit Çetin] - [ibrahimyigit.cetin@istinye.edu.tr] 
Found a bug? Open an issue.  

Proje Sorumlusu: [Samethan Kül] - [samehan.kul@istinye.edu.tr]. Hata bulursanız bir sorun bildirin.

---

Replace placeholders (e.g., YOUR_USERNAME/YOUR_REPO) with your project details.
