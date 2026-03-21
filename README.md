## OSYM klasor yapisi

Bu klasor yapisi, sorulari once Word'e duzenli yapistirmak, sonra ayni veriyi Python tarafinda JSON/CSV'ye donusturup deneme sistemine baglamak icin hazirlandi.

### Klasorler

- **`Worde_Yapistir/`**: Yil bazinda Word'e yapistirilacak soru metinleri.
- Baslangic sablonu: `Worde_Yapistir/TEMPLATE.txt`
- **`Gorseller/`**: Yil bazinda soru gorselleri.
- Onerilen dosya adi: `2021_Soru_01.png`, `2021_Soru_02.png`
- **`Python_Verisi/`**: Donusum cikti klasoru.
- `Python_Verisi/json/`
- `Python_Verisi/csv/`
- **`Tablolar/`**: Sorularla iliskili tablo veya ek gorsel materyaller icin yardimci klasor.

### Word'e yapistirilacak metin formati

Metni asagidaki sirayla tut:

Not: Ayrı bir `Cevap_Anahtari/` klasoru kullanilmayacak. Dogru cevap bilgisi her sorunun hemen altinda `Dogru Cevap:` satiri olarak yer alacak.

```text
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

Dogru Cevap: A

Aciklama:
[Bu sikkin neden dogru oldugu]

Not:
[Varsa gorsel bilgisi]
```

### Resimli veya gorselli sorular

Resimli sorularda metnin icine ayrica su blogu ekle:

```text
Gorsel Notu:
Bu soru resim/gorsel iceriyor.
Gorsel dosya adi: 2021_Soru_04.png
Gorsel konumu: C:\Users\osman\Desktop\OSYM\Gorseller\2021\2021_Soru_04.png
Word'de bu satirin altina gorseli yapistir.
```

### Pratik calisma sirasi

- **2013-2020**: Metin cikarimi daha iyi ise once `Worde_Yapistir/YYYY.txt` dosyalarini doldur.
- **2021-2023**: Gorsel agirlikli ise `Gorseller/YYYY/` icine gorselleri koy, metne `Gorsel Notu` blogunu ekle.
- Son asamada ayni veriyi `Python_Verisi/json` ve `Python_Verisi/csv` altina donustur.

### Ileride yapilabilecekler

- Uygulamayi Windows icin `.exe` olarak paketlemek.
- Istege bagli kurulum sihirbazi eklemek.
- Hafif lisanslama sistemi eklemek.
- Soru verisi yonetimini ve dagitim kontrolunu daha duzenli hale getirmek.
- 2018 ve sonrasi DHBT sinavlarini veri havuzuna eklemek.
- MBSTS sinavlarini da ayni yapida projeye dahil etmek.

### Hatirlatma notu

- Veri kapsamini genisletirken 2018 ve sonrasi DHBT sinavlari ile MBSTS sinavlarini eklemeyi unutma.

### Hafif lisanslama fikri

Ileride uygulanabilecek mantikli yaklasim:

- Uygulama ilk acilista lisans anahtari ister.
- Anahtar, gelistiricinin tuttugu bir API veya veritabani uzerinden dogrulanir.
- Her lisans anahtari tek cihaz aktivasyonu mantigiyla calisabilir.
- Cihaz degisimi gerekiyorsa manuel lisans sifirlama veya panel uzerinden yeniden aktivasyon yapilabilir.
- Amac asiri sert DRM kurmak degil; duzenli lisans yonetimi ve izinsiz kopyalamayi azaltmaktir.

### Guvenlik ve crack riskini azaltma notlari

Tam koruma mumkun degildir; ancak asagidaki onlemler riski azaltabilir:

- Offline yerine online lisans dogrulama kullanmak.
- Lisans anahtarini cihaz kimligiyle eslestirmek.
- Lisans kontrolunu sadece giriste degil, uygulamanin kritik noktalarinda da yapmak.
- Tum lisans mantigini istemcide tutmamak; asil karari sunucu tarafinda vermek.
- API isteklerini token, imza veya zaman damgasi gibi ek korumalarla guclendirmek.
- Kod paketlemede obfuscation kullanmak; tek basina yeterli olmasa da dogrudan kopyalamayi zorlastirir.
- Gizli anahtarlari ve hassas sabitleri uygulama icinde duz metin olarak tutmamak.
- Aktivasyon ve lisans denemelerini loglayip supheli kullanımlari izlemek.
- Ayni lisansin birden fazla cihazda eszamanli kullanimini sinirlamak.
- Guncelleme mekanizmasi ekleyip lisans ve guvenlik kontrollerini zamanla guclendirmek.

En mantikli siralama genelde sudur: once stabil `.exe`, sonra hafif online lisanslama, sonra gerekirse ek koruma katmanlari.
