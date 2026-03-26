# OSYM Projesi

Bu proje, `Worde_Yapistir/` klasöründeki sınav metinlerinden soru verisi okuyup analiz üretmek, benzer soru kalıplarını incelemek, konu bazlı çalışma yapmak ve GUI üzerinden soru çözmek için hazırlanmıştır.

Bu sürümde özellikle şu alanlar iyileştirildi:

- Mutlak yol bağımlılıkları azaltıldı.
- Konu adları ortak katalog üzerinden normalize edilmeye başlandı.
- Özet metinleri ayrı bir parser ile işlenir hale geldi.
- Soruları yıl ve konuya göre temiz metin dosyaları olarak dışa aktaran yeni bir araç eklendi.

## Klasör Yapısı

```text
OSYM/
├─ Worde_Yapistir/           # Ham soru metinleri
├─ Gorseller/                # Soru görselleri
├─ Tablolar/                 # Yardımcı tablo/görsel içerikleri
├─ Python_Verisi/            # Python kodları, analiz çıktıları, özetler
│  ├─ analiz_araci.py
│  ├─ dkab_quiz_modern.py
│  ├─ similarity_analyzer.py
│  ├─ project_paths.py
│  ├─ topic_catalog.py
│  ├─ topic_text_parser.py
│  ├─ temiz_metin_aktar.py
│  ├─ dkab_ozet.txt
│  ├─ dkab_kodlamali_ozet.txt
│  └─ temiz_metin/           # Yeni dışa aktarma klasörü
├─ check_sim.py              # Benzerlik analizi için CLI giriş noktası
└─ fix_numbering.py          # Belirli bir dosyada soru numarası düzeltme aracı
```

## Ana Dosyalar ve Görevleri

`check_sim.py`

- Soru havuzunu okuyup benzer soru ve konu eğilimi analizi üretir.
- Komut satırından yıl, ders ve konu filtresi alır.

`Python_Verisi/similarity_analyzer.py`

- Benzerlik puanı, tekrar eden kalıplar, konu sıklıkları ve alt konu ipuçlarını üretir.
- Mevcut sistem heuristik tabanlıdır; semantik embedding modeli kullanılmaz.

`Python_Verisi/analiz_araci.py`

- Tüm sınav dosyalarını okuyup genel analiz raporu üretir.
- Yıl, ders ve konu dağılımı çıkarır.
- Konu kalite raporu üretir.
- Özet dosyaları ile soru konuları arasındaki eşleşme farklarını raporlar.

`Python_Verisi/dkab_quiz_modern.py`

- Tkinter tabanlı ana uygulamadır.
- Soru çözme, filtreleme, analiz ekranı, özet okuma ve TTS akışını yönetir.

`Python_Verisi/project_paths.py`

- Proje içindeki temel klasör yollarını merkezi olarak tanımlar.
- Taşınabilirlik için mutlak yol yerine bu modül kullanılmalıdır.

`Python_Verisi/topic_catalog.py`

- Kanonik soru konu listesini tutar.
- Alias eşlemeleri ve konu normalizasyonu burada yapılır.
- Dosya adı için güvenli konu adı üretir.

`Python_Verisi/topic_text_parser.py`

- `dkab_ozet.txt` ve `dkab_kodlamali_ozet.txt` dosyalarını ayrıştırır.
- Ana başlık, alt başlık, cümle ve konu eşleşmesi bilgisi üretir.

`Python_Verisi/temiz_metin_aktar.py`

- Soruları ders/yıl/konu bazında temiz metin `.txt` dosyalarına dışa aktarır.

## Kurulum

Bu proje için en az Python 3.11 veya tercihen Python 3.12 önerilir.

Windows üzerinde örnek kurulum:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Projede kullanılan modüllerin bir kısmı ortama zaten kurulmuş olabilir. Harici bağımlılık ihtiyacı en çok `dkab_quiz_modern.py` içindeki seslendirme tarafında ortaya çıkar.

## Çalıştırma Komutları

Benzerlik analizi:

```bash
python check_sim.py
python check_sim.py --yil 2024 --ders DKAB
python check_sim.py --yil 2024 --ders DKAB --konu "Fıkıh"
```

Genel analiz raporu:

```bash
python Python_Verisi/analiz_araci.py
```

Temiz metin dışa aktarma:

```bash
python Python_Verisi/temiz_metin_aktar.py --year 2024 --subject DKAB
python Python_Verisi/temiz_metin_aktar.py --year 2024 --subject DKAB --topic "Fıkıh"
```

GUI uygulaması:

```bash
python Python_Verisi/dkab_quiz_modern.py
```

## Konu Sistemi

Projede iki ayrı ama ilişkili konu katmanı vardır:

### 1. Soru Konuları

- Kaynak: soru dosyalarındaki `KONU:` satırları
- Yönetim: `Python_Verisi/topic_catalog.py`
- Özellik:
  - Kanonik ve sınırlı liste kullanılır.
  - Alias adları normalize edilir.
  - Analiz, filtreleme ve dışa aktarma bu kanonik konu adlarıyla çalışır.

