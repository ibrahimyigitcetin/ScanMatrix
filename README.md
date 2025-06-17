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



## Özellik 1: ARP Tabanlı Host Keşfi
- **Açıklama**: Scapy ile hedef ağda ARP taraması yaparak aktif cihazların IP, MAC adresleri ve üretici (vendor) bilgileri toplanır. Tarama süresi yaklaşık 1-2 saniye.
- **Detaylar**: Broadcast çerçeveleri ile tüm ağ taranır, stealth modda MAC spoofing kullanılır.

## Özellik 2: Nmap Ping Tabanlı Host Keşfi
- **Açıklama**: Nmap’in `-sn` parametresiyle ping taraması yapılarak hostların IP ve MAC adresleri tespit edilir. Tarama süresi yaklaşık 4-6 saniye.
- **Detaylar**: MAC adresi bilinmeyen cihazlar için ek üretici sorgusu yapılır.

## Özellik 3: Host Sonuçlarının Birleştirilmesi
- **Açıklama**: ARP ve Nmap taramalarından gelen host bilgileri birleştirilir, çakışmalar giderilir ve IP’ler artan sırayla (ipaddress modülü) sıralanır.
- **Detaylar**: Çıktılar, IP, MAC ve üretici bilgileriyle konsolda renkli olarak gösterilir.

## Özellik 4: Hızlı TCP Port Taraması
- **Açıklama**: Scapy ile hedef IP’lerde SYN taraması yapılır, belirtilen port aralığında (varsayılan 0-65535) açık portlar tespit edilir.
- **Detaylar**: 15’li port gruplarıyla tarama, rasgele kaynak portlar, 0.08 saniye zaman aşımı ve 2 tekrar deneme.

## Özellik 5: Eksik Port Yeniden Taraması
- **Açıklama**: İlk taramada yanıt alınamayan portlar için ek SYN taraması yapılır, doğruluk artırılır.
- **Detaylar**: 0.03 saniye zaman aşımıyla eksik portlar tekrar kontrol edilir.

## Özellik 6: Kullanıcı Tanımlı Tarama Hızı
- **Açıklama**: `--rate` parametresiyle tarama hızı (varsayılan 100 paket/saniye) ayarlanabilir, performans optimize edilir.
- **Detaylar**: ThreadPoolExecutor ile 50 iş parçacığı kullanılarak paralel tarama.

## Özellik 7: Nmap Versiyon Taraması
- **Açıklama**: Açık portlar için Nmap ile `-sS -sV` kullanılarak servis, ürün ve versiyon bilgileri toplanır.
- **Detaylar**: `--version-intensity 1` ile hafif tarama, hızlı sonuçlar.

## Özellik 8: İşletim Sistemi Tespiti
- **Açıklama**: Nmap’in `-O` parametresiyle cihazların işletim sistemi bilgileri (ad, doğruluk, üretici, aile, nesil) tespit edilir.
- **Detaylar**: Her cihaz için osmatch verileri ayrı ayrı işlenir.

## Özellik 9: Zafiyet Taraması
- **Açıklama**: Nmap’in `vuln` betiği ile açık portlarda zafiyetler aranır, CVE, exploit ve zayıf yapılandırmalar filtrelenir.
- **Detaylar**: Betik çıktıları 200 karaktere kadar konsolda gösterilir.

## Özellik 10: NVD CVE Sorgusu
- **Açıklama**: Tespit edilen yazılım ve versiyonlar için NVD API ile CVE sorguları yapılır, en fazla 5 sonuç döndürülür.
- **Detaylar**: API anahtarıyla 50 sonuç sınırı, 0.2 saniye gecikme, önbellekleme ile performans artışı.

## Özellik 11: Proxy Desteği
- **Açıklama**: `--proxies` ile kullanıcı tanımlı proxy listesi üzerinden Nmap taramaları yapılabilir.
- **Detaylar**: Proxy seçimi rasgele yapılır, gizlilik artırılır.

## Özellik 12: Stealth Modu
- **Açıklama**: `--stealth` ile MAC spoofing ve IP fragmantasyonu kullanılarak gizli tarama yapılır.
- **Detaylar**: Tespit edilme riskini azaltmak için rasgele MAC adresleri üretilir.

## Özellik 13: JSON Çıktı Kaydetme
- **Açıklama**: Tarama sonuçları (hostlar, portlar, versiyon, işletim sistemi, zafiyetler) JSON formatında kaydedilir.
- **Detaylar**: Zaman damgasıyla dosya adı, tüm sonuçlar tek dosyada.

## Özellik 14: CSV Çıktı Kaydetme
- **Açıklama**: Sonuçlar ayrı CSV dosyalarına (hostlar, portlar, nmap portları, işletim sistemleri, zafiyetler) kaydedilir.
- **Detaylar**: Her dosya için uygun sütun başlıkları, zaman damgası ile adlandırma.

## Özellik 15: HTML Rapor Oluşturma
- **Açıklama**: Jinja2 ile dinamik HTML raporu oluşturulur, sonuçlar tablo formatında sunulur.
- **Detaylar**: CSS ile stilize edilmiş, okunabilir rapor; hedef, tarama zamanı ve tüm sonuçlar içerir.

## Özellik 16: Ağ Topolojisi Görselleştirme
- **Açıklama**: NetworkX ve Matplotlib ile ağ topolojisi grafiği çizilir, scanner ile cihazlar arasındaki bağlantılar gösterilir.
- **Detaylar**: Açık portlar etiketlenir, PNG formatında kaydedilir.

## Özellik 17: Tkinter GUI Desteği
- **Açıklama**: Kullanıcı dostu GUI ile hedef IP, port aralığı, stealth ve verbose seçenekleri girilebilir.
- **Detaylar**: Gerçek zamanlı durum güncellemeleri, tarama tamamlandığında bildirim.

## Özellik 18: Kapsamlı Loglama
- **Açıklama**: Logging modülü ile INFO, WARNING, ERROR logları konsola ve `network_scanner.log` dosyasına yazılır.
- **Detaylar**: Colorama ile renkli konsol çıktıları, hata ayıklama için verbose modu.

## Özellik 19: Komut Satırı Esnekliği
- **Açıklama**: Argparse ile hedef IP (`-t`), portlar (`--ports`), hız (`--rate`), proxy (`--proxies`), çıktı (`--output`), verbose (`-v`), stealth (`-s`) ve GUI (`--gui`) desteklenir.
- **Detaylar**: Kullanıcı ihtiyaçlarına göre özelleştirilebilir.

## Özellik 20: Kesinti ve Hata Yönetimi
- **Açıklama**: KeyboardInterrupt ile tarama kesildiğinde kısmi sonuçlar kaydedilir, tüm adımlarda hata yakalama yapılır.
- **Detaylar**: Thread-safe işlemler için Lock kullanımı, sağlamlık artırılır.


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
