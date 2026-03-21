## OSYM klasor yapisi

Bu klasor yapisi, sorulari once Word'e duzenli yapistirmak, sonra ayni veriyi Python tarafinda JSON/CSV'ye donusturup deneme sistemine baglamak icin hazirlandi.

### Mevcut durum

- `DKAB` soru metinleri veri havuzunda `2013-2025` araliginda bulunuyor.
- `IHL` soru metinleri veri havuzunda `2019-2023` araliginda bulunuyor.
- `DHBT` soru metinleri veri havuzunda `2014`, `2016` ve `2018` yillari icin `Lisans`, `Onlisans` ve `Ortaogretim` olarak bulunuyor.
- `2018 DHBT` sinavlari veri havuzuna eklendi ve konu etiketleri standart listeye gore duzenlendi.

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

### Konu giris kurallari

Soru ekleyecek herkes asagidaki kurallara uymali:

- Her soru blogunda yalnizca **bir adet** `KONU:` satiri bulunur.
- `Soru x:` satirindan sonra ikinci bir `KONU:` satiri eklenmez.
- `KONU:` satirinda yalnizca standart konu listesinde yer alan basliklardan biri kullanilir.
- Alt basliklar `KONU:` olarak yazilmaz.
- Daha spesifik konu bilgisi gerekiyorsa soru metninde veya aciklamada tutulur.
- `Akaid / Kelam` yerine daima `Kelam / Akaid` kullanilir.
- `Islam Tarihi / Siyer` gibi birlesik baslik kullanilmaz; soru icerigine gore `Islam Tarihi` veya `Siyer` secilir.
- `Din Sosyolojisi ve Psikolojisi` gibi birlesik baslik kullanilmaz; baskin alan hangisiyse o secilir.
- `Kur'an-i Kerim ve Tecvid`, `Islam Tarihi`, `Islam Ahlaki ve Tasavvuf` gibi varyasyonlar yerine standart yazim kullanilir.

### Standart konu listesi

Yeni eklenecek sorularda sadece su konu basliklari kullanilabilir:

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

### Konu dagilim rehberi

Bu dagilimlar mutlak kural degildir; son karar her zaman soru icerigine gore verilir. Ancak soru numarasi ile konu arasinda ciddi uyumsuzluk varsa once bu dagilim rehberi dikkate alinmalidir.

#### OABT DKAB / IHL (guncel 75 soru yapisi)

| Sinav | Soru araligi | Genelde gelen alanlar |
| --- | ---: | --- |
| OABT DKAB / IHL | 1-10 | Kur'an-ı Kerim ve Tecvid, Tefsir baslangici |
| OABT DKAB / IHL | 11-20 | Hadis, Fıkıh, kismen Fıkıh Usulü |
| OABT DKAB / IHL | 21-30 | Kelam / Akaid, Mezhepler, Islam dusuncesi |
| OABT DKAB / IHL | 31-40 | Siyer, Islam Tarihi, Islam Kultur ve Medeniyeti, Tasavvuf / Ahlak |
| OABT DKAB / IHL | 41-50 | Din Felsefesi, Din Sosyolojisi, Din Psikolojisi, Din Egitimi, Dinler Tarihi |
| OABT DKAB / IHL | 51-75 | Ozellikle Din Egitimi ve diger din bilimleri agirlikli ogretim / olcme / gelisim / alan uygulamalari |

#### DHBT

| Sinav | Soru araligi | Genelde gelen alanlar |
| --- | ---: | --- |
| DHBT-1 | 1-20 | Temel din bilgisi: inanc, ibadet, Kur'an bilgisi, siyer, ahlak |
| DHBT-2 | 21-40 | Duzeye gore alan bilgisi: hadis, fıkıh, tefsir, kelam / akaid, siyer, din hizmetleri / hitabet vb. |

#### Eski KPSS-OABT hazirlik mantigi icin yaklasik okuma

| Sinav | Soru araligi | Genelde gelen alanlar |
| --- | ---: | --- |
| Eski KPSS-OABT | 1-15 | Kur'an, Tecvid, Tefsir |
| Eski KPSS-OABT | 16-30 | Hadis, Fıkıh |
| Eski KPSS-OABT | 31-45 | Kelam, Mezhepler, Islam Tarihi, Siyer |
| Eski KPSS-OABT | 46-60 | Tasavvuf, Ahlak, Kultur, Medeniyet |
| Eski KPSS-OABT | 61-75 | Din bilimleri: din egitimi, din psikolojisi, din sosyolojisi, din felsefesi, dinler tarihi |

