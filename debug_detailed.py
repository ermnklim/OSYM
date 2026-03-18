# Debug parsing of question 3 with detailed logs
with open('Worde_Yapistir/2020_DKAB_Sorulari.txt', 'r', encoding='utf-8') as file:
    content = file.read()

soru_blocks = content.split('---SONRAKİ SORU---')

for i, block in enumerate(soru_blocks):
    if 'Soru 3:' in block:
        print("=== PARSING SORU 3 ===")
        lines = block.strip().split('\n')
        
        soru_no = None
        soru_metni = []
        options = {}
        dogru_cevap = None
        aciklama = ""
        gorsel_var = False
        gorsel_dosyalari = []
        
        for i, line in enumerate(lines):
            print(f"Line {i}: {repr(line)}")
            
            if line.startswith('Soru ') and ':' in line:
                soru_no = int(line.split()[1].replace(':', ''))
                print(f"  -> Found soru_no: {soru_no}")
            elif 'Görsel Notu:' in line or 'Görsel dosyası:' in line or 'Dosya:' in line:
                print(f"  -> FOUND VISUAL LINE!")
                gorsel_var = True
                if 'Görsel dosyası:' in line:
                    dosya_adi = line.split('Görsel dosyası:')[1].strip()
                    gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\2020\\{dosya_adi}")
                    print(f"  -> Added visual file: {dosya_adi}")
                elif 'Dosya:' in line:
                    dosya_adi = line.split('Dosya:')[1].strip()
                    gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\2020\\{dosya_adi}")
                    print(f"  -> Added visual file: {dosya_adi}")
        
        print(f"\nFinal result:")
        print(f"  Görsel var: {gorsel_var}")
        print(f"  Görsel dosyaları: {gorsel_dosyalari}")
        break
