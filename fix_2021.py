import re

raw_text = r"""
DERS: DKAB
KONU: Tecvit
YIL: 2021
SORU NO: 1

Soru:
Tecvit kaideleri ve bunların gerçekleştiği harf gruplarıyla ilgili:
I. İdgam-ı bila gunne: lam ve ra
II. İdgam-ı mütecaniseyn: kaf ve kef
III. İdgam-ı mütekaribeyn: be ve mim
eşleştirmelerinden hangileri doğrudur?

A) Yalnız I
B) Yalnız II
C) Yalnız III
D) I ve II
E) I, II ve III

Doğru Cevap: A

Açıklama:
İdgam-ı bila gunne lam ve ra harflerinde olur. Diğer eşleştirmeler bu şekliyle doğru verilmemiştir. [DKAB 2021, page 2](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=2)

---

DERS: DKAB
KONU: Tecvit / Vakıf
YIL: 2021
SORU NO: 2

Soru:
Kur’an-ı Kerim’de peş peşe gelip birinde durulduğunda diğerinde geçilmesi gereken vakıf çeşidi aşağıdakilerden hangisidir?

A) Vakf-ı mutlak
B) Vakf-ı mücevvez
C) Vakf-ı muanaka
D) Vakf-ı caiz
E) Vakf-ı lazım

Doğru Cevap: C

Açıklama:
Vakf-ı muanaka, iki durak noktasından birinde durulup diğerinde geçilmesi gereken özel vakıf türüdür. [DKAB 2021, page 2](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=2)

---

DERS: DKAB
KONU: Tecvit
YIL: 2021
SORU NO: 3

Soru:
Kur’an-ı Kerim’i okurken bazı kelimelerin altında küçük harflerle çeşitli kelimelerin veya harflerin yer aldığı görülür. Buna göre aşağıdaki açıklamalardan hangisi yanlıştır?

A) Kelimedeki ya harfinin altına yazılan harf inceltme içindir.
B) Kelimedeki [OCR belirsiz] harfinin altına yazılan işaret uzatmak içindir.
C) Altında “sekte” lafzı bulunan kelime okunurken nefes bir süre tutulup ses kesilir.
D) Altında “işmam” kelimesi bulunan harfte cezimden sonra harfin aslında olan ötre sessiz olarak dudaklarla gösterilir.
E) Kelimedeki [OCR belirsiz] harfinin altına yazılan “kasr” kısa okuma içindir.

Doğru Cevap: C

Açıklama:
Bu soruda verilen ifadelerden yanlış olan seçenek C olarak işaretlenmiştir. OCR düşük olduğu için soru metninde küçük bozulmalar olabilir. [DKAB 2021, page 3](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=3)

---

DERS: DKAB
KONU: Tecvit / Medler
YIL: 2021
SORU NO: 4

Soru:
Verilen ayetlerde aşağıdaki medlerden hangisi bulunmamaktadır?

A) Lazım
B) [OCR belirsiz]
C) Munfasıl
D) Muttasıl
E) Tabii

Doğru Cevap: D

Açıklama:
Soruda verilen örneklerde bulunmayan med türü muttasıl olarak işaretlenmiştir. [DKAB 2021, page 3](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=3)

---

DERS: DKAB
KONU: Kur’an İlimleri
YIL: 2021
SORU NO: 5

Soru:
“...Kendisine ayetlerimizi verdiğimiz hâlde onlardan sıyrılıp da şeytanın kendisini peşine taktığı...” ayetinde kimin kastedildiği belli değildir. Bu hususu inceleyen Kur’an ilmi aşağıdakilerden hangisidir?

A) Mübhematü’l-Kur’an
B) Vücuh ve nezair
C) Garibü’l-Kur’an
D) Mecazü’l-Kur’an
E) Münasebatü’l-Kur’an

Doğru Cevap: A

Açıklama:
Kur’an’da açıkça adı verilmeyen kişi, yer ve topluluklarla ilgilenen alan Mübhematü’l-Kur’an’dır. [DKAB 2021, page 4](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=4)

---

DERS: DKAB
KONU: Tefsir
YIL: 2021
SORU NO: 6

Soru:
“Ey Resul! Rabbinden sana indirileni tebliğ et...” ayetinin Hz. Ali’nin imametine delil olduğunu savunan bir eser, aşağıdaki tefsir türlerinden hangisi kapsamında değerlendirilir?

A) İlmi
B) Fıkhi
C) Mezhebi
D) İçtimai
E) Lugavi

Doğru Cevap: C

Açıklama:
Bir mezhebin görüşünü temellendirmek amacıyla yapılan yorum mezhebi tefsir kapsamına girer. [DKAB 2021, page 4](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=4)

---

DERS: DKAB
KONU: Tefsir Yaklaşımları
YIL: 2021
SORU NO: 7

Soru:
Kur’an’ı kendi bütünlüğü içinde, nazil olduğu ortamı ve ilk muhatapların bilgi ve görüşlerini merkeze alarak tefsir etmeyi savunan kişinin benimsediği tefsir türü hangisidir?

A) Dirayet
B) İçtimai
C) İşari
D) Rivayet
E) İlmi

Doğru Cevap: D

Açıklama:
İlk muhataplar, nüzul ortamı ve nakil merkezli yaklaşım rivayet tefsiri ile ilişkilidir. [DKAB 2021, page 5](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=5)

---

DERS: DKAB
KONU: Kur’an İlimleri
YIL: 2021
SORU NO: 8

Soru:
Kur’an’da açıkça zikredilmeyen şahıs ve yerleri nitelemek için kullanılan unsurlar arasında aşağıdakilerden hangisi yer almaz?

A) [OCR belirsiz]
B) İsm-i mevsuller
C) İsm-i işaretler
D) Künye ve lakaplar
E) Heca harfleri

Doğru Cevap: E

Açıklama:
Heca harfleri bu amaçla kullanılmaz; diğerleri dolaylı anlatım unsurları arasında yer alabilir. [DKAB 2021, page 5](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=5)

---

DERS: DKAB
KONU: Tefsir Usulü
YIL: 2021
SORU NO: 9

Soru:
Aşağıdakilerden hangisi tefsirde sahabeye verilen önemin sebepleri arasında yer almaz?

A) Hz. Muhammed’e soru sorup öğrenme imkânına sahip olmaları
B) Kendilerine nazil olduğu için Kur’an’ın inceliklerini iyi anlamaları
C) Ayetlerin nüzul sebeplerine vakıf olmaları
D) Kur’an’ı anlama ve yorumlama konusunda ittifak etmeleri
E) Arap örf, âdet ve kültürünü iyi bilmeleri

Doğru Cevap: D

Açıklama:
Sahabe bütün yorumlarda ittifak etmiş değildir. Bu nedenle D seçeneği doğru cevap olur. [DKAB 2021, page 6](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=6)

---

DERS: DKAB
KONU: Hadis
YIL: 2021
SORU NO: 10

Soru:
Bir bedevinin, elçiden duyduğu bilgilerle yetinmeyip bizzat Hz. Muhammed’e gelerek doğrulama yapması hadis ilminde aşağıdakilerden hangisine örnek teşkil eder?

A) Âli isnadın önemine
B) Şifahi rivayetin değerine
C) Rivayetin tarikini artırma çabasına
D) Senedin muttasıl olmasının zorunluluğuna
E) Ravilerin sika olması gerektiğine

Doğru Cevap: A

Açıklama:
Bilginin doğrudan ve daha kısa yolla asıl kaynaktan alınması âli isnadın önemine örnektir. [DKAB 2021, page 6](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=6)

---

DERS: DKAB
KONU: Hadis Usulü
YIL: 2021
SORU NO: 11

Soru:
Buhari’nin Sahih’inde, senedinde sahabe dışındaki bütün ravileri hazfedilmiş hadis aşağıdaki türlerden hangisine girer?

A) Muallel
B) Müdrec
C) Maklub
D) Muallak
E) Maktu

Doğru Cevap: D

Açıklama:
Senedin başından ravi düşürülerek verilen rivayet muallak hadis olarak adlandırılır. [DKAB 2021, page 7](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=7)

---

DERS: DKAB
KONU: Hadis Usulü
YIL: 2021
SORU NO: 12

Soru:
Bir rivayet sika ravilerden oluşan birçok farklı senedle, diğeri ise tek senedle nakledilmiştir. Buna göre bu iki rivayet aşağıdakilerden hangisinde doğru sıralanmıştır?

A) Maruf – münker
B) Mahfuz – şaz
C) Mutabi – şahid
D) Nasih – mensuh
E) Ahad – mütevatir

Doğru Cevap: B

Açıklama:
Çok daha güçlü ve çok yollu rivayet mahfuz, buna aykırı kalan tekil rivayet ise şaz olarak değerlendirilir. [DKAB 2021, page 7](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=7)

---

DERS: DKAB
KONU: Hadis
YIL: 2021
SORU NO: 13

Soru:
Bu sorunun metni ve şıkları OCR nedeniyle net okunamadı.

A) [OCR ile okunamadı]
B) [OCR ile okunamadı]
C) [OCR ile okunamadı]
D) [OCR ile okunamadı]
E) [OCR ile okunamadı]

Doğru Cevap: [OCR ile net tespit edilemedi]

Açıklama:
Bu soru için PDF görüntüsünden manuel bakmak gerekecek. [DKAB 2021, page 7](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=7), [page 8](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=8)

---

DERS: DKAB
KONU: Hadis Tarihi
YIL: 2021
SORU NO: 14

Soru:
Aşağıdakilerden hangisi müksirun sahabilerin çok hadis rivayet etmelerinde etkili olan sebeplerden biri değildir?

A) Hz. Muhammed’le geçirdikleri zaman dilimi
B) İlim ortamına sahip şehirlerde yaşamaları
C) Dinin öğrenilmesi ve öğretilmesine yoğunlaşmaları
D) Güçlü bir hafızaya sahip olmaları
E) Duydukları hadisleri yazıyla kaydetmeleri

Doğru Cevap: E

Açıklama:
Müksirun sahabilerin çok hadis rivayet etmesinde yazıyla kayıt temel belirleyici unsur değildir. [DKAB 2021, page 8](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=8)

---

DERS: DKAB
KONU: İslam Hukuku
YIL: 2021
SORU NO: 15

Soru:
İslam hukukunda kamu menfaatine göre yeni hükümler konulabilmesi aşağıdaki delillerden hangisiyle ilgilidir?

A) İstihsan
B) İstishab
C) İstislah
D) İcma
E) Örf

Doğru Cevap: C

Açıklama:
Maslahat esaslı hüküm üretme yöntemi istislah olarak adlandırılır. [DKAB 2021, page 8](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=8)

---

DERS: DKAB
KONU: İslam Hukuku
YIL: 2021
SORU NO: 16

Soru:
Kurban organizasyonu yapan kuruluşun sözleşmesinde kurban bedeli, organizasyon masrafı ve artacak paranın yardım olarak alınması birlikte yer almaktadır. Bu sözleşme hangi akit ikilisini içerir?

A) Vekâlet – hibe
B) Vekâlet – kefalet
C) Kefalet – murabaha
D) Vekâlet – murabaha
E) Murabaha – [OCR belirsiz]

Doğru Cevap: A

Açıklama:
Organizasyon için vekâlet, artan kısmın bağış olarak bırakılması ise hibe kapsamında değerlendirilir. [DKAB 2021, page 9](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=9)

---

DERS: DKAB
KONU: Fıkıh Usulü
YIL: 2021
SORU NO: 17

Soru:
Sedd-i zerai ile ilgili olarak:
I. İslam hukukunun asli delilleri arasında kabul edilir.
II. Haram fiillere götüren davranışların yasaklanması şeklinde tanımlanır.
III. Fakihler arasında geçerliliği ve uygulanacağı durumlar konusunda ittifak vardır.
hangileri doğrudur?

A) Yalnız I
B) Yalnız II
C) I ve II
D) II ve III
E) I, II ve III

Doğru Cevap: B

Açıklama:
Sedd-i zerai, harama götüren yolların kapatılması anlayışıdır. Asli delil değildir ve uygulanması konusunda tam ittifak yoktur. [DKAB 2021, page 9](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=9)

---

DERS: DKAB
KONU: Fıkıh
YIL: 2021
SORU NO: 18

Soru:
Yolculukta orucun ertelenebilmesi ve zaruret hâlinde haram bir şeyin yenebilmesi aşağıdaki kavram ikililerinden hangisi kapsamında değerlendirilir?

A) Rükün – mani
B) Mutlak – mukayyed
C) Sahih – fasid
D) Hacet – zaruret
E) Azimet – ruhsat

Doğru Cevap: E

Açıklama:
Normal hüküm azimet, kolaylaştırıcı geçici hüküm ise ruhsattır. Sorudaki iki örnek ruhsat kapsamındadır. [DKAB 2021, page 10](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=10)

---

DERS: DKAB
KONU: Oruç / Namaz
YIL: 2021
SORU NO: 19

Soru:
Mahmut, televizyondan duyduğu başka şehir ezanıyla iftar edip namaza başlamıştır. Kendi bulunduğu yerde vakit henüz girmemiştir. İmamın vermesi gereken cevap aşağıdakilerden hangisidir?

A) Her ikisi de geçersizdir; oruç kaza edilmeli, namaz ise tekrar kılınmalıdır.
B) Her ikisi de geçersizdir; kefaret orucu tutulmalı, namaz ise tekrar kılınmalıdır.
C) [OCR belirsiz]
D) [OCR belirsiz]
E) Hata ile yenildiği için oruç geçerlidir; namaz bitmeden vakit girdiği için namaz da geçerlidir.

Doğru Cevap: A

Açıklama:
Bulunduğu yerin vakti esas olduğundan oruç da namaz da geçerli sayılmaz. [DKAB 2021, page 10](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=10)

---

DERS: DKAB
KONU: Oruç
YIL: 2021
SORU NO: 20

Soru:
Hz. Muhammed’in Medine’ye geldiğinde Yahudilerin tuttuğunu gördüğü, ramazan orucu farz kılınınca yükümlülük olmaktan çıkan oruç aşağıdakilerden hangisidir?

A) Şevval
B) Davud
C) Aşura
D) Zilhicce
E) Şaban

Doğru Cevap: C

Açıklama:
Bahsedilen oruç Aşura orucudur. Ramazan farz kılınınca zorunlu olmaktan çıkmıştır. [DKAB 2021, page 11](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=11)

---

DERS: DKAB
KONU: Hac
YIL: 2021
SORU NO: 21

Soru:
İlk olarak Mekke’ye gidip umre yapacak, ardından vakit kaybetmeden Arafat’a çıkacak hacı adayları aşağıdaki hac türlerinden hangilerine niyet etmelidir?
I. İfrad
II. Kıran
III. Temettü

A) Yalnız I
B) Yalnız II
C) Yalnız III
D) I ve II
E) II ve III

Doğru Cevap: B

Açıklama:
Umre ve haccı ihramdan çıkmadan birlikte sürdürme durumu kıran haccına işaret eder. [DKAB 2021, page 11](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=11)

---

DERS: DKAB
KONU: Kelam
YIL: 2021
SORU NO: 22

Soru:
Fiilleri kesb edenin insan, yaratanın Allah olduğunu; cüz’i irade ile insanın sorumluluğunu savunan düşünürlerin mensup olduğu itikadi mezhep hangisidir?

A) Cebriyye
B) Maturidiyye
C) Eşariyye
D) [OCR belirsiz]
E) Selefiyye

Doğru Cevap: D

Açıklama:
Bu soruda OCR ile bir şık adı bozulmuş durumda; ancak cevap anahtarına göre doğru seçenek D’dir. [DKAB 2021, page 12](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=12)

---

DERS: DKAB
KONU: Kelam
YIL: 2021
SORU NO: 23

Soru:
Gazali’ye göre Allah’ın fiili aşağıdakilerden hangisi olarak tanımlanır?

A) O’nun iradesi ve kudreti sonucu ortaya çıkan şeydir.
B) O’nun kudretinin neticesinde zorunlu olarak sadır olan şeydir.
C) O’nun bilgisine konu olan şeydir.
D) Varlığı O’nun varlığından ayrı düşünülemeyecek şeydir.
E) O’nun iradesinin bilgiye dönüştüğü şeydir.

Doğru Cevap: A

Açıklama:
Gazali’nin yaklaşımında fiil, Allah’ın irade ve kudreti ile ilişkilendirilir. [DKAB 2021, page 12](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=12)

---

DERS: DKAB
KONU: Sıfatlar
YIL: 2021
SORU NO: 24

Soru:
Allah’ın eli, yüzü, gözü gibi ifadeler aşağıdaki ilahi sıfat türlerinden hangisi içinde değerlendirilir?

A) Nefsi
B) Haberi
C) Sübuti
D) Fiili
E) [OCR belirsiz]

Doğru Cevap: B

Açıklama:
Bu tür nitelendirmeler haberî sıfatlar başlığı altında ele alınır. [DKAB 2021, page 13](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=13)

---

DERS: DKAB
KONU: Mutezile
YIL: 2021
SORU NO: 25

Soru:
İnsanın hür olduğu ve kendi fiilinin yaratıcısı sayıldığı anlayış, Mutezile’nin beş esasından hangisi kapsamındadır?

A) Emir bi’l-maruf nehiy ani’l-münker
B) Va’d ve vaid
C) Tevhid
D) el-Menzile beyne’l-menzileteyn
E) Adl

Doğru Cevap: E

Açıklama:
İnsanın fiillerinden sorumlu oluşu ve özgür iradesi Mutezile’de adl ilkesiyle ilişkilidir. [DKAB 2021, page 13](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=13)

---

DERS: DKAB
KONU: Allah’ın Varlığının Delilleri
YIL: 2021
SORU NO: 26

Soru:
Âlemdeki her şeyin insana uygun ve onun yararına düzenlenmiş olduğunu esas alan isbat-ı vacip delili hangisidir?

A) Fıtrat
B) Hudus
C) [OCR belirsiz]
D) İnayet
E) Temanu

Doğru Cevap: D

Açıklama:
Evrendeki düzen ve uyumluluğun insan yararına oluşu inayet deliliyle açıklanır. [DKAB 2021, page 14](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=14)

---

DERS: DKAB
KONU: Allah’ın Sıfatları
YIL: 2021
SORU NO: 27

Soru:
“Allah, hiçbir mekâna, sebebe, mucit ve müessire ihtiyaç duymaz...” ifadesi aşağıdaki sıfatlardan hangisine vurgu yapar?

A) İlim
B) Kudret
C) İrade
D) Kıyam binefsihi
E) Hayat

Doğru Cevap: D

Açıklama:
Kendi zatı ile kaim olup hiçbir şeye ihtiyaç duymama, kıyam binefsihi sıfatıdır. [DKAB 2021, page 14](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=14)

---

DERS: DKAB
KONU: Mezhepler Tarihi
YIL: 2021
SORU NO: 28

Soru:
Hz. Ali’yi hakem olayından dolayı küfürle suçlayıp onu haklı görenleri de suçlu sayan grup aşağıdaki ekollerden hangisine mensuptur?

A) Mutezile
B) Sebeiyye
C) Rafiziler
D) Mürcie
E) Hariciler

Doğru Cevap: E

Açıklama:
Bu yaklaşım Haricilerin tipik tavrıdır. [DKAB 2021, page 15](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=15)

---

DERS: DKAB
KONU: Mezhepler Tarihi
YIL: 2021
SORU NO: 29

Soru:
Haritada nüfus yoğunluğu verilen mezhep aşağıdakilerden hangisidir?

A) Zeydilik
B) İsmaililik
C) Eşarilik
D) İmamilik
E) [OCR belirsiz]

Doğru Cevap: D

Açıklama:
Haritadaki dağılım İmamilik mezhebine işaret etmektedir. [DKAB 2021, page 15](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=15)

Görsel Notu:
Bu soru resimlidir / haritalıdır.
Görsel dosyası: 2021_Soru_29_Gorsel_01.png
Konum: C:\Users\osman\Desktop\OSYM\Gorseller\2021\2021_Soru_29_Gorsel_01.png

---

DERS: DKAB
KONU: Mezhepler Tarihi
YIL: 2021
SORU NO: 30

Soru:
Lübnan’daki, hulul/tecelli anlayışını savunan ve Hakim bi-Emrillah’a özel anlam yükleyen grubun mensup olduğu mezhep hangisidir?

A) Yezidilik
B) Nusayrilik
C) Dürzilik
D) İsmaililik
E) Zeydilik

Doğru Cevap: C

Açıklama:
Soruda verilen özellikler Dürzilik mezhebiyle ilgilidir. [DKAB 2021, page 16](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=16)

---

DERS: DKAB
KONU: Tasavvuf / Bilgi Yolları
YIL: 2021
SORU NO: 31

Soru:
Nefsi arındırma ve ilham yoluyla hakikate ulaşmayı savunan kişi aşağıdaki yollardan hangisini benimsemektedir?

A) Fıtrat
B) İstidlal
C) İlham ve keşif
D) Talim ve beyan
E) Nakil

Doğru Cevap: C

Açıklama:
İlham ve keşif, daha çok tasavvufi bilgi anlayışında öne çıkar. [DKAB 2021, page 16](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=16)

---

DERS: DKAB
KONU: Siyer
YIL: 2021
SORU NO: 32

Soru:
Hendek Savaşı sırasında Medine Vesikası’na aykırı hareket ederek Müslümanlarla antlaşmasını bozan kabile hangisidir?

A) Kurayza
B) Kaynuka
C) Gatafan
D) Nadir
E) Hevazin

Doğru Cevap: A

Açıklama:
Hendek Savaşı sırasında antlaşmayı bozan Yahudi kabilesi Beni Kurayza’dır. [DKAB 2021, page 17](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=17)

---

DERS: DKAB
KONU: Siyer
YIL: 2021
SORU NO: 33

Soru:
Ebu Ubeyde b. Cerrah komutasındaki birliğin “habat” yiyip sahile vurmuş balıkla açlığını giderdiği seriyye hangisidir?

A) Sifülbahr
B) Rabiğ
C) Batn-ı Nahle
D) Zatüsselasil
E) [OCR belirsiz]

Doğru Cevap: A

Açıklama:
Bu olay Sifülbahr Seriyyesi ile ilişkilidir. [DKAB 2021, page 17](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=17)

---

DERS: DKAB
KONU: Siyer / İslam Tarihi
YIL: 2021
SORU NO: 34

Soru:
Hz. Muhammed’in hastalığı sırasında “Bana divit ve kâğıt getirin...” demesiyle başlayan olay İslam tarihinde nasıl isimlendirilir?

A) Kırtas Hadisesi
B) Cemel Vakası
C) Ridde Olayı
D) Garanik Hadisesi
E) Gadir-i Hum Olayı

Doğru Cevap: A

Açıklama:
Bu olay kaynaklarda Kırtas Hadisesi olarak bilinir. [DKAB 2021, page 18](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=18)

---

DERS: DKAB
KONU: Siyer
YIL: 2021
SORU NO: 35

Soru:
Hubab b. Münzir’in su kuyularına yakın yerde konaklanmasını önerdiği olay hangi gazvede yaşanmıştır?

A) Beni Mustalik
B) Gabe
C) Huneyn
D) Bedir
E) Beni Lihyan

Doğru Cevap: D

Açıklama:
Hubab b. Münzir’in savaş taktiğiyle ilgili bu önerisi Bedir Gazvesi’nde olmuştur. [DKAB 2021, page 18](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=18)

---

DERS: DKAB
KONU: İslam Tarihi
YIL: 2021
SORU NO: 36

Soru:
Hz. Osman’ın valilerle yaptığı toplantıda sunulan öneriler arasında hangisi yer almaz?

A) Muhaliflerin cihatla meşgul edilmesi
B) Şikâyetçi grupların elebaşlarının öldürülmesi
C) Muhaliflerin ülke dışına gönderilmesi
D) İşin valilere bırakılması
E) Eleştirenlerin bir kısmının mali destekle gönüllerinin alınması

Doğru Cevap: C

Açıklama:
Verilen seçenekler içinde toplantıda yer almayan öneri C seçeneğidir. [DKAB 2021, page 19](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=19)

---

DERS: DKAB
KONU: İslam Tarihi
YIL: 2021
SORU NO: 37

Soru:
Sevad arazilerinin fethi sürecinde gerçekleşen savaşlardan hangisi bu süreçte yer almaz?

A) Kadisiye
B) Köprü
C) Yermük
D) Celula
E) Nihavend

Doğru Cevap: C

Açıklama:
Yermük daha çok Suriye cephesiyle ilişkilidir; Sevad bölgesi fetih sürecinin savaşları arasında sayılmaz. [DKAB 2021, page 19](https://myaidrive.com/DEqXHCfiNRhsAbqu4n4TQs/DKAB-2021_oc.pdf?pdfPage=19)
"""

# Reformat
formatted_blocks = []
blocks = raw_text.split('---')

for block in blocks:
    lines = [line.strip() for line in block.strip().split('\n')]
    if len(lines) < 5:
        continue
        
    out_lines = []
    soru_no = ""
    for line in lines:
        if line.startswith('SORU NO:'):
            soru_no = line.split(':')[1].strip()
        elif line == 'Soru:':
            if soru_no:
                out_lines.append(f"Soru {soru_no}:")
            else:
                out_lines.append("Soru:")
        else:
            out_lines.append(line)
            
    # filter out blanks
    final_lines = []
    for line in out_lines:
        if line.startswith('SORU NO:'): continue
        if not line:
            final_lines.append('')
        else:
            final_lines.append(line)
        
    formatted_blocks.append('\n'.join(final_lines).strip())

with open(r'c:\Users\osman\Desktop\OSYM\Worde_Yapistir\2021_DKAB_Sorulari.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n---SONRAKİ SORU---\n\n'.join(formatted_blocks))

print("Islem bitti, 2021 sorulari eklendi.")