### Etiketleme notlari

- `Soru 75` gibi gec bir soruya `Hadis`, `Kelam / Akaid`, `Tefsir`, `Fıkıh` veya `Kur'an-ı Kerim ve Tecvid` etiketi verilecekse once mutlaka icerik tekrar kontrol edilmelidir.
- `Din Egitimi` blogunda gecen bir soruda `Hadis` veya `Tefsir` kavramlari bulunsa bile soru ogretim, program, olcme, gelisim veya yontem odakliysa `Din Eğitimi` secilmelidir.
- `İslam Kültür ve Medeniyeti` icine sanat, mimari, hilye, naat, tezhip, hat, minyatur, cami mimarisi gibi kultur-medeniyet sorulari girer.
- `İslam Mezhepleri ve Akımları` ile `Mezhepler Tarihi` ayriminda, soru dogrudan mezhep / firka / akim tanitimi ise uygun baslik secilir; tarihsel-siyasi seyir odakliysa icerik tekrar kontrol edilir.
- `Din Hizmetleri ve Hitabet` icine vaaz, hutbe, hitabet, iletisim, irsad ve din hizmeti uygulamalari girer.

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

Veri eklerken ve duzenlerken pratikte en saglikli sira su sekildedir:

1. Once ilgili sinavin metnini `Worde_Yapistir/` altinda tamamla veya temizle.
2. Her soru icin `KONU:` etiketini standart konu listesine gore kontrol et.
3. Konu kararsizsa once soru icerigine bak, sonra soru numarasini konu dagilim rehberiyle karsilastir.
4. Gorselli sorularda `Gorseller/` klasorunu ve `Gorsel Notu` blogunu birlikte duzenle.
5. Bir sinav tamamlandiginda parser ve analiz tarafinda konu listesinin dogru gorundugunu kontrol et.
6. En son asamada ayni veriyi `Python_Verisi/json/` ve `Python_Verisi/csv/` altina donustur.

Bugunku veri durumuna gore oncelik sirasini boyle takip etmek daha verimlidir:

- Mevcut DKAB ve IHL metinlerinde kalan yanlis konu etiketlerini temizle.
- DHBT havuzunda yeni eklenecek yillari ve eksik duzeyleri ayni standartla tamamla.
- Veri girisi oturduktan sonra parser, analiz ve arayuz tarafinda filtre kontrollerini sikilastir.

### Ileride yapilabilecekler

- Mevcut DKAB, IHL ve DHBT dosyalarini ikinci kez tarayip konu dagilim rehberine gore toplu kalite kontrol yapmak.
- `analiz_araci.py` icine gecersiz veya supheli `KONU:` etiketlerini raporlayan otomatik kontrol eklemek.
- `dkab_quiz_modern.py` icinde gecersiz konu gorulurse arayuzde daha acik uyari vermek.
- Yeni DHBT yillarini ve eksik duzey / oturumlari veri havuzuna eklemek.
- MBSTS sinavlarini ayni metin formati ve konu mantigiyla projeye dahil etmek.
- Veri yapisi yeterince oturdugunda uygulamayi Windows icin `.exe` olarak paketlemek.
- Ihtiyac devam ederse kurulum sihirbazi ve hafif lisanslama katmanini sonraki asamaya birakmak.

### Hatirlatma notu

- Veri kapsamini genisletirken yeni DHBT yillari ile MBSTS sinavlarini eklemeyi unutma.
- Yeni soru eklerken once bu README'deki standart konu listesi ve dagilim rehberine gore etiketleme yap.

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
- Aktivasyon ve lisans denemelerini loglayip supheli kullanimlari izlemek.
- Ayni lisansin birden fazla cihazda eszamanli kullanimini sinirlamak.
- Guncelleme mekanizmasi ekleyip lisans ve guvenlik kontrollerini zamanla guclendirmek.

En mantikli siralama genelde sudur: once stabil `.exe`, sonra hafif online lisanslama, sonra gerekirse ek koruma katmanlari.
