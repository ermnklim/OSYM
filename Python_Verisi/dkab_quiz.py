#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DKAB ÖABT Sınavı Çözüm Scripti
2013-2023 yılları arası DKAB sorularını çözme pratiği yapın
"""

import json
import random
import os
from typing import Dict, List, Tuple

class DKABQuiz:
    def __init__(self):
        self.questions = []
        self.score = 0
        self.total_questions = 0
        self.current_year = None
        
    def load_questions_from_text(self, file_path: str, year: int):
        """Text dosyasından soruları yükler"""
        questions = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Soruları parçala
            soru_blocks = content.split('---SONRAKİ SORU---')
            
            for block in soru_blocks:
                if 'Soru ' in block and 'Doğru Cevap:' in block:
                    question = self.parse_question(block, year)
                    if question:
                        questions.append(question)
                        
        except Exception as e:
            print(f"Hata: {file_path} dosyası okunamadı: {e}")
            
        return questions
    
    def parse_question(self, text: str, year: int) -> Dict:
        """Tek bir soruyu parse eder"""
        try:
            lines = text.strip().split('\n')
            
            # Soru numarasını bul
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
                
                # Soru numarası
                if line.startswith('Soru ') and ':' in line:
                    soru_no = int(line.split()[1].replace(':', ''))
                
                # Soru metni (boş satıra kadar)
                elif line and not line.startswith('A)') and not line.startswith('B)') and not line.startswith('C)') and not line.startswith('D)') and not line.startswith('E)') and not line.startswith('Doğru Cevap:') and soru_no:
                    if line != 'Soru' and not line.startswith('KONU:') and not line.startswith('YIL:') and not line.startswith('DERS:'):
                        soru_metni.append(line)
                
                # Şıklar
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
                
                # Doğru cevap
                elif line.startswith('Doğru Cevap:'):
                    dogru_cevap = line.split(':')[1].strip()
                
                # Açıklama
                elif line.startswith('Açıklama:'):
                    aciklama_lines = []
                    i += 1
                    while i < len(lines) and not lines[i].startswith('---') and not lines[i].startswith('Görsel') and not lines[i].startswith('Tablo'):
                        aciklama_lines.append(lines[i].rstrip())
                        i += 1
                    aciklama = '\n'.join(aciklama_lines).strip()
                    i -= 1
                
                # Görsel kontrolü
                elif 'Görsel Notu:' in line or 'Görsel dosyası:' in line:
                    gorsel_var = True
                    if 'Görsel dosyası:' in line:
                        dosya_adi = line.split('Görsel dosyası:')[1].strip()
                        gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                
                i += 1
            
            if soru_no and len(options) == 5 and dogru_cevap:
                return {
                    "yil": year,
                    "ders": "DKAB",
                    "konu": "DKAB",
                    "soru_no": soru_no,
                    "soru_metni": '\n'.join(soru_metni).strip(),
                    "siklar": options,
                    "dogru_cevap": dogru_cevap,
                    "aciklama": aciklama,
                    "gorsel_var": gorsel_var,
                    "gorsel_dosyalari": gorsel_dosyalari,
                    "tablo_var": False,
                    "tablo_dosyalari": []
                }
        except Exception as e:
            print(f"Parse hatası: {e}")
            
        return None
    
    def load_all_questions(self):
        """Tüm yıllardaki soruları yükler"""
        base_path = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir"
        
        for year in range(2013, 2024):
            file_path = os.path.join(base_path, f"{year}_DKAB_Sorulari.txt")
            if os.path.exists(file_path):
                year_questions = self.load_questions_from_text(file_path, year)
                self.questions.extend(year_questions)
                print(f"{year} yılından {len(year_questions)} soru yüklendi")
        
        print(f"\nToplam {len(self.questions)} soru yüklendi!")
    
    def practice_session(self, year: int = None, num_questions: int = 10):
        """Pratik oturumu başlatır"""
        available_questions = self.questions
        
        if year:
            available_questions = [q for q in self.questions if q['yil'] == year]
            if not available_questions:
                print(f"{year} yılı için soru bulunamadı!")
                return
        
        if len(available_questions) < num_questions:
            num_questions = len(available_questions)
        
        selected_questions = random.sample(available_questions, num_questions)
        
        print(f"\n{'='*60}")
        print(f"DKAB PRATİK SINAVI")
        if year:
            print(f"Yıl: {year}")
        print(f"Soru Sayısı: {num_questions}")
        print(f"{'='*60}\n")
        
        self.score = 0
        self.total_questions = num_questions
        
        for i, question in enumerate(selected_questions, 1):
            self.ask_question(question, i)
        
        self.show_results()
    
    def ask_question(self, question: Dict, question_num: int):
        """Tek soru sorar"""
        print(f"\n{'-'*50}")
        print(f"Soru {question_num}/{self.total_questions} (Yıl: {question['yil']}, No: {question['soru_no']})")
        print(f"{'-'*50}")
        
        print(f"\n{question['soru_metni']}\n")
        
        # Şıkları karıştırarak göster
        options = list(question['siklar'].items())
        random.shuffle(options)
        
        option_map = {}
        for i, (key, value) in enumerate(options, 1):
            option_map[str(i)] = key
            print(f"{i}) {value}")
        
        # Görsel notu varsa belirt
        if question['gorsel_var']:
            print(f"\n📸 Bu soruda görsel bulunmaktadır!")
            for dosya in question['gorsel_dosyalari']:
                print(f"   📁 {dosya}")
        
        # Cevap al
        while True:
            try:
                cevap = input(f"\nCevabınız (1-5): ").strip()
                if cevap in option_map:
                    break
                else:
                    print("Lütfen 1-5 arasında bir seçim yapın!")
            except KeyboardInterrupt:
                print("\n\nTest iptal edildi!")
                return
        
        # Sonucu kontrol et
        dogru_sik = option_map[cevap]
        if dogru_sik == question['dogru_cevap']:
            print(f"\n✅ DOĞRU! Harika seçim!")
            self.score += 1
        else:
            print(f"\n❌ YANLIŞ!")
            print(f"   Doğru cevap: {question['dogru_cevap']}) {question['siklar'][question['dogru_cevap']]}")
            print(f"   Sizin cevabınız: {dogru_sik}) {question['siklar'][dogru_sik]}")
        
        # Açıklamayı göster
        if question['aciklama']:
            print(f"\n📝 Açıklama:")
            print(f"   {question['aciklama']}")
        
        input("\nDevam etmek için Enter'a basın...")
    
    def show_results(self):
        """Sonuçları gösterir"""
        print(f"\n{'='*60}")
        print(f"TEST SONUÇLARI")
        print(f"{'='*60}")
        print(f"Doğru Sayısı: {self.score}/{self.total_questions}")
        print(f"Başarı Oranı: {(self.score/self.total_questions)*100:.1f}%")
        
        if self.score >= self.total_questions * 0.8:
            print("🎉 MÜKEMMEL! Çok başarılısın!")
        elif self.score >= self.total_questions * 0.6:
            print("👏 İYİ! Başarılısın, devam et!")
        elif self.score >= self.total_questions * 0.4:
            print("📚 ORTA! Daha fazla çalışmalısın!")
        else:
            print("💪 ÇALIŞMAN GEREKİYOR! Vazgeçme!")
    
    def show_statistics(self):
        """İstatistikleri gösterir"""
        if not self.questions:
            print("Henüz soru yüklenmedi!")
            return
        
        print(f"\n{'='*60}")
        print(f"İSTATİSTİKLER")
        print(f"{'='*60}")
        
        # Yıllara göre dağılım
        year_dist = {}
        for q in self.questions:
            year = q['yil']
            year_dist[year] = year_dist.get(year, 0) + 1
        
        print("Yıllara göre soru dağılımı:")
        for year in sorted(year_dist.keys()):
            print(f"  {year}: {year_dist[year]} soru")
        
        print(f"\nToplam: {len(self.questions)} soru")
    
    def export_to_json(self, output_file: str):
        """Soruları JSON formatında dışa aktarır"""
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(self.questions, file, ensure_ascii=False, indent=2)
            print(f"Sorular {output_file} dosyasına aktarıldı!")
        except Exception as e:
            print(f"Dışa aktarma hatası: {e}")

def main():
    """Ana menü"""
    quiz = DKABQuiz()
    
    print("🎓 DKAB ÖABT PRATİK UYGULAMASI")
    print("=" * 50)
    
    while True:
        print("\n📋 MENÜ:")
        print("1. Tüm soruları yükle")
        print("2. Pratik test yap (rastgele)")
        print("3. Belirli bir yıldan pratik yap")
        print("4. İstatistikleri göster")
        print("5. JSON olarak dışa aktar")
        print("0. Çıkış")
        
        try:
            choice = input("\nSeçiminiz (0-5): ").strip()
            
            if choice == '0':
                print("Görüşmek üzere! 👋")
                break
            elif choice == '1':
                print("\nSorular yükleniyor...")
                quiz.load_all_questions()
            elif choice == '2':
                if not quiz.questions:
                    print("Önce soruları yüklemeniz gerekiyor (Seçenek 1)!")
                else:
                    try:
                        num = int(input("Kaç soruluk test istersiniz? (1-50): "))
                        if 1 <= num <= 50:
                            quiz.practice_session(num_questions=num)
                        else:
                            print("Lütfen 1-50 arasında bir sayı girin!")
                    except ValueError:
                        print("Geçersiz sayı!")
            elif choice == '3':
                if not quiz.questions:
                    print("Önce soruları yüklemeniz gerekiyor (Seçenek 1)!")
                else:
                    try:
                        year = int(input("Hangi yıl (2013-2023): "))
                        num = int(input("Kaç soru: "))
                        if 2013 <= year <= 2023 and 1 <= num <= 50:
                            quiz.practice_session(year=year, num_questions=num)
                        else:
                            print("Geçersiz yıl veya soru sayısı!")
                    except ValueError:
                        print("Geçersiz değer!")
            elif choice == '4':
                quiz.show_statistics()
            elif choice == '5':
                if not quiz.questions:
                    print("Önce soruları yüklemeniz gerekiyor (Seçenek 1)!")
                else:
                    output_file = r"C:\Users\osman\Desktop\OSYM\Python_Verisi\dkab_questions.json"
                    quiz.export_to_json(output_file)
            else:
                print("Geçersiz seçim! Lütfen 0-5 arasında bir seçim yapın.")
                
        except KeyboardInterrupt:
            print("\n\nProgramdan çıkılıyor... Görüşürüz! 👋")
            break
        except Exception as e:
            print(f"Bir hata oluştu: {e}")

if __name__ == "__main__":
    main()
