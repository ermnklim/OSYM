$filePath = "c:\Users\osman\Desktop\OSYM\Worde_Yapistir\2016_DKAB_Sorulari.txt"
$content = [System.IO.File]::ReadAllText($filePath, [System.Text.Encoding]::UTF8)

# Adim 1: Soru 49 -> 50, 48 -> 49, ... 21 -> 22 (yukari dogru, cakisma olmasin diye)
for ($i = 49; $i -ge 21; $i--) {
    $content = [System.Text.RegularExpressions.Regex]::Replace(
        $content,
        "(?m)^Soru $i`:",
        "Soru $($i + 1):"
    )
}

# Adim 2: Eski "Soru 50: TEST BITTI" blogunu kaldir
# Bu blok yeniden numaralanmamis, hala dosyanin sonunda duruyor
# "---SONRAKI SORU---" den TEST BITTI'ye kadar olan kismi bul ve sil
$testIdx = $content.IndexOf("TEST B")
if ($testIdx -gt 0) {
    $sepIdx = $content.LastIndexOf("---SONRAKİ SORU---", $testIdx)
    if ($sepIdx -gt 0) {
        $content = $content.Substring(0, $sepIdx).TrimEnd()
    }
}

# Adim 3: Soru 21 icin yer tutucu ekle (PDF'den atlanmis soru)
$placeholder = "Soru 21:`r`n[PDF'deki 21. soru dosyaya aktarilmamistir. Lutfen PDF'den ekleyiniz.]`r`n`r`nA) ...`r`nB) ...`r`nC) ...`r`nD) ...`r`nE) ...`r`n`r`nDoğru Cevap: ?`r`n`r`nAçıklama:`r`n[Eksik - PDF'den eklenecek]"

# Soru 22'den once tek bir "---SONRAKI SORU---" vardir (onceki Soru 20'nin sonu)
# Pattern: "---SONRAKI SORU---" + bosluk + "Soru 22:" -> araya 21'i ekle
$pattern = "(?m)^---SONRAKİ SORU---\r?\n\r?\nSoru 22:"
$replacement = "---SONRAKİ SORU---`r`n`r`n$placeholder`r`n`r`n---SONRAKİ SORU---`r`n`r`nSoru 22:"
$content = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern, $replacement)

[System.IO.File]::WriteAllText($filePath, $content, [System.Text.Encoding]::UTF8)
Write-Host "Numara duzeltme tamamlandi!"
Write-Host "Toplam satir sayisi: $($content.Split("`n").Count)"
