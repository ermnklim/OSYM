#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DKAB ÖABT Sınavı Çözüm Scripti - GUI Version
2013-2023 yılları arası DKAB sorularını çözme pratiği yapın
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import random
import os
from typing import Dict, List, Tuple
import threading

class DKABQuizGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎓 DKAB ÖABT Pratik Sınavı")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.questions = []
        self.current_question = None
        self.current_index = 0
        self.score = 0
        self.total_questions = 0
        self.selected_year = None
        self.selected_num = 10
        
        # Colors
        self.colors = {
            'bg': '#f0f0f0',
            'header': '#2c3e50',
            'correct': '#27ae60',
            'wrong': '#e74c3c',
            'button': '#3498db',
            'button_hover': '#2980b9'
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Ana arayüzü kurar"""
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors['header'], height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🎓 DKAB ÖABT PRATİK SINAVI", 
                               font=("Arial", 20, "bold"), 
                               fg='white', bg=self.colors['header'])
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(header_frame, text="2013-2023 Din Kültürü ve Ahlak Bilgisi Öğretmenliği", 
                                 font=("Arial", 12), 
                                 fg='#ecf0f1', bg=self.colors['header'])
        subtitle_label.pack()
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Settings
        left_panel = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Settings Frame
        settings_frame = tk.LabelFrame(left_panel, text="⚙️ Test Ayarları", 
                                      font=("Arial", 12, "bold"), bg='white')
        settings_frame.pack(padx=10, pady=10, fill=tk.X)
        
        # Year selection
        tk.Label(settings_frame, text="Yıl Seçimi:", font=("Arial", 10), bg='white').pack(anchor=tk.W, padx=5, pady=(5,0))
        
        self.year_var = tk.StringVar(value="Tüm yıllar")
        years = ["Tüm yıllar"] + [str(year) for year in range(2013, 2024)]
        self.year_combo = ttk.Combobox(settings_frame, textvariable=self.year_var, 
                                       values=years, state="readonly", width=15)
        self.year_combo.pack(padx=5, pady=5, fill=tk.X)
        
        # Question count
        tk.Label(settings_frame, text="Soru Sayısı:", font=("Arial", 10), bg='white').pack(anchor=tk.W, padx=5, pady=(10,0))
        
        self.num_var = tk.StringVar(value="10")
        num_frame = tk.Frame(settings_frame, bg='white')
        num_frame.pack(padx=5, pady=5, fill=tk.X)
        
        self.num_spinbox = tk.Spinbox(num_frame, from_=1, to=50, textvariable=self.num_var, width=10)
        self.num_spinbox.pack(side=tk.LEFT)
        
        # Start button
        self.start_button = tk.Button(settings_frame, text="🚀 TESTİ BAŞLAT", 
                                     font=("Arial", 12, "bold"),
                                     bg=self.colors['button'], fg='white',
                                     command=self.start_quiz,
                                     cursor="hand2")
        self.start_button.pack(padx=5, pady=10, fill=tk.X, ipady=5)
        
        # Statistics Frame
        stats_frame = tk.LabelFrame(left_panel, text="📊 İstatistikler", 
                                    font=("Arial", 12, "bold"), bg='white')
        stats_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.stats_label = tk.Label(stats_frame, text="Henüz test yapılmadı\n\n", 
                                   font=("Arial", 9), bg='white', justify=tk.LEFT)
        self.stats_label.pack(padx=5, pady=5, anchor=tk.W)
        
        # Load questions button
        self.load_button = tk.Button(left_panel, text="📁 SORULARI YÜKLE", 
                                     font=("Arial", 10),
                                     bg='#95a5a6', fg='white',
                                     command=self.load_questions,
                                     cursor="hand2")
        self.load_button.pack(padx=10, pady=10, fill=tk.X)
        
        # Right panel - Quiz area
        self.right_panel = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=1)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Welcome screen
        self.show_welcome_screen()
        
    def show_welcome_screen(self):
        """Hoş geldin ekranını gösterir"""
        # Clear right panel
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        welcome_frame = tk.Frame(self.right_panel, bg='white')
        welcome_frame.pack(expand=True, fill=tk.BOTH)
        
        # Welcome message
        welcome_text = """
🎓 DKAB ÖABT PRATİK SINAVINA HOŞ GELDİNİZ!

Bu uygulama ile 2013-2023 yılları arası Din Kültürü ve Ahlak Bilgisi 
Öğretmenliği ÖABT sınav soruları üzerinde pratik yapabilirsin.

📋 Özellikler:
• Rastgele soru seçimi
• Yıl bazında pratik
• Anlık sonuç ve açıklama
• Görsel desteği
• Detaylı istatistikler

🚀 Başlamak için:
1. Önce "SORULARI YÜKLE" butonuna tıklayın
2. Yıl ve soru sayısını seçin
3. "TESTİ BAŞLAT" butonuna tıklayın

Başarılar dilerim! 🌟
        """
        
        welcome_label = tk.Label(welcome_frame, text=welcome_text, 
                                font=("Arial", 12), bg='white', justify=tk.LEFT)
        welcome_label.pack(expand=True, pady=50)
        
    def load_questions(self):
        """Soruları yükler"""
        def load_in_background():
            try:
                base_path = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir"
                loaded_questions = []
                
                for year in range(2013, 2024):
                    file_path = os.path.join(base_path, f"{year}_DKAB_Sorulari.txt")
                    if os.path.exists(file_path):
                        year_questions = self.parse_questions_from_file(file_path, year)
                        loaded_questions.extend(year_questions)
                
                self.questions = loaded_questions
                self.update_stats()
                
                # Update UI in main thread
                self.root.after(0, lambda: self.load_button.config(
                    text=f"✅ {len(self.questions)} SORU YÜKLENDİ", 
                    bg=self.colors['correct']
                ))
                
                messagebox.showinfo("Başarılı", f"Toplam {len(self.questions)} soru yüklendi!")
                
            except Exception as e:
                messagebox.showerror("Hata", f"Sorular yüklenirken hata oluştu: {e}")
        
        # Show loading message
        self.load_button.config(text="⏳ YÜKLENİYOR...", bg='#f39c12')
        self.root.after(100, load_in_background)
        
    def parse_questions_from_file(self, file_path: str, year: int) -> List[Dict]:
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
    
    def parse_single_question(self, text: str, year: int) -> Dict:
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
    
    def update_stats(self):
        """İstatistikleri günceller"""
        if not self.questions:
            self.stats_label.config(text="Henüz soru yüklenmedi\n\n")
            return
        
        year_dist = {}
        for q in self.questions:
            year = q['yil']
            year_dist[year] = year_dist.get(year, 0) + 1
        
        stats_text = f"Toplam Soru: {len(self.questions)}\n\n"
        stats_text += "Yıllara göre dağılım:\n"
        for year in sorted(year_dist.keys()):
            stats_text += f"  {year}: {year_dist[year]} soru\n"
        
        self.stats_label.config(text=stats_text)
    
    def start_quiz(self):
        """Quiz'i başlatır"""
        if not self.questions:
            messagebox.showwarning("Uyarı", "Önce soruları yükleyin!")
            return
        
        try:
            num_questions = int(self.num_var.get())
            if num_questions < 1 or num_questions > 50:
                messagebox.showwarning("Uyarı", "Soru sayısı 1-50 arasında olmalı!")
                return
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir soru sayısı girin!")
            return
        
        # Filter questions by year if selected
        available_questions = self.questions
        selected_year = self.year_var.get()
        
        if selected_year != "Tüm yıllar":
            year = int(selected_year)
            available_questions = [q for q in self.questions if q['yil'] == year]
            if not available_questions:
                messagebox.showwarning("Uyarı", f"{year} yılı için soru bulunamadı!")
                return
        
        if len(available_questions) < num_questions:
            num_questions = len(available_questions)
        
        # Select random questions
        self.quiz_questions = random.sample(available_questions, num_questions)
        self.current_index = 0
        self.score = 0
        self.total_questions = num_questions
        
        # Start quiz
        self.show_question()
    
    def show_question(self):
        """Soruyu gösterir"""
        if self.current_index >= len(self.quiz_questions):
            self.show_results()
            return
        
        # Clear right panel
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        question = self.quiz_questions[self.current_index]
        
        # Question frame
        question_frame = tk.Frame(self.right_panel, bg='white')
        question_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header info
        info_frame = tk.Frame(question_frame, bg='white')
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(info_frame, text=f"Soru {self.current_index + 1}/{self.total_questions}", 
                font=("Arial", 14, "bold"), bg='white').pack(side=tk.LEFT)
        
        tk.Label(info_frame, text=f"Yıl: {question['yil']} | No: {question['soru_no']}", 
                font=("Arial", 10), bg='white', fg='#7f8c8d').pack(side=tk.RIGHT)
        
        # Progress bar
        progress = (self.current_index + 1) / self.total_questions
        progress_frame = tk.Frame(question_frame, bg='white')
        progress_frame.pack(fill=tk.X, pady=5)
        
        canvas = tk.Canvas(progress_frame, height=10, bg='#ecf0f1', highlightthickness=0)
        canvas.pack(fill=tk.X)
        canvas.create_rectangle(0, 0, canvas.winfo_width() * progress, 10, 
                                fill=self.colors['button'], tags="progress")
        
        # Question text
        question_text_frame = tk.Frame(question_frame, bg='#f8f9fa', relief=tk.RIDGE, bd=1)
        question_text_frame.pack(fill=tk.X, pady=10)
        
        question_text = tk.Text(question_text_frame, font=("Arial", 11), 
                               bg='#f8f9fa', wrap=tk.WORD, height=6)
        question_text.pack(padx=10, pady=10)
        question_text.insert(tk.END, question['soru_metni'])
        question_text.config(state=tk.DISABLED)
        
        # Visual notification if exists
        if question['gorsel_var']:
            visual_frame = tk.Frame(question_frame, bg='#fff3cd', relief=tk.RIDGE, bd=1)
            visual_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(visual_frame, text="📸 Bu soruda görsel bulunmaktadır!", 
                    font=("Arial", 10, "bold"), bg='#fff3cd', fg='#856404').pack(pady=5)
            
            for dosya in question['gorsel_dosyalari']:
                tk.Label(visual_frame, text=f"📁 {dosya}", 
                        font=("Arial", 9), bg='#fff3cd', fg='#856404').pack()
        
        # Options
        options_frame = tk.Frame(question_frame, bg='white')
        options_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Shuffle options
        options = list(question['siklar'].items())
        random.shuffle(options)
        
        self.option_vars = {}
        self.option_map = {}
        
        for i, (key, value) in enumerate(options, 1):
            self.option_map[str(i)] = key
            
            option_frame = tk.Frame(options_frame, bg='white')
            option_frame.pack(fill=tk.X, pady=5)
            
            var = tk.StringVar()
            self.option_vars[str(i)] = var
            
            rb = tk.Radiobutton(option_frame, text=f"{i}) {value}", 
                               variable=var, value=str(i),
                               font=("Arial", 11), bg='white',
                               command=lambda v=var: self.select_option(v))
            rb.pack(anchor=tk.W)
        
        # Buttons
        button_frame = tk.Frame(question_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=20)
        
        self.submit_button = tk.Button(button_frame, text="CEVABI GÖNDER", 
                                      font=("Arial", 12, "bold"),
                                      bg=self.colors['button'], fg='white',
                                      command=self.check_answer,
                                      cursor="hand2")
        self.submit_button.pack(side=tk.RIGHT, padx=5)
        
        if self.current_index > 0:
            prev_button = tk.Button(button_frame, text="← ÖNCEKİ", 
                                   font=("Arial", 10),
                                   bg='#95a5a6', fg='white',
                                   command=self.previous_question,
                                   cursor="hand2")
            prev_button.pack(side=tk.LEFT, padx=5)
    
    def select_option(self, var):
        """Seçenek seçildiğinde"""
        # Enable submit button
        self.submit_button.config(bg=self.colors['correct'])
    
    def check_answer(self):
        """Cevabı kontrol eder"""
        # Get selected option
        selected = None
        for key, var in self.option_vars.items():
            if var.get():
                selected = key
                break
        
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir seçenek seçin!")
            return
        
        question = self.quiz_questions[self.current_index]
        dogru_sik = self.option_map[selected]
        
        # Show result
        result_frame = tk.Frame(self.right_panel, bg='white')
        result_frame.pack(fill=tk.X, padx=20, pady=10)
        
        if dogru_sik == question['dogru_cevap']:
            self.score += 1
            result_label = tk.Label(result_frame, text="✅ DOĞRU CEVAP!", 
                                  font=("Arial", 14, "bold"), 
                                  bg='white', fg=self.colors['correct'])
            result_label.pack()
        else:
            result_label = tk.Label(result_frame, text="❌ YANLIŞ CEVAP!", 
                                  font=("Arial", 14, "bold"), 
                                  bg='white', fg=self.colors['wrong'])
            result_label.pack()
            
            correct_label = tk.Label(result_frame, 
                                   text=f"Doğru cevap: {question['dogru_cevap']}) {question['siklar'][question['dogru_cevap']]}", 
                                   font=("Arial", 11), 
                                   bg='white', fg=self.colors['wrong'])
            correct_label.pack(pady=5)
        
        # Explanation
        if question['aciklama']:
            exp_frame = tk.Frame(self.right_panel, bg='#e8f5e8', relief=tk.RIDGE, bd=1)
            exp_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Label(exp_frame, text="📝 AÇIKLAMA:", 
                    font=("Arial", 11, "bold"), 
                    bg='#e8f5e8').pack(anchor=tk.W, padx=10, pady=(10,5))
            
            exp_text = tk.Text(exp_frame, font=("Arial", 10), 
                              bg='#e8f5e8', wrap=tk.WORD, height=4)
            exp_text.pack(padx=10, pady=(0,10))
            exp_text.insert(tk.END, question['aciklama'])
            exp_text.config(state=tk.DISABLED)
        
        # Next button
        if self.current_index < len(self.quiz_questions) - 1:
            next_button = tk.Button(self.right_panel, text="SONRAKİ SORU →", 
                                   font=("Arial", 12, "bold"),
                                   bg=self.colors['button'], fg='white',
                                   command=self.next_question,
                                   cursor="hand2")
            next_button.pack(pady=20)
        else:
            finish_button = tk.Button(self.right_panel, text="TESTİ BİTİR", 
                                      font=("Arial", 12, "bold"),
                                      bg=self.colors['correct'], fg='white',
                                      command=self.show_results,
                                      cursor="hand2")
            finish_button.pack(pady=20)
    
    def next_question(self):
        """Sonraki soruya geçer"""
        self.current_index += 1
        self.show_question()
    
    def previous_question(self):
        """Önceki soruya döner"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()
    
    def show_results(self):
        """Sonuçları gösterir"""
        # Clear right panel
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        results_frame = tk.Frame(self.right_panel, bg='white')
        results_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)
        
        # Results header
        tk.Label(results_frame, text="🎯 TEST SONUÇLARI", 
                font=("Arial", 20, "bold"), bg='white').pack(pady=20)
        
        # Score
        score_text = f"{self.score}/{self.total_questions}"
        percentage = (self.score / self.total_questions) * 100
        
        score_label = tk.Label(results_frame, text=score_text, 
                              font=("Arial", 48, "bold"), bg='white')
        score_label.pack(pady=10)
        
        percentage_label = tk.Label(results_frame, text=f"Başarı Oranı: %{percentage:.1f}", 
                                   font=("Arial", 14), bg='white')
        percentage_label.pack(pady=5)
        
        # Message
        if percentage >= 80:
            message = "🎉 MÜKEMMEL! Çok başarılısın!"
            color = self.colors['correct']
        elif percentage >= 60:
            message = "👏 İYİ! Başarılısın, devam et!"
            color = self.colors['button']
        elif percentage >= 40:
            message = "📚 ORTA! Daha fazla çalışmalısın!"
            color = '#f39c12'
        else:
            message = "💪 ÇALIŞMAN GEREKİYOR! Vazgeçme!"
            color = self.colors['wrong']
        
        message_label = tk.Label(results_frame, text=message, 
                               font=("Arial", 16, "bold"), 
                               bg='white', fg=color)
        message_label.pack(pady=20)
        
        # Buttons
        button_frame = tk.Frame(results_frame, bg='white')
        button_frame.pack(pady=30)
        
        new_test_button = tk.Button(button_frame, text="YENİ TEST", 
                                   font=("Arial", 12, "bold"),
                                   bg=self.colors['button'], fg='white',
                                   command=self.new_test,
                                   cursor="hand2")
        new_test_button.pack(side=tk.LEFT, padx=10)
        
        menu_button = tk.Button(button_frame, text="ANA MENÜ", 
                              font=("Arial", 12, "bold"),
                              bg='#95a5a6', fg='white',
                              command=self.show_welcome_screen,
                              cursor="hand2")
        menu_button.pack(side=tk.LEFT, padx=10)
    
    def new_test(self):
        """Yeni test başlatır"""
        self.start_quiz()

def main():
    root = tk.Tk()
    app = DKABQuizGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
