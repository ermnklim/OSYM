# Test parsing of visual files
import sys
sys.path.append('Python_Verisi')

# Import just the parsing methods
import re

def parse_single_question(text, year):
    """Tek soruyu parse eder"""
    try:
        lines = text.strip().split('\n')
        
        soru_no = None
        soru_metni = []
        options = {}
        dogru_cevap = None
        aciklama = ""
        gorsel_var = False
        gorsel_dosyalari = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('Soru ') and ':' in line:
                soru_no = int(line.split()[1].replace(':', ''))
            elif line and not line.startswith('A)') and not line.startswith('B)') and not line.startswith('C)') and not line.startswith('D)') and not line.startswith('E)') and not line.startswith('Doğru Cevap:') and soru_no and not line.startswith('KONU:') and not line.startswith('YIL:') and not line.startswith('DERS:'):
                soru_metni.append(line)
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
                aciklama_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('---'):
                    current_line = lines[i].strip()
                    if not current_line.startswith('Görsel Notu:') and not current_line.startswith('Görsel dosyası:') and not current_line.startswith('Dosya:') and not current_line.startswith('Tablo'):
                        aciklama_lines.append(lines[i].rstrip())
                    elif current_line.startswith('Görsel Notu:') or current_line.startswith('Görsel dosyası:') or current_line.startswith('Dosya:'):
                        # Handle visual information in the same loop
                        gorsel_var = True
                        if 'Görsel dosyası:' in current_line:
                            dosya_adi = current_line.split('Görsel dosyası:')[1].strip()
                            gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                        elif 'Dosya:' in current_line:
                            dosya_adi = current_line.split('Dosya:')[1].strip()
                            gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                    i += 1
                aciklama = '\n'.join(aciklama_lines).strip()
                i -= 1
            elif 'Görsel Notu:' in line or 'Görsel dosyası:' in line or 'Dosya:' in line:
                gorsel_var = True
                if 'Görsel dosyası:' in line:
                    dosya_adi = line.split('Görsel dosyası:')[1].strip()
                    gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                elif 'Dosya:' in line:
                    dosya_adi = line.split('Dosya:')[1].strip()
                    gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
            
            i += 1
        
        if soru_no and len(options) == 5 and dogru_cevap:
            return {
                'soru_no': soru_no,
                'soru_metni': '\n'.join(soru_metni),
                'options': options,
                'dogru_cevap': dogru_cevap,
                'aciklama': aciklama,
                'gorsel_var': gorsel_var,
                'gorsel_dosyalari': gorsel_dosyalari,
                'year': year
            }
    except Exception as e:
        print(f"Soru parse hatası: {e}")
        return None

# Read and parse 2020 questions
with open('Worde_Yapistir/2020_DKAB_Sorulari.txt', 'r', encoding='utf-8') as file:
    content = file.read()

soru_blocks = content.split('---SONRAKİ SORU---')

for block in soru_blocks:
    if 'Soru ' in block and 'Doğru Cevap:' in block:
        question = parse_single_question(block, 2020)
        if question and question['soru_no'] in [3, 13]:
            print(f'Soru {question["soru_no"]} görsel bilgisi:')
            print(f'  Görsel var: {question.get("gorsel_var", False)}')
            print(f'  Görsel dosyaları: {question.get("gorsel_dosyalari", [])}')
            print('')