Standart soru konu listesi:

- `Kur'an-ı Kerim ve Tecvid`
- `Tefsir`
- `Hadis`
- `Fıkıh`
- `Fıkıh Usulü`
- `Kelam / Akaid`
- `İslam Mezhepleri ve Akımları`
- `İslam Tarihi`
- `Siyer`
- `İslam Kültür ve Medeniyeti`
- `İslam Felsefesi`
- `Din Felsefesi`
- `Din Sosyolojisi`
- `Din Psikolojisi`
- `Din Eğitimi`
- `Dinler Tarihi`
- `İslam Ahlakı ve Tasavvuf`
- `Mezhepler Tarihi`
- `Din Hizmetleri ve Hitabet`

Örnek alias düzeltmeleri:

- `Akaid / Kelam` -> `Kelam / Akaid`
- `Kur'an-i Kerim ve Tecvid` -> `Kur'an-ı Kerim ve Tecvid`
- `İslam Tarihi / Siyer` -> `İslam Tarihi`

### 2. Özet Başlıkları

- Kaynak: `Python_Verisi/dkab_ozet.txt` ve `Python_Verisi/dkab_kodlamali_ozet.txt`
- Yönetim: `Python_Verisi/topic_text_parser.py`
- Özellik:
  - Daha serbest ve daha geniş başlık yapısı kullanılabilir.
  - Bu başlıklar soru konularıyla bire bir aynı olmak zorunda değildir.
  - Ayrı bir katman olarak korunur, ama eşleme tablosu ile kanonik soru konularına bağlanır.

Örnek:

- `İslam İbadet Esasları` başlığı soru tarafında genelde `Fıkıh` ile ilişkilendirilir.
- `İnanç Esasları` başlığı soru tarafında genelde `Kelam / Akaid` ile ilişkilendirilir.

## KONU Yazım Kuralları

Soru dosyalarında her soru bloğunda en fazla bir adet `KONU:` satırı olmalıdır.

Örnek:

```text
DERS: DKAB
KONU: Fıkıh
YIL: 2024

Soru 12:
...
```

Öneriler:

- `KONU:` satırında mümkünse doğrudan kanonik konu adı kullanın.
- Çok özel alt başlıkları `KONU:` yerine soru metni veya açıklama içinde tutun.
- Yeni veri girerken önce `topic_catalog.py` içindeki kanonik listeye uyun.

## Özet Dosyası Mantığı

`dkab_ozet.txt` ve `dkab_kodlamali_ozet.txt` dosyaları GUI içinde okunur ve ayrıştırılır.

Bu turda dosya içeriği yeniden yazılmamıştır. Ancak yeni parser için önerilen biçim şöyledir:

- Ana konu başlığı tek satırda açık olsun.
- Alt başlıklar ayrı satırda olsun.
- Çıkmış soru referansı mümkünse tek biçimde yazılsın.

Örnek önerilen not:

```text
SİYER
HİCRET
(çıkmış sorular: 2024 öabt 12. soru, 2023 öabt 17. soru)
```

## Temiz Metin Dışa Aktarma

Yeni araç: `Python_Verisi/temiz_metin_aktar.py`

Varsayılan çıktı yapısı:

```text
Python_Verisi/temiz_metin/<ders>/<yil>/<konu>.txt
```

Örnek:

```text
Python_Verisi/temiz_metin/DKAB/2024/fikih.txt
```

Dosya içeriğinde şunlar bulunur:

- Ders
- Yıl
- Konu
- Toplam soru sayısı
- Soru numarası
- Temiz soru kök metni

Varsayılan olarak şunlar dışa aktarılmaz:

- Şıklar
- Doğru cevap
- Açıklama
- Görsel notları

## Veri Formatı Özeti

Ham soru dosyaları `Worde_Yapistir/` altında şu kalıba yakın olmalıdır:

```text
DERS: DKAB
KONU: Tefsir
YIL: 2024

Soru 1:
[Soru metni]

A) ...
B) ...
C) ...
D) ...
E) ...

Doğru Cevap: A

---SONRAKI SORU---
```

Parser tarafında bazı bozuk ayraç varyasyonları da tolere edilir; yine de mümkün olduğunca `---SONRAKI SORU---` biçimi kullanılmalıdır.

## Kısa Kullanım Senaryoları

Belirli bir yılın DKAB soru eğilimini incelemek:

```bash
python check_sim.py --yil 2024 --ders DKAB
```

Tüm veri havuzunun konu kalite kontrolünü görmek:

```bash
python Python_Verisi/analiz_araci.py
```

2024 DKAB sorularını konu bazlı temiz metin dosyalarına ayırmak:

```bash
python Python_Verisi/temiz_metin_aktar.py --year 2024 --subject DKAB
```

Özet notlarını GUI üzerinden konu bazlı gezmek ve okutmak:

```bash
python Python_Verisi/dkab_quiz_modern.py
```
