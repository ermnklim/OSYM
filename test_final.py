# Final test to confirm visual parsing works in main application
import sys
sys.path.append('Python_Verisi')
from dkab_quiz_modern import ModernDKABQuiz

# Create a simple test class that doesn't require GUI
class TestQuiz:
    def parse_single_question(self, text, year):
        """Tek soruyu parse eder - same logic as main app"""
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
                    aciklama = line.split('Açıklama:')[1].strip()
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

# Test parsing
quiz = TestQuiz()

with open('Worde_Yapistir/2020_DKAB_Sorulari.txt', 'r', encoding='utf-8') as file:
    content = file.read()

soru_blocks = content.split('---SONRAKİ SORU---')

for block in soru_blocks:
    if 'Soru ' in block and 'Doğru Cevap:' in block:
        question = quiz.parse_single_question(block, 2020)
        if question and question['soru_no'] in [3, 13]:
            print(f'Soru {question["soru_no"]} görsel bilgisi:')
            print(f'  Görsel var: {question.get("gorsel_var", False)}')
            print(f'  Görsel dosyaları: {question.get("gorsel_dosyalari", [])}')
            print('')
