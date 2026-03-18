## OSYM klasör yapısı

Bu klasör yapısı, soruları önce Word’e düzenli yapıştırmak, sonra aynı veriyi Python tarafında JSON/CSV’ye dönüştürüp deneme sistemine bağlamak için hazırlandı.

### Klasörler

- **`Worde_Yapistir/`**: Yıl bazında Word’e yapıştırılacak soru metinleri (`2013.txt` … `2023.txt`).
  - Başlangıç şablonu: `Worde_Yapistir/TEMPLATE.txt`
- **`Gorseller/`**: Yıl bazında soru görselleri (`Gorseller/2013/` … `Gorseller/2023/`).
  - Önerilen dosya adı: `2021_Soru_01.png`, `2021_Soru_02.png`, ...
- **`Cevap_Anahtari/`**: Yıl bazında cevap anahtarı metinleri (`2013.txt` … `2023.txt`).
- **`Python_Verisi/`**: Dönüşüm çıktı klasörü.
  - `Python_Verisi/json/`
  - `Python_Verisi/csv/`

### Word’e yapıştırılacak metin formatı (önerilen)

Metni aşağıdaki sırayla tut:

```
DERS: DKAB
KONU:
YIL: 2021

Soru 1:
[Tam soru metni]

A) ...
B) ...
C) ...
D) ...
E) ...

Doğru Cevap: A

Açıklama:
[Bu şıkkın neden doğru olduğu]

Not:
[Varsa görsel bilgisi]
```

### Resimli/görselli sorular

Resimli sorularda metnin içine ayrıca şu bloğu ekle (Word’de bu bloğun altına görseli yapıştır):

```
Görsel Notu:
Bu soru resim/görsel içeriyor.
Görsel dosya adı: 2021_Soru_04.png
Görsel konumu: C:\Users\osman\Desktop\OSYM\Gorseller\2021\2021_Soru_04.png
Word’de bu satırın altına görseli yapıştır.
```

### Pratik çalışma sırası (önerilen)

- **2013–2020**: Metin çıkarımı daha iyi → önce `Worde_Yapistir/YYYY.txt` dosyalarını doldur.
- **2021–2023**: Görsel ağırlıklı → `Gorseller/YYYY/` içine görselleri koy, metne “Görsel Notu” bloğunu ekle.
- Son aşamada aynı veriyi `Python_Verisi/json` ve `Python_Verisi/csv` altına dönüştür.

