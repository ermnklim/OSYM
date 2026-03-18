# Test with the exact working logic from debug
with open('Worde_Yapistir/2020_DKAB_Sorulari.txt', 'r', encoding='utf-8') as file:
    content = file.read()

soru_blocks = content.split('---SONRAKİ SORU---')

for i, block in enumerate(soru_blocks):
    if 'Soru 3:' in block:
        print("=== WORKING PARSING LOGIC ===")
        lines = block.strip().split('\n')
        
        soru_no = None
        soru_metni = []
        options = {}
        dogru_cevap = None
        aciklama = ""
        gorsel_var = False
        gorsel_dosyalari = []
        
        # Parse using the working logic
        for i, line in enumerate(lines):
            if line.startswith('Soru ') and ':' in line:
                soru_no = int(line.split()[1].replace(':', ''))
            elif line.startswith('A)'):
                options['A'] = line[2:].strip()
            elif line.startswith('B)'):
                options['B'] = line[2:].strip()
            elif line.startswith('C)'):
                options['C'] = line[2:].strip()
            elif line.startswith('D)'):
                options['D'] = line[2:].strip()
            elif line.startswith('E)'):
                options['E'] = line[2:].strip()
            elif line.startswith('Doğru Cevap:'):
                dogru_cevap = line.split(':')[1].strip()
            elif line.startswith('Açıklama:'):
                aciklama = line.split('Açıklama:')[1].strip()
            elif 'Görsel Notu:' in line or 'Görsel dosyası:' in line or 'Dosya:' in line:
                gorsel_var = True
                if 'Görsel dosyası:' in line:
                    dosya_adi = line.split('Görsel dosyası:')[1].strip()
                    gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\2020\\{dosya_adi}")
                elif 'Dosya:' in line:
                    dosya_adi = line.split('Dosya:')[1].strip()
                    gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\2020\\{dosya_adi}")
        
        print(f"Final result:")
        print(f"  Görsel var: {gorsel_var}")
        print(f"  Görsel dosyaları: {gorsel_dosyalari}")
        break
