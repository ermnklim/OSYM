import sys
import os

# Add the Python_Verisi directory to the path
sys.path.append('c:\\Users\\osman\\Desktop\\OSYM\\Python_Verisi')

# Import just the parsing functions
import dkab_quiz_modern

# Create a simple test class
class TestQuiz:
    def __init__(self):
        pass
    
    def parse_questions_from_file(self, file_path: str, year: int):
        """Dosyadan soruları parse eder"""
        questions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            soru_blocks = content.split('---SONRAKİ SORU---')
            
            for block in soru_blocks:
                if 'Soru ' in block and 'Doğru Cevap:' in block:
                    question = self.parse_single_question(block, year)
                    if question:
                        questions.append(question)
                        
        except Exception as e:
            print(f"Parse hatası {year}: {e}")
            
        return questions
    
    def parse_single_question(self, text: str, year: int):
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
                    while i < len(lines) and not lines[i].startswith('---') and not lines[i].startswith('Görsel') and not lines[i].startswith('Tablo'):
                        aciklama_lines.append(lines[i].rstrip())
                        i += 1
                    aciklama = '\n'.join(aciklama_lines).strip()
                    i -= 1
                elif 'Görsel Notu:' in line or 'Görsel dosyası:' in line:
                    gorsel_var = True
                    if 'Görsel dosyası:' in line:
                        dosya_adi = line.split('Görsel dosyası:')[1].strip()
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

# Test the parsing
test_quiz = TestQuiz()
questions_2018 = test_quiz.parse_questions_from_file('c:\\Users\\osman\\Desktop\\OSYM\\Worde_Yapistir\\2018_DKAB_Sorulari.txt', 2018)

print('Toplam parsed questions:', len(questions_2018))
for i, q in enumerate(questions_2018):
    print('Question', i+1, ':', q.get('soru_no', 'No number'))
