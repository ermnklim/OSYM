#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DKAB ÖABT Sınavı Çözüm Scripti - Modern GUI Version
2013-2025 yılları arası DKAB sorularını çözme pratiği yapın
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import random
import os
from typing import Dict, List, Tuple
import threading

class ModernDKABQuiz:
    def __init__(self, root):
        self.root = root
        self.root.title("🎓 DKAB ÖABT Pratik Sınavı")
        self.root.geometry("1000x750")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(True, True)
        
        # Variables
        self.questions = []
        self.current_question = None
        self.current_index = 0
        self.score = 0
        self.total_questions = 0
        self.selected_year = None
        self.selected_num = 10
        self.quiz_questions = []
        self.test_history = []  # Store test history
        
        # Modern color scheme
        self.colors = {
            'bg': '#1a1a2e',
            'card': '#16213e',
            'accent': '#e94560',
            'primary': '#0f3460',
            'success': '#00b894',
            'warning': '#fdcb6e',
            'danger': '#d63031',
            'text': '#ffffff',
            'text_secondary': '#b2bec3',
            'border': '#2d3561'
        }
        
        # Font styles
        self.fonts = {
            'title': ('Segoe UI', 24, 'bold'),
            'subtitle': ('Segoe UI', 12),
            'header': ('Segoe UI', 16, 'bold'),
            'body': ('Segoe UI', 11),
            'button': ('Segoe UI', 10, 'bold'),
            'small': ('Segoe UI', 9)
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Modern arayüzü kurar"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_container)
        
        # Content area
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left sidebar
        self.create_sidebar(content_frame)
        
        # Main content area
        self.create_main_content(content_frame)
        
        # Show welcome screen
        self.show_welcome_screen()
        
    def create_header(self, parent):
        """Modern header oluşturur"""
        header = tk.Frame(parent, bg=self.colors['card'], height=80)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        header.pack_propagate(False)
        
        # Title
        title_frame = tk.Frame(header, bg=self.colors['card'])
        title_frame.pack(expand=True, fill=tk.BOTH)
        
        title_label = tk.Label(title_frame, text="🎓 DKAB ÖABT PRATİK SINAVI", 
                               font=self.fonts['title'], 
                               fg=self.colors['text'], bg=self.colors['card'])
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        subtitle_label = tk.Label(title_frame, text="2013-2025 Din Kültürü ve Ahlak Bilgisi Öğretmenliği", 
                                 font=self.fonts['subtitle'], 
                                 fg=self.colors['text_secondary'], bg=self.colors['card'])
        subtitle_label.pack(side=tk.LEFT, padx=(0, 20), pady=25)
        
        # Status indicator
        self.status_label = tk.Label(title_frame, text="🔴 Hazır Değil", 
                                    font=self.fonts['body'], 
                                    fg=self.colors['danger'], bg=self.colors['card'])
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=25)
        
    def create_sidebar(self, parent):
        """Sol sidebar oluşturur"""
        sidebar = tk.Frame(parent, bg=self.colors['card'], width=240)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        sidebar.pack_propagate(False)
        
        # Settings card
        settings_card = self.create_card(sidebar, "⚙️ Ayarlar")
        settings_card.pack(fill=tk.X, padx=2, pady=2)
        
        # Year selection
        tk.Label(settings_card, text="Yıl:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.year_var = tk.StringVar(value="Tüm yıllar")
        years = ["Tüm yıllar"] + [str(year) for year in range(2013, 2026)]
        self.year_combo = ttk.Combobox(settings_card, textvariable=self.year_var, 
                                       values=years, state="readonly", width=14)
        self.year_combo.pack(padx=5, pady=0, fill=tk.X)
        self.year_combo.bind("<<ComboboxSelected>>", self.update_question_limit)
        
        # Test mode selection
        tk.Label(settings_card, text="Mod:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.mode_var = tk.StringVar(value="Anında Cevap")
        mode_options = ["Anında Cevap", "Test Sonu Değerlendir"]
        self.mode_combo = ttk.Combobox(settings_card, textvariable=self.mode_var, 
                                      values=mode_options, state="readonly", width=14)
        self.mode_combo.pack(padx=5, pady=0, fill=tk.X)
        
        # Question order selection
        tk.Label(settings_card, text="Sıra:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.order_var = tk.StringVar(value="Rastgele")
        order_options = ["Rastgele", "Sıralı"]
        self.order_combo = ttk.Combobox(settings_card, textvariable=self.order_var, 
                                       values=order_options, state="readonly", width=14)
        self.order_combo.pack(padx=5, pady=0, fill=tk.X)
        
        # Question count
        tk.Label(settings_card, text="Soru:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.num_var = tk.StringVar(value="10")
        num_frame = tk.Frame(settings_card, bg=self.colors['card'])
        num_frame.pack(padx=5, pady=0, fill=tk.X)
        
        self.num_spinbox = tk.Spinbox(num_frame, from_=1, to=75, textvariable=self.num_var, 
                                      width=5, font=('Segoe UI', 8))
        self.num_spinbox.pack(side=tk.LEFT)
        
        # Start button
        self.start_button = self.create_button(settings_card, "🚀 BAŞLAT", 
                                              self.start_quiz, self.colors['success'])
        self.start_button.pack(padx=5, pady=3, fill=tk.X, ipady=2)
        
        # Statistics card
        stats_card = self.create_card(sidebar, "📊 İstatistik")
        stats_card.pack(fill=tk.X, padx=2, pady=2)
        
        self.stats_text = tk.Text(stats_card, height=4, width=25, 
                                  font=('Segoe UI', 8), 
                                  bg=self.colors['primary'], fg=self.colors['text'],
                                  relief=tk.FLAT, padx=4, pady=4)
        self.stats_text.pack(padx=2, pady=2, fill=tk.BOTH, expand=True)
        self.stats_text.insert(tk.END, "Henüz soru yüklenmedi\n\n")
        self.stats_text.config(state=tk.DISABLED)
        
        # Load button
        self.load_button = self.create_button(sidebar, "📁 YÜKLE", 
                                             self.load_questions, self.colors['warning'])
        self.load_button.pack(padx=2, pady=2, fill=tk.X, ipady=2)

        # --- Soruya Git Kartı ---
        goto_card = self.create_card(sidebar, "🔍 Soruya Git")
        goto_card.pack(fill=tk.X, padx=2, pady=2)

        tk.Label(goto_card, text="Yıl:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.goto_year_var = tk.StringVar(value="2019")
        goto_years = [str(y) for y in range(2013, 2026)]
        self.goto_year_combo = ttk.Combobox(goto_card, textvariable=self.goto_year_var,
                                            values=goto_years, state="readonly", width=14)
        self.goto_year_combo.pack(padx=5, pady=0, fill=tk.X)
        self.goto_year_combo.bind("<<ComboboxSelected>>", self._update_goto_question_list)

        tk.Label(goto_card, text="Soru No:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.goto_q_var = tk.StringVar(value="1")
        self.goto_q_combo = ttk.Combobox(goto_card, textvariable=self.goto_q_var,
                                         values=[str(i) for i in range(1, 76)],
                                         state="normal", width=14)
        self.goto_q_combo.pack(padx=5, pady=0, fill=tk.X)

        self.goto_btn = self.create_button(goto_card, "🔎 SORUYU AÇ",
                                           self.open_specific_question, self.colors['accent'])
        self.goto_btn.pack(padx=5, pady=5, fill=tk.X, ipady=2)
        
    def create_main_content(self, parent):
        """Ana içerik alanı oluşturur (Kaydırılabilir)"""
        self.main_container = tk.Frame(parent, bg=self.colors['card'])
        self.main_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.main_container, bg=self.colors['card'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.main_content = tk.Frame(self.canvas, bg=self.colors['card'])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.main_content, anchor="nw")
        
        self.main_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        def _on_mousewheel(event):
            try:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                pass
                
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def create_card(self, parent, title):
        """Modern kart oluşturur"""
        card = tk.Frame(parent, bg=self.colors['card'], relief=tk.RAISED, bd=1)
        
        # Card header
        header = tk.Frame(card, bg=self.colors['primary'], height=20)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_label = tk.Label(header, text=title, font=('Segoe UI', 8, 'bold'), 
                              fg=self.colors['text'], bg=self.colors['primary'])
        title_label.pack(pady=1)
        
        return card
        
    def create_button(self, parent, text, command, color):
        """Modern buton oluşturur"""
        button = tk.Button(parent, text=text, command=command,
                          font=self.fonts['button'],
                          bg=color, fg=self.colors['text'],
                          relief=tk.FLAT, cursor="hand2",
                          activebackground=self.darken_color(color),
                          activeforeground=self.colors['text'])
        
        # Hover effects
        def on_enter(e):
            button.config(bg=self.lighten_color(color))
        def on_leave(e):
            button.config(bg=color)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
        
    def lighten_color(self, color):
        """Rengi aydınlatır"""
        return color
        
    def darken_color(self, color):
        """Rengi koyulaştırır"""
        return color
        
    def show_welcome_screen(self):
        """Hoş geldin ekranını gösterir"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
            
        welcome_card = self.create_card(self.main_content, "🌟 Hoş Geldiniz")
        welcome_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content_frame = tk.Frame(welcome_card, bg=self.colors['card'])
        content_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        welcome_text = """
🎓 DKAB ÖABT PRATİK SINAVINA HOŞ GELDİNİZ!

Bu modern uygulama ile 2013-2025 yılları arası Din Kültürü ve Ahlak Bilgisi 
Öğretmenliği ÖABT sınav soruları üzerinde pratik yapabilirsin.

📋 Özellikler:
• Modern ve şık arayüz
• Rastgele soru seçimi
• Yıl bazında pratik
• Anlık sonuç ve açıklama
• Görsel desteği
• Detaylı istatistikler
• İlerleme takibi

🚀 Başlamak için:
1. Önce "SORULARI YÜKLE" butonuna tıklayın
2. Yıl ve soru sayısını seçin
3. "TESTİ BAŞLAT" butonuna tıklayın

Başarılar dilerim! 🌟
        """
        
        welcome_label = tk.Label(content_frame, text=welcome_text, 
                                font=self.fonts['body'], bg=self.colors['card'], 
                                fg=self.colors['text'], justify=tk.LEFT)
        welcome_label.pack(expand=True, pady=30)
        
    def load_questions(self):
        """Soruları yükler"""
        def load_in_background():
            try:
                base_path = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir"
                loaded_questions = []
                
                for year in range(2013, 2026):
                    file_path = os.path.join(base_path, f"{year}_DKAB_Sorulari.txt")
                    if os.path.exists(file_path):
                        year_questions = self.parse_questions_from_file(file_path, year)
                        loaded_questions.extend(year_questions)
                        print(f"{year} yılından {len(year_questions)} soru yüklendi")
                
                self.questions = loaded_questions
                self.update_stats()
                self.root.after(0, self.update_question_limit)
                
                # Update UI in main thread
                self.root.after(0, self.questions_loaded_successfully)
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Sorular yüklenirken hata oluştu: {e}"))
        
        # Show loading message
        self.load_button.config(text="⏳ YÜKLENİYOR...", bg=self.colors['text_secondary'])
        self.root.after(100, load_in_background)
        
    def questions_loaded_successfully(self):
        """Sorular başarıyla yüklendiğinde"""
        self.load_button.config(text=f"✅ {len(self.questions)} SORU YÜKLENDİ", bg=self.colors['success'])
        self.status_label.config(text="🟢 Hazır", fg=self.colors['success'])
        messagebox.showinfo("Başarılı", f"Toplam {len(self.questions)} soru yüklendi!")
        
    def parse_questions_from_file(self, file_path: str, year: int) -> List[Dict]:
        """Dosyadan sorular? parse eder"""
        questions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            content = content.replace('---SONRAKİ SORU---', '---SONRAKI SORU---')
            content = content.replace('---SONRAKÄ° SORU---', '---SONRAKI SORU---')
            content = content.replace('---SONRAK? SORU---', '---SONRAKI SORU---')
            content = content.replace('---SONRAK?? SORU---', '---SONRAKI SORU---')
            soru_blocks = content.split('---SONRAKI SORU---')
            
            for block in soru_blocks:
                if 'Soru ' in block and ('Doğru Cevap:' in block or 'Dogru Cevap:' in block or 'DoÄŸru Cevap:' in block or 'Do?ru Cevap:' in block or 'Do??ru Cevap:' in block):
                    question = self.parse_single_question(block, year)
                    if question:
                        questions.append(question)
                        
        except Exception as e:
            print(f"Parse hatas? {year}: {e}")
            
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
                elif line and not line.startswith('A)') and not line.startswith('B)') and not line.startswith('C)') and not line.startswith('D)') and not line.startswith('E)') and not line.startswith('Doğru Cevap:') and not line.startswith('Dogru Cevap:') and not line.startswith('DoÄŸru Cevap:') and not line.startswith('Do?ru Cevap:') and not line.startswith('Do??ru Cevap:') and not line.startswith('Açıklama:') and not line.startswith('Aciklama:') and not line.startswith('AÃ§Ä±klama:') and not line.startswith('A??klama:') and not line.startswith('A????klama:') and not line.startswith('Görsel') and not line.startswith('Gorsel') and not line.startswith('GÃ¶rsel') and not line.startswith('G?rsel') and not line.startswith('G??rsel') and not line.startswith('Dosya:') and not line.startswith('Konum:') and soru_no and not line.startswith('KONU:') and not line.startswith('YIL:') and not line.startswith('DERS:'):
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
                elif line.startswith('Doğru Cevap:') or line.startswith('Dogru Cevap:') or line.startswith('DoÄŸru Cevap:') or line.startswith('Do?ru Cevap:') or line.startswith('Do??ru Cevap:'):
                    dogru_cevap = line.split(':', 1)[1].strip()
                elif line.startswith('Açıklama:') or line.startswith('Aciklama:') or line.startswith('AÃ§Ä±klama:') or line.startswith('A??klama:') or line.startswith('A????klama:'):
                    aciklama = line.split(':', 1)[1].strip()
                elif 'Görsel Notu:' in line or 'Gorsel Notu:' in line or 'GÃ¶rsel Notu:' in line or 'G?rsel Notu:' in line or 'G??rsel Notu:' in line or 'Görsel dosyası:' in line or 'Gorsel dosyasi:' in line or 'GÃ¶rsel dosyasÄ±:' in line or 'G?rsel dosyas?:' in line or 'G??rsel dosyas??:' in line or 'Dosya:' in line:
                    gorsel_var = True
                    if 'Görsel dosyası:' in line:
                        dosya_adi = line.split('Görsel dosyası:')[1].strip()
                        gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                    elif 'GÃ¶rsel dosyasÄ±:' in line:
                        dosya_adi = line.split('GÃ¶rsel dosyasÄ±:')[1].strip()
                        gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                    elif 'G?rsel dosyas?:' in line:
                        dosya_adi = line.split('G?rsel dosyas?:')[1].strip()
                        gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                    elif 'Gorsel dosyasi:' in line:
                        dosya_adi = line.split('Gorsel dosyasi:')[1].strip()
                        gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                    elif 'G??rsel dosyas??:' in line:
                        dosya_adi = line.split('G??rsel dosyas??:')[1].strip()
                        gorsel_dosyalari.append(f"C:\\Users\\osman\\Desktop\\OSYM\\Gorseller\\{year}\\{dosya_adi}")
                    elif 'Dosya:' in line:
                        dosya_adi = line.split('Dosya:')[1].strip()
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
            print(f"Parse hatas?: {e}")
            
        return None

    def get_question_limit_for_year(self, selected_year):
        """Yila veya tum yillara gore maksimum soru sayisini doner."""
        if selected_year == "Tüm yıllar":
            return 75

        if self.questions:
            try:
                year = int(selected_year)
                year_count = len([q for q in self.questions if q['yil'] == year])
                if year_count > 0:
                    return year_count
            except Exception:
                pass

        return 75

    def update_question_limit(self, event=None):
        """Secilen yila gore soru limitini gunceller."""
        selected_year = self.year_var.get()
        max_questions = self.get_question_limit_for_year(selected_year)
        self.num_spinbox.config(to=max_questions)

        try:
            current_value = int(self.num_var.get())
        except ValueError:
            current_value = 10

        if current_value > max_questions:
            self.num_var.set(str(max_questions))
        elif current_value < 1:
            self.num_var.set('1')

    def update_stats(self):
        """İstatistikleri günceller"""
        if not self.questions:
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, "Henüz soru yüklenmedi\n\n")
            self.stats_text.config(state=tk.DISABLED)
            return
        
        year_dist = {}
        for q in self.questions:
            year = q['yil']
            year_dist[year] = year_dist.get(year, 0) + 1
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        stats_text = f"📊 TOPLAM SORU: {len(self.questions)}\n\n"
        stats_text += "📅 Yıllara göre dağılım:\n"
        stats_text += "-" * 30 + "\n"
        
        for year in sorted(year_dist.keys()):
            stats_text += f"  {year}: {year_dist[year]} soru\n"
        
        stats_text += "\n" + "=" * 30 + "\n"
        stats_text += f"🎯 Hazır: {len(self.questions)} soru"
        
        self.stats_text.insert(tk.END, stats_text)
        self.stats_text.config(state=tk.DISABLED)
    
    def start_quiz(self):
        """Quiz'i başlatır"""
        if not self.questions:
            messagebox.showwarning("Uyarı", "Önce soruları yükleyin!")
            return
        
        try:
            num_questions = int(self.num_var.get())
            selected_year = self.year_var.get()
            max_questions = self.get_question_limit_for_year(selected_year)
            if num_questions < 1 or num_questions > max_questions:
                messagebox.showwarning("Uyarı", f"Soru sayısı 1-{max_questions} arasında olmalı!")
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
        
        # Select random or sequential questions
        if self.order_var.get() == "Rastgele":
            self.quiz_questions = random.sample(available_questions, num_questions)
        else:
            # Sequential - take first N questions
            self.quiz_questions = available_questions[:num_questions]
        
        # Reset user answers for review mode
        self.user_answers = []
        
        # Clear test history when starting new test
        self.test_history = []
        
        self.current_index = 0
        self.score = 0
        self.total_questions = num_questions
        
        # Start quiz
        self.show_question()
    
    def show_question(self):
        """Soruyu gösterir"""
        if self.current_index >= len(self.quiz_questions):
            # If we're in review mode, show per-question evaluation instead of plain results.
            if self.mode_var.get() == "Test Sonu Değerlendir":
                self.show_review_screen()
            else:
                self.show_results()
            return
        
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        question = self.quiz_questions[self.current_index]
        
        # Question card
        question_card = self.create_card(self.main_content, f"📝 Soru {self.current_index + 1}/{self.total_questions}")
        question_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content_frame = tk.Frame(question_card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Progress bar
        progress_frame = tk.Frame(content_frame, bg=self.colors['card'])
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        progress_text = tk.Label(progress_frame, 
                                text=f"İlerleme: {self.current_index + 1}/{self.total_questions} | Yıl: {question['yil']} | No: {question['soru_no']}", 
                                font=self.fonts['small'], 
                                fg=self.colors['text_secondary'], bg=self.colors['card'])
        progress_text.pack(side=tk.LEFT)
        
        # Progress bar visual
        progress_canvas = tk.Canvas(progress_frame, height=6, bg=self.colors['border'], highlightthickness=0)
        progress_canvas.pack(fill=tk.X, side=tk.RIGHT, padx=(20, 0))
        
        progress = (self.current_index + 1) / self.total_questions
        progress_canvas.create_rectangle(0, 0, 200 * progress, 6, fill=self.colors['success'], outline="")
        
        # Question text
        question_frame = tk.Frame(content_frame, bg=self.colors['primary'], relief=tk.RIDGE, bd=2)
        question_frame.pack(fill=tk.X, pady=(0, 15))
        
        question_text = tk.Text(question_frame, font=self.fonts['body'], 
                               bg=self.colors['primary'], fg=self.colors['text'],
                               wrap=tk.WORD, height=6, relief=tk.FLAT, padx=15, pady=15)
        question_text.pack(fill=tk.X)
        question_text.insert(tk.END, question['soru_metni'])
        question_text.config(state=tk.DISABLED)
        
        # Visual notification if exists
        if question['gorsel_var']:
            visual_frame = tk.Frame(content_frame, bg=self.colors['warning'], relief=tk.RIDGE, bd=2)
            visual_frame.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(visual_frame, text="📸 BU SORUDA GÖRSEL BULUNMAKTADIR!", 
                    font=self.fonts['body'], bg=self.colors['warning'], 
                    fg=self.colors['bg']).pack(pady=5)
            
            for dosya in question['gorsel_dosyalari']:
                try:
                    # Try to load and display the image
                    from PIL import Image, ImageTk
                    import os
                    
                    if os.path.exists(dosya):
                        # Load and resize image
                        img = Image.open(dosya)
                        # Resize image to fit the display area (max width 500, max height 300)
                        img.thumbnail((500, 300), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        # Create image label
                        img_label = tk.Label(visual_frame, image=photo, 
                                           bg=self.colors['warning'])
                        img_label.image = photo  # Keep a reference
                        img_label.pack(pady=10)
                        
                        # Show filename below image
                        tk.Label(visual_frame, text=f"📁 {os.path.basename(dosya)}", 
                                font=self.fonts['small'], bg=self.colors['warning'], 
                                fg=self.colors['bg']).pack(pady=2)
                    else:
                        # File doesn't exist, show error
                        tk.Label(visual_frame, text=f"❌ Görsel bulunamadı: {os.path.basename(dosya)}", 
                                font=self.fonts['small'], bg=self.colors['warning'], 
                                fg='red').pack(pady=2)
                        
                except ImportError:
                    # PIL not available, fall back to text display
                    tk.Label(visual_frame, text=f"📁 {dosya}", 
                            font=self.fonts['small'], bg=self.colors['warning'], 
                            fg=self.colors['bg']).pack(pady=2)
                    tk.Label(visual_frame, text="(Görüntülemek için PIL kütüphanesi gerekli)", 
                            font=self.fonts['small'], bg=self.colors['warning'], 
                            fg='#666').pack(pady=2)
                except Exception as e:
                    # Error loading image
                    tk.Label(visual_frame, text=f"❌ Görsel yüklenemedi: {os.path.basename(dosya)}", 
                            font=self.fonts['small'], bg=self.colors['warning'], 
                            fg='red').pack(pady=2)
        
        # Options
        options_frame = tk.Frame(content_frame, bg=self.colors['card'])
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Get options
        options = list(question['siklar'].items())
        
        # Shuffle options only if random order is selected
        if self.order_var.get() == "Rastgele":
            random.shuffle(options)
        else:
            # Keep original order for sequential mode
            pass
        
        self.option_vars = {}
        self.option_map = {}
        self.option_buttons = {}
        
        for i, (key, value) in enumerate(options, 1):
            self.option_map[str(i)] = key
            
            option_frame = tk.Frame(options_frame, bg=self.colors['card'])
            option_frame.pack(fill=tk.X, pady=8)
            
            # Option button
            var = tk.StringVar()
            self.option_vars[str(i)] = var
            
            option_btn = tk.Button(option_frame, text=f"{i}) {value}", 
                                 font=self.fonts['body'],
                                 bg=self.colors['border'], fg=self.colors['text'],
                                 relief=tk.FLAT, cursor="hand2",
                                 command=lambda v=var, i=str(i): self.select_option(v, i))
            option_btn.pack(fill=tk.X, ipady=8)
            self.option_buttons[str(i)] = option_btn
        
        # Navigation buttons at the top
        nav_frame = tk.Frame(content_frame, bg=self.colors['card'], relief=tk.RIDGE, bd=1)
        nav_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Previous button (only if not first question)
        if self.current_index > 0:
            prev_btn = self.create_button(nav_frame, "←", 
                                         self.previous_question, self.colors['text_secondary'])
            prev_btn.pack(side=tk.LEFT, padx=5, ipady=2)
        
        # Question counter in the middle
        counter_label = tk.Label(nav_frame, text=f"Soru {self.current_index + 1}/{self.total_questions}", 
                                font=('Segoe UI', 9, 'bold'), bg=self.colors['card'], fg=self.colors['text'])
        counter_label.pack(side=tk.LEFT, expand=True)
        
        # Next button (always show)
        if self.current_index < len(self.quiz_questions) - 1:
            next_btn = self.create_button(nav_frame, "→", 
                                         self.next_question, self.colors['success'])
            next_btn.pack(side=tk.RIGHT, padx=5, ipady=2)
        else:
            finish_command = self.show_results
            if self.mode_var.get() == "Test Sonu Değerlendir":
                finish_command = self.show_review_screen
            finish_btn = self.create_button(nav_frame, "🏁", finish_command, self.colors['accent'])
            finish_btn.pack(side=tk.RIGHT, padx=5, ipady=2)
        
        # Restore selection from history if exists
        self.restore_selection_from_history(question)
    
    def select_option(self, var, option_num):
        """Seçenek seçildiğinde - moda göre davranır"""
        # Save selection to history
        question = self.quiz_questions[self.current_index]
        selected_sik = self.option_map[option_num]
        
        # Update or add to history
        self.update_test_history(question, selected_sik)
        
        # Clear all selections and reset colors
        for key, v in self.option_vars.items():
            v.set("")
            self.option_buttons[key].config(bg=self.colors['border'], fg=self.colors['text'])
        
        # Set current selection
        var.set(option_num)
        
        # Check test mode
        if self.mode_var.get() == "Anında Cevap":
            # Instant feedback mode - show result on same screen
            dogru_sik = self.option_map[option_num]
            
            # Color the selected option and show result immediately
            selected_button = self.option_buttons[option_num]
            if dogru_sik == question['dogru_cevap']:
                selected_button.config(bg=self.colors['success'], fg='white')
                self.score += 1
                # Show success message on the same screen
                self.show_feedback_on_screen(question, True)
            else:
                selected_button.config(bg=self.colors['danger'], fg='white')
                # Also highlight the correct answer in green
                for opt_num, sik_key in self.option_map.items():
                    if sik_key == question['dogru_cevap']:
                        self.option_buttons[opt_num].config(bg=self.colors['success'], fg='white')
                        break
                # Show error message on the same screen
                self.show_feedback_on_screen(question, False)
        else:
            # Review mode - just highlight selection, no colors, auto-advance after 2 seconds
            self.option_buttons[option_num].config(bg='white', fg=self.colors['bg'])
            
            # Store the answer for later review
            if not hasattr(self, 'user_answers'):
                self.user_answers = []
            
            self.user_answers.append({
                'question': question,
                'selected_option': selected_sik,  # Store the actual letter (A, B, C, D, E)
                'correct_option': question['dogru_cevap'],
                'is_correct': selected_sik == question['dogru_cevap']
            })
            
            # Auto-advance after 2 seconds
            if self.current_index < len(self.quiz_questions) - 1:
                self.root.after(2000, self.next_question)
            else:
                self.root.after(2000, self.show_review_screen)
    
    def update_test_history(self, question, selected_sik):
        """Test geçmişini günceller"""
        # Find if this question is already in history
        for item in self.test_history:
            if item['question']['yil'] == question['yil'] and item['question']['soru_no'] == question['soru_no']:
                item['selected'] = selected_sik
                return
        
        # Add new question to history
        self.test_history.append({
            'question': question,
            'selected': selected_sik
        })
    
    def restore_selection_from_history(self, question):
        """Geçmişten seçimi geri yükler"""
        for item in self.test_history:
            if item['question']['yil'] == question['yil'] and item['question']['soru_no'] == question['soru_no']:
                # Find the option number for this selection
                for option_num, sik_key in self.option_map.items():
                    if sik_key == item['selected']:
                        # Set the selection
                        self.option_vars[option_num].set(option_num)
                        self.option_buttons[option_num].config(bg='white', fg=self.colors['bg'])
                        break
                return
    
    def show_feedback_on_screen(self, question, is_correct):
        """Aynı ekran üzerinde geri bildirim gösterir"""
        # Find the question card and add feedback to it
        for widget in self.main_content.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_children():
                # This should be our question card
                question_card = widget
                break
        
        # Create feedback frame
        feedback_frame = tk.Frame(question_card, bg=self.colors['card'])
        feedback_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        # Result info
        if is_correct:
            result_color = self.colors['success']
            result_text = "🎉 DOĞRU CEVAP!"
        else:
            result_color = self.colors['danger']
            result_text = "❌ YANLIŞ CEVAP!"
        
        result_info = tk.Frame(feedback_frame, bg=result_color, relief=tk.RIDGE, bd=2)
        result_info.pack(fill=tk.X)
        
        tk.Label(result_info, text=result_text, 
                font=self.fonts['header'], bg=result_color, fg=self.colors['text']).pack(pady=10)
        
        # Explanation
        if question['aciklama']:
            exp_frame = tk.Frame(feedback_frame, bg=self.colors['primary'], relief=tk.RIDGE, bd=2)
            exp_frame.pack(fill=tk.X, pady=(10, 0))
            
            tk.Label(exp_frame, text="📝 AÇIKLAMA:", 
                    font=self.fonts['header'], 
                    bg=self.colors['primary'], fg=self.colors['text']).pack(anchor=tk.W, padx=15, pady=(15, 5))
            
            exp_text = tk.Text(exp_frame, font=self.fonts['body'], 
                              bg=self.colors['primary'], fg=self.colors['text'],
                              wrap=tk.WORD, height=3, relief=tk.FLAT, padx=15, pady=10)
            exp_text.pack(fill=tk.X, padx=10, pady=(0, 15))
            exp_text.insert(tk.END, question['aciklama'])
            exp_text.config(state=tk.DISABLED)
    
    def show_result_screen(self, question, is_correct):
        """Sonuç ekranını gösterir"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # Result card
        if is_correct:
            result_card = self.create_card(self.main_content, "✅ DOĞRU CEVAP!")
            result_color = self.colors['success']
        else:
            result_card = self.create_card(self.main_content, "❌ YANLIŞ CEVAP!")
            result_color = self.colors['danger']
        
        result_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content_frame = tk.Frame(result_card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Result info
        result_info = tk.Frame(content_frame, bg=result_color, relief=tk.RIDGE, bd=2)
        result_info.pack(fill=tk.X, pady=(0, 15))
        
        if is_correct:
            tk.Label(result_info, text="🎉 HARİKA SEÇİM! DOĞRU CEVAP!", 
                    font=self.fonts['header'], bg=result_color, fg=self.colors['text']).pack(pady=15)
        else:
            tk.Label(result_info, text="❌ YANLIŞ CEVAP!", 
                    font=self.fonts['header'], bg=result_color, fg=self.colors['text']).pack(pady=5)
        
        # Explanation
        if question['aciklama']:
            exp_frame = tk.Frame(content_frame, bg=self.colors['primary'], relief=tk.RIDGE, bd=2)
            exp_frame.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(exp_frame, text="📝 AÇIKLAMA:", 
                    font=self.fonts['header'], 
                    bg=self.colors['primary'], fg=self.colors['text']).pack(anchor=tk.W, padx=15, pady=(15, 5))
            
            exp_text = tk.Text(exp_frame, font=self.fonts['body'], 
                              bg=self.colors['primary'], fg=self.colors['text'],
                              wrap=tk.WORD, height=4, relief=tk.FLAT, padx=15, pady=10)
            exp_text.pack(fill=tk.X, padx=10, pady=(0, 15))
            exp_text.insert(tk.END, question['aciklama'])
            exp_text.config(state=tk.DISABLED)
        
        # Navigation buttons
        nav_frame = tk.Frame(content_frame, bg=self.colors['card'])
        nav_frame.pack(fill=tk.X, pady=20)
        
        if self.current_index < len(self.quiz_questions) - 1:
            next_btn = self.create_button(nav_frame, "SONRAKİ SORU →", 
                                         self.next_question, self.colors['success'])
            next_btn.pack(side=tk.RIGHT, ipady=8)
        else:
            finish_btn = self.create_button(nav_frame, "🏁 TESTİ BİTİR", 
                                           self.show_results, self.colors['accent'])
            finish_btn.pack(side=tk.RIGHT, ipady=8)
        
        if self.current_index > 0:
            prev_btn = self.create_button(nav_frame, "← ÖNCEKİ SORU", 
                                         self.previous_question, self.colors['text_secondary'])
            prev_btn.pack(side=tk.LEFT, ipady=8)
    
    def check_answer(self):
        """Cevabı kontrol eder - sadece review mod için"""
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
        
        # Store the answer for later review
        if not hasattr(self, 'user_answers'):
            self.user_answers = []
        
        self.user_answers.append({
            'question': question,
            'selected': selected,
            'correct': dogru_sik,
            'is_correct': dogru_sik == question['dogru_cevap']
        })
        
        # Color the selected option
        selected_button = self.option_buttons[selected]
        if dogru_sik == question['dogru_cevap']:
            selected_button.config(bg=self.colors['success'], fg='white')
            self.score += 1
        else:
            selected_button.config(bg=self.colors['danger'], fg='white')
            # Also highlight the correct answer in green
            for option_num, sik_key in self.option_map.items():
                if sik_key == question['dogru_cevap']:
                    self.option_buttons[option_num].config(bg=self.colors['success'], fg='white')
                    break
        
        # Move to next question
        if self.current_index < len(self.quiz_questions) - 1:
            self.current_index += 1
            self.show_question()
        else:
            # Show review screen
            self.show_review_screen()
    
    def show_review_screen(self):
        """Değerlendirme ekranını gösterir"""
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # Review card
        review_card = self.create_card(self.main_content, "📋 TEST DEĞERLENDİRME")
        review_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content_frame = tk.Frame(review_card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Score summary
        score_frame = tk.Frame(content_frame, bg=self.colors['primary'], relief=tk.RIDGE, bd=2)
        score_frame.pack(fill=tk.X, pady=(0, 15))
        
        # In review mode score may not be incremented live; compute from collected answers.
        if hasattr(self, "user_answers") and self.user_answers:
            self.score = sum(1 for a in self.user_answers if a.get("is_correct"))
        percentage = (self.score / self.total_questions) * 100 if self.total_questions else 0.0
        
        tk.Label(score_frame, text=f"SKOR: {self.score}/{self.total_questions} (%{percentage:.1f})", 
                font=self.fonts['header'], bg=self.colors['primary'], fg=self.colors['text']).pack(pady=15)
        
        # Questions review
        review_text = tk.Text(content_frame, font=self.fonts['body'], 
                              bg=self.colors['card'], fg=self.colors['text'],
                              wrap=tk.WORD, height=15, relief=tk.FLAT, padx=15, pady=15)
        review_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Add review content
        review_content = "SORU DEĞERLENDİRMESİ:\n" + "="*50 + "\n\n"
        
        for i, answer in enumerate(self.user_answers, 1):
            q = answer['question']
            status = "✅ DOĞRU" if answer['is_correct'] else "❌ YANLIŞ"
            
            review_content += f"Soru {i} (Yıl: {q['yil']}, No: {q['soru_no']}) - {status}\n"
            review_content += f"Soru: {q['soru_metni'][:80]}...\n"
            review_content += f"Sizin cevabınız: {q['siklar'].get(answer['selected_option'], 'N/A')}\n"
            review_content += f"Doğru cevap: {q['siklar'].get(answer['correct_option'], 'N/A')}\n"
            
            if not answer['is_correct'] and q['aciklama']:
                review_content += f"Açıklama: {q['aciklama'][:100]}...\n"
            
            review_content += "-"*50 + "\n\n"
        
        review_text.insert(tk.END, review_content)
        review_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg=self.colors['card'])
        button_frame.pack(fill=tk.X, pady=20)
        
        new_test_btn = self.create_button(button_frame, "🔄 YENİ TEST", 
                                         self.new_test, self.colors['success'])
        new_test_btn.pack(side=tk.LEFT, padx=10, ipady=8)
        
        menu_btn = self.create_button(button_frame, "🏠 ANA MENÜ", 
                                     self.show_welcome_screen, self.colors['text_secondary'])
        menu_btn.pack(side=tk.LEFT, padx=10, ipady=8)
    
    def _update_goto_question_list(self, event=None):
        """Seçilen yıla göre mevcut soru numaralarını günceller"""
        try:
            year = int(self.goto_year_var.get())
            nums = sorted(set(q['soru_no'] for q in self.questions if q['yil'] == year))
            values = [str(n) for n in nums] if nums else [str(i) for i in range(1, 76)]
            self.goto_q_combo['values'] = values
            if values:
                self.goto_q_combo.set(values[0])
        except Exception:
            pass

    def open_specific_question(self):
        """Seçilen yıl ve numaradaki soruyu doğrudan görüntüler"""
        if not self.questions:
            messagebox.showwarning("Uyarı", "Önce soruları yükleyin!")
            return
        try:
            year = int(self.goto_year_var.get())
            q_no = int(self.goto_q_var.get())
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir yıl ve soru numarası girin!")
            return

        matches = [q for q in self.questions if q['yil'] == year and q['soru_no'] == q_no]
        if not matches:
            messagebox.showwarning("Uyarı", f"{year} yılı {q_no}. soru bulunamadı!\n"
                                            f"Bu yıla ait yüklü sorular: "
                                            f"{sorted(set(q['soru_no'] for q in self.questions if q['yil'] == year))}")
            return

        self.show_specific_question(matches[0])

    def show_specific_question(self, question):
        """Tek bir soruyu inceleme modunda (cevap + açıklama göster) ekrana basar"""
        for widget in self.main_content.winfo_children():
            widget.destroy()

        card = self.create_card(
            self.main_content,
            f"📖  {question['yil']} – Soru {question['soru_no']}")
        card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollable container
        canvas = tk.Canvas(card, bg=self.colors['card'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(canvas, bg=self.colors['card'])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(win_id, width=e.width)
        inner.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Mouse wheel scroll
        def _on_mousewheel(e):
            try:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        pad = dict(padx=18, pady=8)

        # --- Meta bilgi ---
        meta_frame = tk.Frame(inner, bg=self.colors['primary'], relief=tk.RIDGE, bd=1)
        meta_frame.pack(fill=tk.X, **pad)
        tk.Label(meta_frame,
                 text=f"📅 Yıl: {question['yil']}   |   🔢 Soru No: {question['soru_no']}",
                 font=('Segoe UI', 10, 'bold'),
                 bg=self.colors['primary'], fg=self.colors['text']).pack(pady=8)

        # --- Soru metni ---
        soru_frame = tk.Frame(inner, bg=self.colors['primary'], relief=tk.RIDGE, bd=1)
        soru_frame.pack(fill=tk.X, **pad)
        tk.Label(soru_frame, text="📝 SORU:",
                 font=('Segoe UI', 9, 'bold'),
                 bg=self.colors['primary'], fg=self.colors['warning']).pack(anchor=tk.W, padx=10, pady=(8, 2))
        soru_text = tk.Text(soru_frame, font=('Segoe UI', 10),
                            bg=self.colors['primary'], fg=self.colors['text'],
                            wrap=tk.WORD, height=6, relief=tk.FLAT, padx=10, pady=8)
        soru_text.pack(fill=tk.X, padx=5, pady=(0, 8))
        soru_text.insert(tk.END, question['soru_metni'])
        soru_text.config(state=tk.DISABLED)

        # --- Görseller ---
        if question.get('gorsel_var') and question.get('gorsel_dosyalari'):
            gorsel_frame = tk.Frame(inner, bg=self.colors['warning'], relief=tk.RIDGE, bd=1)
            gorsel_frame.pack(fill=tk.X, **pad)
            tk.Label(gorsel_frame, text="📸 GÖRSELLER:",
                     font=('Segoe UI', 9, 'bold'),
                     bg=self.colors['warning'], fg=self.colors['bg']).pack(anchor=tk.W, padx=10, pady=(8, 2))
            
            for dosya in question['gorsel_dosyalari']:
                try:
                    from PIL import Image, ImageTk
                    import os
                    
                    if os.path.exists(dosya):
                        # Load and resize image
                        img = Image.open(dosya)
                        img.thumbnail((500, 300), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        # Create image label
                        img_label = tk.Label(gorsel_frame, image=photo, 
                                           bg=self.colors['warning'])
                        img_label.image = photo  # Keep a reference
                        img_label.pack(pady=10)
                        
                        # Show filename below image
                        tk.Label(gorsel_frame, text=f"📁 {os.path.basename(dosya)}", 
                                font=('Segoe UI', 8), bg=self.colors['warning'], 
                                fg=self.colors['bg']).pack(pady=2)
                    else:
                        tk.Label(gorsel_frame, text=f"❌ Görsel bulunamadı: {os.path.basename(dosya)}", 
                                font=('Segoe UI', 8), bg=self.colors['warning'], 
                                fg='red').pack(pady=2)
                        
                except ImportError:
                    tk.Label(gorsel_frame, text=f"📁 {dosya}", 
                            font=('Segoe UI', 8), bg=self.colors['warning'], 
                            fg=self.colors['bg']).pack(pady=2)
                    tk.Label(gorsel_frame, text="(Görüntülemek için PIL kütüphanesi gerekli)", 
                            font=('Segoe UI', 8), bg=self.colors['warning'], 
                            fg='#666').pack(pady=2)
                except Exception as e:
                    tk.Label(gorsel_frame, text=f"❌ Görsel yüklenemedi: {os.path.basename(dosya)}", 
                            font=('Segoe UI', 8), bg=self.colors['warning'], 
                            fg='red').pack(pady=2)

        # --- Şıklar ---
        siklar_frame = tk.Frame(inner, bg=self.colors['card'])
        siklar_frame.pack(fill=tk.X, **pad)
        tk.Label(siklar_frame, text="📋 ŞIKLAR:",
                 font=('Segoe UI', 9, 'bold'),
                 bg=self.colors['card'], fg=self.colors['text_secondary']).pack(anchor=tk.W, pady=(0, 4))

        for harf in ('A', 'B', 'C', 'D', 'E'):
            val = question['siklar'].get(harf, '')
            if not val:
                continue
            is_correct = (harf == question['dogru_cevap'])
            bg = self.colors['success'] if is_correct else self.colors['border']
            fg = 'white'
            prefix = "✅" if is_correct else "  "
            sik_btn = tk.Label(siklar_frame,
                               text=f"{prefix} {harf}) {val}",
                               font=('Segoe UI', 10),
                               bg=bg, fg=fg,
                               relief=tk.FLAT, anchor=tk.W, padx=12, pady=6)
            sik_btn.pack(fill=tk.X, pady=2)

        # --- Doğru cevap ---
        dogru_frame = tk.Frame(inner, bg=self.colors['success'], relief=tk.RIDGE, bd=1)
        dogru_frame.pack(fill=tk.X, **pad)
        tk.Label(dogru_frame,
                 text=f"✅ DOĞRU CEVAP:  {question['dogru_cevap']}  —  "
                      f"{question['siklar'].get(question['dogru_cevap'], '')}",
                 font=('Segoe UI', 10, 'bold'),
                 bg=self.colors['success'], fg='white').pack(pady=10, padx=12, anchor=tk.W)

        # --- Açıklama ---
        if question.get('aciklama'):
            acik_frame = tk.Frame(inner, bg=self.colors['primary'], relief=tk.RIDGE, bd=1)
            acik_frame.pack(fill=tk.X, **pad)
            tk.Label(acik_frame, text="💡 AÇIKLAMA:",
                     font=('Segoe UI', 9, 'bold'),
                     bg=self.colors['primary'], fg=self.colors['warning']).pack(anchor=tk.W, padx=10, pady=(8, 2))
            acik_text = tk.Text(acik_frame, font=('Segoe UI', 10),
                                bg=self.colors['primary'], fg=self.colors['text'],
                                wrap=tk.WORD, height=4, relief=tk.FLAT, padx=10, pady=8)
            acik_text.pack(fill=tk.X, padx=5, pady=(0, 8))
            acik_text.insert(tk.END, question['aciklama'])
            acik_text.config(state=tk.DISABLED)

        # --- Komşu soru butonları ---
        year_qs = sorted([q for q in self.questions if q['yil'] == question['yil']],
                         key=lambda q: q['soru_no'])
        idx = next((i for i, q in enumerate(year_qs) if q['soru_no'] == question['soru_no']), None)

        nav_frame = tk.Frame(inner, bg=self.colors['card'])
        nav_frame.pack(fill=tk.X, padx=18, pady=12)

        if idx is not None and idx > 0:
            prev_q = year_qs[idx - 1]
            pb = self.create_button(nav_frame,
                                    f"← Soru {prev_q['soru_no']}",
                                    lambda q=prev_q: self.show_specific_question(q),
                                    self.colors['text_secondary'])
            pb.pack(side=tk.LEFT, ipady=4)

        if idx is not None and idx < len(year_qs) - 1:
            next_q = year_qs[idx + 1]
            nb = self.create_button(nav_frame,
                                    f"Soru {next_q['soru_no']} →",
                                    lambda q=next_q: self.show_specific_question(q),
                                    self.colors['success'])
            nb.pack(side=tk.RIGHT, ipady=4)

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
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        # Results card
        results_card = self.create_card(self.main_content, "🎯 TEST SONUÇLARI")
        results_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content_frame = tk.Frame(results_card, bg=self.colors['card'])
        content_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)
        
        # Score display
        score_frame = tk.Frame(content_frame, bg=self.colors['primary'], relief=tk.RIDGE, bd=3)
        score_frame.pack(pady=20)
        
        score_text = f"{self.score}/{self.total_questions}"
        percentage = (self.score / self.total_questions) * 100 if self.total_questions else 0.0
        
        tk.Label(score_frame, text=score_text, 
                font=('Segoe UI', 48, 'bold'), bg=self.colors['primary'], fg=self.colors['text']).pack(padx=30, pady=20)
        
        tk.Label(score_frame, text=f"Başarı Oranı: %{percentage:.1f}", 
                font=self.fonts['header'], bg=self.colors['primary'], fg=self.colors['text']).pack(pady=(0, 20))
        
        # Message
        if percentage >= 80:
            message = "🎉 MÜKEMMEL! ÇOK BAŞARILI!"
            color = self.colors['success']
        elif percentage >= 60:
            message = "👏 İYİ! BAŞARILI, DEVAM ET!"
            color = self.colors['success']
        elif percentage >= 40:
            message = "📚 ORTA! DAHA FAZLA ÇALIŞMALISIN!"
            color = self.colors['warning']
        else:
            message = "💪 ÇALIŞMAN GEREKİYOR! VAZGEÇME!"
            color = self.colors['danger']
        
        message_frame = tk.Frame(content_frame, bg=color, relief=tk.RIDGE, bd=2)
        message_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(message_frame, text=message, 
                font=self.fonts['header'], bg=color, fg=self.colors['text']).pack(pady=15)
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg=self.colors['card'])
        button_frame.pack(pady=30)
        
        new_test_btn = self.create_button(button_frame, "🔄 YENİ TEST", 
                                          self.new_test, self.colors['success'])
        new_test_btn.pack(side=tk.LEFT, padx=10, ipady=8)
        
        menu_btn = self.create_button(button_frame, "🏠 ANA MENÜ", 
                                     self.show_welcome_screen, self.colors['text_secondary'])
        menu_btn.pack(side=tk.LEFT, padx=10, ipady=8)
    
    def new_test(self):
        """Yeni test başlatır"""
        self.start_quiz()

def main():
    root = tk.Tk()
    app = ModernDKABQuiz(root)
    root.mainloop()

if __name__ == "__main__":
    main()
