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
import time
from typing import Dict, List, Tuple
import threading

class ModernDKABQuiz:
    def __init__(self, root):
        self.root = root
        self.root.title("DKAB OABT Pratik Sinavi")
        self.root.geometry("1000x750")
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
        self.test_history = []
        self.current_view = "welcome"
        self.current_specific_question = None
        self.subjects = []
        self.available_subjects = ["DKAB", "IHL"]
        self._next_timer = None
        self._countdown_job = None
        self._elapsed_job = None
        self.remaining_seconds = 0
        self.test_start_time = None
        self.question_start_time = None
        self.total_elapsed_seconds = 0
        self.question_times = {}
        self.active_mode = None
        self.settings_file = os.path.join(os.path.dirname(__file__), "dkab_quiz_settings.json")
        self.persisted_settings = self.load_persisted_settings()

        self.theme_palettes = {
            "Gece Lacivert": {
                'bg': '#111827',
                'card': '#182235',
                'accent': '#f43f5e',
                'primary': '#1e3a5f',
                'success': '#10b981',
                'warning': '#f59e0b',
                'danger': '#ef4444',
                'text': '#f8fafc',
                'text_secondary': '#cbd5e1',
                'border': '#334155'
            },
            "Zumrut": {
                'bg': '#0b1f1a',
                'card': '#12332b',
                'accent': '#2dd4bf',
                'primary': '#14532d',
                'success': '#22c55e',
                'warning': '#fbbf24',
                'danger': '#f87171',
                'text': '#ecfdf5',
                'text_secondary': '#bbf7d0',
                'border': '#285b52'
            },
            "Gun Batimi": {
                'bg': '#2a1a1f',
                'card': '#3a2530',
                'accent': '#fb7185',
                'primary': '#7c2d12',
                'success': '#34d399',
                'warning': '#f59e0b',
                'danger': '#f87171',
                'text': '#fff7ed',
                'text_secondary': '#fed7aa',
                'border': '#6b3b47'
            },
            "Acik Modern": {
                'bg': '#eef2ff',
                'card': '#ffffff',
                'accent': '#2563eb',
                'primary': '#dbeafe',
                'success': '#16a34a',
                'warning': '#d97706',
                'danger': '#dc2626',
                'text': '#0f172a',
                'text_secondary': '#475569',
                'border': '#cbd5e1'
            }
        }
        self.current_theme = self.persisted_settings.get("theme", "Gece Lacivert")
        self.colors = self.theme_palettes[self.current_theme].copy()
        self.root.configure(bg=self.colors['bg'])

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

    def load_persisted_settings(self):
        """Kaydedilen ayarlari diskten okur."""
        defaults = {
            "theme": "Gece Lacivert",
            "year": "Tüm yıllar",
            "ders": "Tüm dersler",
            "konu": "Tüm konular",
            "mode": "Anında Cevap",
            "time_limit": "10",
            "order": "Rastgele",
            "num": "10",
            "goto_year": "2019",
            "goto_ders": "DKAB",
            "goto_q": "1",
        }
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    defaults.update({k: str(v) for k, v in data.items() if v is not None})
        except Exception:
            pass
        return defaults

    def save_persisted_settings(self):
        """Mevcut ayarlari diske yazar."""
        if not hasattr(self, "theme_var"):
            return

        data = {
            "theme": self.theme_var.get(),
            "year": self.year_var.get(),
            "ders": self.ders_var.get(),
            "konu": self.konu_var.get(),
            "mode": self.mode_var.get(),
            "time_limit": self.time_limit_var.get(),
            "order": self.order_var.get(),
            "num": self.num_var.get(),
            "goto_year": self.goto_year_var.get(),
            "goto_ders": self.goto_ders_var.get(),
            "goto_q": self.goto_q_var.get(),
        }
        self.persisted_settings.update(data)
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.persisted_settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def bind_settings_persistence(self):
        """Ayar degisikliklerini otomatik kaydeder."""
        vars_to_watch = [
            self.theme_var,
            self.year_var,
            self.ders_var,
            self.konu_var,
            self.mode_var,
            self.time_limit_var,
            self.order_var,
            self.num_var,
            self.goto_year_var,
            self.goto_ders_var,
            self.goto_q_var,
        ]
        for var in vars_to_watch:
            var.trace_add("write", lambda *_: self.save_persisted_settings())

    def apply_persisted_settings(self):
        """Kaydedilen ayarlari arayuze uygular."""
        self.theme_var.set(self.persisted_settings.get("theme", self.current_theme))
        self.year_var.set(self.persisted_settings.get("year", "Tüm yıllar"))
        self.ders_var.set(self.persisted_settings.get("ders", "Tüm dersler"))
        self.konu_var.set(self.persisted_settings.get("konu", "Tüm konular"))
        self.mode_var.set(self.persisted_settings.get("mode", "Anında Cevap"))
        self.time_limit_var.set(self.persisted_settings.get("time_limit", "10"))
        self.order_var.set(self.persisted_settings.get("order", "Rastgele"))
        self.num_var.set(self.persisted_settings.get("num", "10"))
        self.goto_year_var.set(self.persisted_settings.get("goto_year", "2019"))
        self.goto_ders_var.set(self.persisted_settings.get("goto_ders", "DKAB"))
        self.goto_q_var.set(self.persisted_settings.get("goto_q", "1"))
        self.on_mode_changed()

    def setup_ttk_styles(self):
        """ttk bilesenlerini aktif temaya gore stillendirir."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        field_bg = self.colors['card'] if self.colors['card'] != '#ffffff' else '#f8fafc'
        style.configure(
            'Modern.TCombobox',
            fieldbackground=field_bg,
            background=self.colors['primary'],
            foreground=self.colors['text'],
            bordercolor=self.colors['border'],
            arrowcolor=self.colors['accent'],
            lightcolor=self.colors['border'],
            darkcolor=self.colors['border'],
            insertcolor=self.colors['text']
        )
        style.map(
            'Modern.TCombobox',
            fieldbackground=[('readonly', field_bg)],
            foreground=[('readonly', self.colors['text'])],
            selectbackground=[('readonly', self.colors['primary'])],
            selectforeground=[('readonly', self.colors['text'])]
        )
        style.configure(
            'Modern.Vertical.TScrollbar',
            background=self.colors['primary'],
            troughcolor=self.colors['bg'],
            bordercolor=self.colors['bg'],
            arrowcolor=self.colors['text'],
            darkcolor=self.colors['primary'],
            lightcolor=self.colors['primary']
        )

    def setup_ui(self):
        """Modern arayuzu kurar."""
        self.root.configure(bg=self.colors['bg'])
        self.setup_ttk_styles()

        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)

        self.create_header(main_container)

        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.create_sidebar(content_frame)
        self.create_main_content(content_frame)
        self.apply_persisted_settings()
        self.bind_settings_persistence()
        self.update_question_limit()
        self._update_goto_question_list()
        self.show_welcome_screen()

    def rebuild_ui(self):
        """Tema degisimi sonrasi arayuzu koruyarak yeniden kurar."""
        saved = {
            'year': getattr(self, 'year_var', None).get() if hasattr(self, 'year_var') else 'Tum yillar',
            'mode': getattr(self, 'mode_var', None).get() if hasattr(self, 'mode_var') else 'Aninda Cevap',
            'time_limit': getattr(self, 'time_limit_var', None).get() if hasattr(self, 'time_limit_var') else '10',
            'order': getattr(self, 'order_var', None).get() if hasattr(self, 'order_var') else 'Rastgele',
            'num': getattr(self, 'num_var', None).get() if hasattr(self, 'num_var') else '10',
            'ders': getattr(self, 'ders_var', None).get() if hasattr(self, 'ders_var') else 'Tüm dersler',
            'konu': getattr(self, 'konu_var', None).get() if hasattr(self, 'konu_var') else 'Tüm konular',
            'goto_year': getattr(self, 'goto_year_var', None).get() if hasattr(self, 'goto_year_var') else '2019',
            'goto_ders': getattr(self, 'goto_ders_var', None).get() if hasattr(self, 'goto_ders_var') else 'DKAB',
            'goto_q': getattr(self, 'goto_q_var', None).get() if hasattr(self, 'goto_q_var') else '1',
        }

        for widget in self.root.winfo_children():
            widget.destroy()

        self.setup_ui()

        self.year_var.set(saved['year'])
        self.ders_var.set(saved['ders'])
        self.konu_var.set(saved['konu'])
        self.mode_var.set(saved['mode'])
        self.time_limit_var.set(saved['time_limit'])
        self.order_var.set(saved['order'])
        self.num_var.set(saved['num'])
        self.goto_year_var.set(saved['goto_year'])
        self.goto_ders_var.set(saved['goto_ders'])
        self.goto_q_var.set(saved['goto_q'])
        self.on_mode_changed()
        self.update_question_limit()
        self._update_goto_question_list()

        if self.questions:
            self.update_stats()
            self.load_button.config(text=f'Yuklendi: {len(self.questions)} soru', bg=self.colors['success'])
            self.status_label.config(text='Hazir', fg=self.colors['success'])

        if self.current_view == 'question' and self.quiz_questions:
            self.show_question()
        elif self.current_view == 'review' and hasattr(self, 'user_answers'):
            self.show_review_screen()
        elif self.current_view == 'results' and self.total_questions:
            self.show_results()
        elif self.current_view == 'specific' and self.current_specific_question:
            self.show_specific_question(self.current_specific_question)
        else:
            self.show_welcome_screen()

    def change_theme(self, event=None):
        """Secilen temayi uygular."""
        selected = self.theme_var.get()
        if selected in self.theme_palettes:
            self.current_theme = selected
            self.colors = self.theme_palettes[selected].copy()
            self.rebuild_ui()

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
        """Sol sidebar oluşturur (Kaydırılabilir)"""
        sidebar_outer = tk.Frame(parent, bg=self.colors['card'], width=260)
        sidebar_outer.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        sidebar_outer.pack_propagate(False)
        
        self.sidebar_canvas = tk.Canvas(sidebar_outer, bg=self.colors['card'], highlightthickness=0, width=240)
        self.sidebar_scrollbar = ttk.Scrollbar(sidebar_outer, orient="vertical", command=self.sidebar_canvas.yview, style="Modern.Vertical.TScrollbar")
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)
        
        self.sidebar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sidebar = tk.Frame(self.sidebar_canvas, bg=self.colors['card'])
        self.sidebar_canvas_window = self.sidebar_canvas.create_window((0, 0), window=sidebar, anchor="nw")
        
        sidebar.bind("<Configure>", lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all")))
        self.sidebar_canvas.bind("<Configure>", lambda e: self.sidebar_canvas.itemconfig(self.sidebar_canvas_window, width=e.width))

        def _on_sidebar_mousewheel(event):
            try:
                # Windows delta is 120, Linux may vary, but we use a common approach
                delta = event.delta if hasattr(event, 'delta') else 0
                if delta == 0 and hasattr(event, 'num'): # Linux support
                    if event.num == 4: delta = 120
                    elif event.num == 5: delta = -120
                self.sidebar_canvas.yview_scroll(int(-1*(delta/120)), "units")
            except Exception:
                pass

        # Sidebar'a mouse girince mousewheel'i ona bağla
        sidebar.bind("<Enter>", lambda e: self.root.bind_all("<MouseWheel>", _on_sidebar_mousewheel))
        sidebar.bind("<Leave>", lambda e: self.root.unbind_all("<MouseWheel>"))
        self.sidebar_canvas.bind("<Enter>", lambda e: self.root.bind_all("<MouseWheel>", _on_sidebar_mousewheel))
        self.sidebar_canvas.bind("<Leave>", lambda e: self.root.unbind_all("<MouseWheel>"))
        
        # Settings card
        settings_card = self.create_card(sidebar, "⚙️ Ayarlar")
        settings_card.pack(fill=tk.X, padx=2, pady=2)

        tk.Label(settings_card, text="Tema:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.theme_var = tk.StringVar(value=self.current_theme)
        self.theme_combo = ttk.Combobox(settings_card, textvariable=self.theme_var,
                                        values=list(self.theme_palettes.keys()), state="readonly",
                                        width=14, style='Modern.TCombobox')
        self.theme_combo.pack(padx=5, pady=(0, 2), fill=tk.X)
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        # Year selection
        tk.Label(settings_card, text="Yıl:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.year_var = tk.StringVar(value="Tüm yıllar")
        years = ["Tüm yıllar"] + [str(year) for year in range(2013, 2026)]
        self.year_combo = ttk.Combobox(settings_card, textvariable=self.year_var, 
                                       values=years, state="readonly", width=14, style='Modern.TCombobox')
        self.year_combo.pack(padx=5, pady=0, fill=tk.X)
        self.year_combo.bind("<<ComboboxSelected>>", self.on_ders_changed)

        # Subject selection
        tk.Label(settings_card, text="Ders:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.ders_var = tk.StringVar(value="Tüm dersler")
        self.ders_combo = ttk.Combobox(settings_card, textvariable=self.ders_var,
                                       values=["Tüm dersler"] + self.available_subjects, state="readonly", width=14, style='Modern.TCombobox')
        self.ders_combo.pack(padx=5, pady=0, fill=tk.X)
        self.ders_combo.bind("<<ComboboxSelected>>", self.on_ders_changed)

        # Konu selection
        tk.Label(settings_card, text="Konu:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.konu_var = tk.StringVar(value="Tüm konular")
        self.konu_combo = ttk.Combobox(settings_card, textvariable=self.konu_var,
                                       values=["Tüm konular"], state="readonly", width=14, style='Modern.TCombobox')
        self.konu_combo.pack(padx=5, pady=0, fill=tk.X)
        self.konu_combo.bind("<<ComboboxSelected>>", self.update_question_limit)
        
        # Test mode selection
        tk.Label(settings_card, text="Mod:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.mode_var = tk.StringVar(value="Anında Cevap")
        mode_options = ["Anında Cevap", "Test Sonu Değerlendir", "Süreli"]
        self.mode_combo = ttk.Combobox(settings_card, textvariable=self.mode_var, 
                                      values=mode_options, state="readonly", width=14, style='Modern.TCombobox')
        self.mode_combo.pack(padx=5, pady=0, fill=tk.X)
        self.mode_combo.bind("<<ComboboxSelected>>", self.on_mode_changed)

        tk.Label(settings_card, text="Süre (dk):", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.time_limit_var = tk.StringVar(value="10")
        self.time_spinbox = tk.Spinbox(settings_card, from_=1, to=180, textvariable=self.time_limit_var,
                                       width=5, font=('Segoe UI', 8))
        self.time_spinbox.pack(padx=5, pady=0, anchor=tk.W)

        # Question order selection
        tk.Label(settings_card, text="Sıra:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.order_var = tk.StringVar(value="Rastgele")
        order_options = ["Rastgele", "Sıralı"]
        self.order_combo = ttk.Combobox(settings_card, textvariable=self.order_var, 
                                       values=order_options, state="readonly", width=14, style='Modern.TCombobox')
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
        
        self.max_btn = tk.Button(num_frame, text="MAX", font=('Segoe UI', 7, 'bold'),
                                bg=self.colors.get('accent', '#3498db'), fg='white',
                                relief=tk.FLAT, cursor="hand2",
                                command=lambda: self.num_var.set(str(int(float(self.num_spinbox.cget('to'))))))
        self.max_btn.pack(side=tk.LEFT, padx=(5, 0))
        
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
                                            values=goto_years, state="readonly", width=14, style='Modern.TCombobox')
        self.goto_year_combo.pack(padx=5, pady=0, fill=tk.X)
        self.goto_year_combo.bind("<<ComboboxSelected>>", self._update_goto_question_list)

        tk.Label(goto_card, text="Ders:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.goto_ders_var = tk.StringVar(value="DKAB")
        self.goto_ders_combo = ttk.Combobox(goto_card, textvariable=self.goto_ders_var,
                                            values=self.available_subjects, state="readonly", width=14, style='Modern.TCombobox')
        self.goto_ders_combo.pack(padx=5, pady=0, fill=tk.X)
        self.goto_ders_combo.bind("<<ComboboxSelected>>", self._update_goto_question_list)

        tk.Label(goto_card, text="Soru No:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.goto_q_var = tk.StringVar(value="1")
        self.goto_q_combo = ttk.Combobox(goto_card, textvariable=self.goto_q_var,
                                         values=[str(i) for i in range(1, 76)],
                                         state="normal", width=14, style='Modern.TCombobox')
        self.goto_q_combo.pack(padx=5, pady=0, fill=tk.X)

        self.goto_btn = self.create_button(goto_card, "🔎 SORUYU AÇ",
                                           self.open_specific_question, self.colors['accent'])
        self.goto_btn.pack(padx=5, pady=5, fill=tk.X, ipady=2)
        
        # --- Analiz Kartı ---
        analiz_card = self.create_card(sidebar, "📈 Analiz")
        analiz_card.pack(fill=tk.X, padx=2, pady=2)
        
        tk.Label(analiz_card, text="Yıl/Konu Dağılımı:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.analiz_combo = ttk.Combobox(analiz_card, values=["Özet", "Detaylı", "Benzer Sorular"],
                                          state="readonly", width=14, style='Modern.TCombobox')
        self.analiz_combo.pack(padx=5, pady=2, fill=tk.X)
        self.analiz_combo.set("Özet")
        
        analiz_btn = self.create_button(analiz_card, "📊 ANALİZİ GÖSTER",
                                        self.show_analysis, self.colors['primary'])
        analiz_btn.pack(padx=5, pady=2, fill=tk.X, ipady=2)
        
        self.yeni_dosya_label = tk.Label(analiz_card, text="", font=('Segoe UI', 7),
                                        fg=self.colors['warning'], bg=self.colors['card'],
                                        wraplength=180)
        self.yeni_dosya_label.pack(padx=5, pady=2, fill=tk.X)

        self.on_mode_changed()
        
    def create_main_content(self, parent):
        """Ana içerik alanı oluşturur (Kaydırılabilir)"""
        self.main_container = tk.Frame(parent, bg=self.colors['card'])
        self.main_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.main_container, bg=self.colors['card'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview, style="Modern.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.main_content = tk.Frame(self.canvas, bg=self.colors['card'])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.main_content, anchor="nw")
        
        self.main_content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        def _on_main_mousewheel(event):
            try:
                delta = event.delta if hasattr(event, 'delta') else 0
                if delta == 0 and hasattr(event, 'num'):
                    if event.num == 4: delta = 120
                    elif event.num == 5: delta = -120
                self.canvas.yview_scroll(int(-1*(delta/120)), "units")
            except Exception:
                pass
                
        # İçerik alanına mouse girince mousewheel'i ona bağla
        self.main_content.bind("<Enter>", lambda e: self.root.bind_all("<MouseWheel>", _on_main_mousewheel))
        self.main_content.bind("<Leave>", lambda e: self.root.unbind_all("<MouseWheel>"))
        self.canvas.bind("<Enter>", lambda e: self.root.bind_all("<MouseWheel>", _on_main_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.root.unbind_all("<MouseWheel>"))
        
    def _quiz_mode(self):
        """Başlatılan testin modunu döndürür."""
        return getattr(self, "active_mode", None) or self.mode_var.get()

    def _uses_review_flow(self):
        """Soruları sonradan değerlendiren modları belirtir."""
        return self._quiz_mode() in ("Test Sonu Değerlendir", "Süreli")

    def _is_timed_quiz(self):
        """Geri sayım kullanan modu belirtir."""
        return self._quiz_mode() == "Süreli"

    def _question_key(self, question):
        """Soruyu benzersiz şekilde anahtarlar."""
        return (question.get('yil'), question.get('ders'), question.get('soru_no'))

    def _start_elapsed_tracking(self):
        """Test ve soru sürelerini canlı izlemeyi başlatır."""
        self.test_start_time = time.monotonic()
        self.question_start_time = self.test_start_time
        self.total_elapsed_seconds = 0
        self.question_times = {}
        self._stop_elapsed_tracking()
        self._elapsed_job = self.root.after(1000, self._tick_elapsed)

    def _stop_elapsed_tracking(self):
        """Canlı süre takibini durdurur."""
        if self._elapsed_job:
            try:
                self.root.after_cancel(self._elapsed_job)
            except Exception:
                pass
            self._elapsed_job = None

    def _store_current_question_time(self):
        """Mevcut soruda harcanan süreyi birikimli olarak kaydeder."""
        if self.question_start_time is None or not self.quiz_questions:
            return

        question = self.quiz_questions[self.current_index]
        elapsed = max(0, int(time.monotonic() - self.question_start_time))
        key = self._question_key(question)
        self.question_times[key] = self.question_times.get(key, 0) + elapsed
        self.question_start_time = time.monotonic()

    def _tick_elapsed(self):
        """Test ekranındaki canlı süre gösterimini günceller."""
        self._elapsed_job = None
        if self.current_view != "question" or self.question_start_time is None:
            return

        current_elapsed = max(0, int(time.monotonic() - self.question_start_time))
        self.total_elapsed_seconds = max(0, int(time.monotonic() - self.test_start_time)) if self.test_start_time else 0

        if hasattr(self, "elapsed_text_var") and self.elapsed_text_var is not None:
            self.elapsed_text_var.set(f"Geçen Süre: {self._format_seconds(self.total_elapsed_seconds)}")
        if hasattr(self, "question_elapsed_text_var") and self.question_elapsed_text_var is not None:
            self.question_elapsed_text_var.set(f"Bu Soru: {self._format_seconds(current_elapsed)}")

        self._elapsed_job = self.root.after(1000, self._tick_elapsed)

    def _stop_countdown(self):
        """Aktif geri sayımı ve otomatik ilerlemeyi durdurur."""
        if self._countdown_job:
            try:
                self.root.after_cancel(self._countdown_job)
            except Exception:
                pass
            self._countdown_job = None
        if self._next_timer:
            try:
                self.root.after_cancel(self._next_timer)
            except Exception:
                pass
            self._next_timer = None

    def _set_status_ready(self):
        """Başlangıç durum yazısını geri getirir."""
        if hasattr(self, "status_label"):
            self.status_label.config(text="🟢 Hazır", fg=self.colors['success'])

    def _format_seconds(self, seconds):
        """Saniyeyi MM:SS formatına çevirir."""
        seconds = max(0, int(seconds))
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02d}:{secs:02d}"

    def _refresh_timer_labels(self):
        """Ekrandaki süre göstergelerini günceller."""
        if hasattr(self, "timer_text_var") and self.timer_text_var is not None:
            self.timer_text_var.set(f"Kalan Süre: {self._format_seconds(self.remaining_seconds)}")

        if hasattr(self, "status_label"):
            if self._is_timed_quiz():
                if self.remaining_seconds > 0:
                    self.status_label.config(text=f"⏳ {self._format_seconds(self.remaining_seconds)}", fg=self.colors['warning'])
                else:
                    self.status_label.config(text="⏰ Süre doldu", fg=self.colors['danger'])
            else:
                self._set_status_ready()

    def _start_countdown(self, minutes):
        """Süreli test için geri sayımı başlatır."""
        self._stop_countdown()
        self.remaining_seconds = max(0, int(minutes) * 60)
        if self.remaining_seconds <= 0:
            self._finish_timed_quiz()
            return
        self._refresh_timer_labels()
        self._countdown_job = self.root.after(1000, self._tick_countdown)

    def _tick_countdown(self):
        """Her saniye çalışan geri sayım döngüsü."""
        self._countdown_job = None
        if not self._is_timed_quiz():
            return

        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.remaining_seconds = 0
            self._refresh_timer_labels()
            self._finish_timed_quiz()
            return

        self._refresh_timer_labels()
        self._countdown_job = self.root.after(1000, self._tick_countdown)

    def _finish_timed_quiz(self):
        """Süre bittiğinde testi sonlandırır."""
        self._stop_countdown()
        self.remaining_seconds = 0
        self._refresh_timer_labels()
        if self.quiz_questions:
            self.show_results()

    def on_mode_changed(self, event=None):
        """Mod değiştiğinde süre alanını etkinleştirir veya devre dışı bırakır."""
        if not hasattr(self, "time_spinbox"):
            return

        if self.mode_var.get() == "Süreli":
            self.time_spinbox.config(state="normal")
        else:
            self.time_spinbox.config(state="disabled")
        self._set_status_ready()

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
        self.current_view = "welcome"
        """Hoş geldin ekranını gösterir"""
        self._stop_countdown()
        self._stop_elapsed_tracking()
        self.remaining_seconds = 0
        self._set_status_ready()
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
        
    def check_new_files(self):
        """Yeni eklenen dosyaları kontrol eder"""
        import re
        import json
        from datetime import datetime
        
        base_path = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir"
        last_check_file = os.path.join(os.path.dirname(__file__), "last_check.json")
        
        try:
            if os.path.exists(last_check_file):
                with open(last_check_file, 'r', encoding='utf-8') as f:
                    last_check = json.load(f)
            else:
                last_check = {"files": {}, "last_run": ""}
        except:
            last_check = {"files": {}, "last_run": ""}
        
        current_files = {}
        new_files = []
        
        if os.path.exists(base_path):
            for filename in os.listdir(base_path):
                match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
                if match:
                    file_path = os.path.join(base_path, filename)
                    mod_time = os.path.getmtime(file_path)
                    current_files[filename] = mod_time
                    
                    if filename not in last_check.get("files", {}):
                        new_files.append(filename)
                    elif last_check["files"].get(filename, 0) != mod_time:
                        new_files.append(f"{filename} (güncellendi)")
        
        last_check["files"] = current_files
        last_check["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(last_check_file, 'w', encoding='utf-8') as f:
                json.dump(last_check, f, ensure_ascii=False, indent=2)
        except:
            pass
        
        return new_files
        
    def show_analysis(self):
        """Analiz ekranını gösterir"""
        self.current_view = "analysis"
        import re
        from collections import defaultdict
        
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        new_files = self.check_new_files()
        if new_files and hasattr(self, 'yeni_dosya_label'):
            self.yeni_dosya_label.config(text=f"🔔 Yeni: {', '.join(new_files[:2])}")
        
        analiz_card = self.create_card(self.main_content, "📈 SORU ANALİZİ")
        analiz_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content_frame = tk.Frame(analiz_card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        base_path = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir"
        years_data = defaultdict(lambda: defaultdict(int))
        konu_data = defaultdict(lambda: defaultdict(int))
        total_questions = 0
        all_parsed_questions = []
        
        if os.path.exists(base_path):
            for filename in os.listdir(base_path):
                match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
                if match:
                    year = int(match.group(1))
                    subject = match.group(2)
                    questions = self.parse_questions_from_file(os.path.join(base_path, filename), year, subject)
                    all_parsed_questions.extend(questions)
                    total_questions += len(questions)
                    for q in questions:
                        years_data[q['yil']][q['ders']] += 1
                        konu_data[q['konu']][q['ders']] += 1
        
        header_frame = tk.Frame(content_frame, bg=self.colors['primary'], relief=tk.RIDGE, bd=2)
        header_frame.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(header_frame, text=f"📊 Toplam: {total_questions} Soru",
                font=('Segoe UI', 12, 'bold'), bg=self.colors['primary'], fg=self.colors['text']).pack(pady=5)
        
        if new_files:
            tk.Label(header_frame, text=f"🔔 Yeni dosya: {', '.join(new_files[:2])}",
                    font=('Segoe UI', 9), bg=self.colors['warning'], fg=self.colors['bg']).pack(pady=3)
        
        tk.Label(content_frame, text="📅 YILLARA GÖRE DAĞILIM",
                font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(pady=(15, 5))
        
        table_frame = tk.Frame(content_frame, bg=self.colors['border'])
        table_frame.pack(padx=15, fill=tk.X)
        
        headers = ["Yıl", "DKAB", "IHL", "Toplam"]
        for i, h in enumerate(headers):
            tk.Label(table_frame, text=h, font=('Segoe UI', 11, 'bold'),
                    bg=self.colors['primary'], fg=self.colors['text'], width=16).grid(row=0, column=i, padx=1, pady=1)
        
        sorted_years = sorted(years_data.keys(), reverse=True)
        for row_idx, year in enumerate(sorted_years, 1):
            dkab = years_data[year]["DKAB"]
            ihl = years_data[year]["IHL"]
            bg = self.colors['card'] if row_idx % 2 == 0 else self.colors['primary']
            for col_idx, val in enumerate([str(year), str(dkab), str(ihl), str(dkab+ihl)]):
                tk.Label(table_frame, text=val, font=('Segoe UI', 11),
                        bg=bg, fg=self.colors['text'], width=16).grid(row=row_idx, column=col_idx, padx=1, pady=1)
        
        tk.Label(content_frame, text="📚 KONULARA GÖRE DAĞILIM",
                font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(pady=(20, 5))
        
        konu_table = tk.Frame(content_frame, bg=self.colors['border'])
        konu_table.pack(padx=15, fill=tk.X)
        
        konu_headers = ["Konu", "DKAB", "IHL", "Toplam"]
        for i, h in enumerate(konu_headers):
            tk.Label(konu_table, text=h, font=('Segoe UI', 11, 'bold'),
                    bg=self.colors['primary'], fg=self.colors['text'], width=24).grid(row=0, column=i, padx=1, pady=1)
        
        konu_totals = {}
        for konu in konu_data:
            dkab = konu_data[konu]["DKAB"]
            ihl = konu_data[konu]["IHL"]
            konu_totals[konu] = dkab + ihl
        
        sorted_konular = sorted(konu_totals.items(), key=lambda x: x[1], reverse=True)
        
        for row_idx, (konu, total) in enumerate(sorted_konular, 1):
            dkab = konu_data[konu]["DKAB"]
            ihl = konu_data[konu]["IHL"]
            bg = self.colors['card'] if row_idx % 2 == 0 else self.colors['primary']
            for col_idx, val in enumerate([konu[:24], str(dkab), str(ihl), str(total)]):
                tk.Label(konu_table, text=val, font=('Segoe UI', 10),
                        bg=bg, fg=self.colors['text'], width=24).grid(row=row_idx, column=col_idx, padx=1, pady=1)
        
        # Bilinmeyen konular listesi
        unknown_questions = [(q['yil'], q['ders'], q['soru_no']) for q in all_parsed_questions if q.get('konu') in ['BİLİNMEYEN KONU', '', None] or not q.get('konu')]
        if unknown_questions:
            tk.Label(content_frame, text="⚠️ BİLİNMEYEN KONU SORULARI",
                    font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['danger']).pack(pady=(20, 5))
            
            unknown_frame = tk.Frame(content_frame, bg=self.colors['danger'])
            unknown_frame.pack(padx=15, fill=tk.X)
            
            unknown_text = "Bu soruların KONU etiketi bulunamadı:\n"
            for yil, ders, no in unknown_questions:
                unknown_text += f"  • {yil} {ders} - Soru {no}\n"
            
            unknown_label = tk.Label(unknown_frame, text=unknown_text.strip(),
                    font=('Segoe UI', 9), bg=self.colors['danger'], fg='white', justify=tk.LEFT)
            unknown_label.pack(padx=10, pady=10)
        
        if hasattr(self, 'analiz_combo') and self.analiz_combo.get() == "Detaylı":
            # 3. Tablo: YIL x DERS x KONU matris
            tk.Label(content_frame, text="📊 YIL × DERS × KONU DAĞILIMI",
                    font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(pady=(20, 5))
            
            yil_ders_konu_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
            for q in all_parsed_questions:
                if q.get('konu') and q.get('konu') not in ['BİLİNMEYEN KONU', '']:
                    yil_ders_konu_data[q['yil']][q['ders']][q['konu']] += 1
            
            matris_inner = tk.Frame(content_frame, bg=self.colors['card'])
            matris_inner.pack(fill=tk.X, padx=15, pady=5)
            
            sorted_years = sorted(yil_ders_konu_data.keys(), reverse=True)
            sorted_konular_list = sorted(set(k for y in sorted_years for d in yil_ders_konu_data[y].keys() for k in yil_ders_konu_data[y][d].keys()))
            
            all_ders = set()
            for y in sorted_years:
                for d in yil_ders_konu_data[y].keys():
                    all_ders.add(d)
            all_ders = sorted(all_ders)
            
            for row_idx, year in enumerate(sorted_years):
                row_bg = self.colors['primary'] if row_idx % 2 == 0 else self.colors['card']
                
                for col_idx, ders in enumerate(all_ders):
                    col_bg = self.colors['success'] if col_idx % 2 == 0 else self.colors['primary']
                    
                    header_frame = tk.Frame(matris_inner, bg=col_bg, relief=tk.RIDGE, bd=1)
                    header_frame.grid(row=row_idx, column=col_idx, padx=2, pady=4, sticky="nw")
                    
                    tk.Label(header_frame, text=f"{year} {ders}",
                            font=('Segoe UI', 10, 'bold'), bg=col_bg, fg='white').pack(pady=4)
                    
                    konu_count_frame = tk.Frame(header_frame, bg=self.colors['card'])
                    konu_count_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
                    
                    bg_cycle = [self.colors['card'], self.colors['border']]
                    added_topics = 0
                    for konu in sorted_konular_list:
                        count = yil_ders_konu_data[year][ders].get(konu, 0)
                        if count > 0:
                            konu_bg = bg_cycle[added_topics % 2]
                            tk.Label(konu_count_frame, text=f"{konu[:24]}: {count}",
                                    font=('Segoe UI', 9), bg=konu_bg, fg=self.colors['text'], width=22).pack(fill=tk.X)
                            added_topics += 1
                            
        elif hasattr(self, 'analiz_combo') and self.analiz_combo.get() == "Benzer Sorular":
            tk.Label(content_frame, text="🔍 BENZER SORULAR AĞI (Eşleşme > %55)",
                    font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(pady=(20, 5))
            
            q_words = []
            for q in all_parsed_questions:
                text = re.sub(r'[^\w\s]', '', (q.get('soru_metni', '') + ' ' + str(q.get('siklar', {}))).lower())
                q_words.append(set(text.split()))

            similar_pairs = []
            n_q = len(all_parsed_questions)
            for i in range(n_q):
                for j in range(i+1, n_q):
                    w1, w2 = q_words[i], q_words[j]
                    if not w1 or not w2: continue
                    inter = len(w1.intersection(w2))
                    union = len(w1.union(w2))
                    sim = inter / union if union else 0
                    if sim > 0.55:
                        similar_pairs.append((sim, all_parsed_questions[i], all_parsed_questions[j]))
            
            similar_pairs.sort(key=lambda x: x[0], reverse=True)
            
            sim_frame = tk.Frame(content_frame, bg=self.colors['border'])
            sim_frame.pack(padx=15, fill=tk.X, pady=5)
            
            if not similar_pairs:
                tk.Label(sim_frame, text="Hiç benzer soru bulunamadı.", font=('Segoe UI', 10),
                         bg=self.colors['card'], fg=self.colors['text']).pack(padx=1, pady=1, fill=tk.X)
            else:
                seen = set()
                count = 0
                for sim, q1, q2 in similar_pairs:
                    pair_id = tuple(sorted([f"{q1['yil']}{q1['ders']}{q1['soru_no']}", f"{q2['yil']}{q2['ders']}{q2['soru_no']}"]))
                    if pair_id in seen: continue
                    seen.add(pair_id)
                    
                    bg_color = self.colors['card'] if count % 2 == 0 else self.colors['primary']
                    
                    row_f = tk.Frame(sim_frame, bg=bg_color)
                    row_f.pack(fill=tk.X, padx=1, pady=1)
                    
                    btn_text = f"🎯 %{int(sim*100)} EŞLEŞME: {q1['yil']} {q1['ders']} (Soru {q1.get('soru_no','?')}) ↔ {q2['yil']} {q2['ders']} (Soru {q2.get('soru_no','?')})"
                    tk.Label(row_f, text=btn_text, font=('Segoe UI', 10, 'bold'), bg=bg_color, fg=self.colors['text']).pack(anchor="w", padx=10, pady=(5, 2))
                    
                    t1 = q1.get('soru_metni', '').replace('\n', ' ')
                    t2 = q2.get('soru_metni', '').replace('\n', ' ')
                    tk.Label(row_f, text=f"• Soru A: {t1[:100]}...", font=('Segoe UI', 8), bg=bg_color, fg=self.colors['text'], justify="left").pack(anchor="w", padx=20, pady=1)
                    tk.Label(row_f, text=f"• Soru B: {t2[:100]}...", font=('Segoe UI', 8), bg=bg_color, fg=self.colors['text'], justify="left").pack(anchor="w", padx=20, pady=(1, 5))
                    
                    count += 1
                    if count >= 30:
                        break
        
        back_btn = self.create_button(content_frame, "🔙 GERİ",
                                      self.show_welcome_screen, self.colors['text_secondary'])
        back_btn.pack(pady=20, ipady=5)
        
    def load_questions(self):
        """Soruları yükler"""
        def load_in_background():
            try:
                import re
                base_path = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir"
                loaded_questions = []
                unique_subjects = set()
                found_years = set()
                
                if os.path.exists(base_path):
                    for filename in os.listdir(base_path):
                        match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
                        if match:
                            year = int(match.group(1))
                            subject = match.group(2)
                            file_path = os.path.join(base_path, filename)
                            year_questions = self.parse_questions_from_file(file_path, year, subject)
                            loaded_questions.extend(year_questions)
                            found_years.add(str(year))
                            unique_subjects.add(subject)
                            print(f"{year} {subject} sınavından {len(year_questions)} soru yüklendi")
                
                self.questions = loaded_questions
                self.subjects = sorted(list(unique_subjects))
                self.available_subjects = [subject for subject in ["DKAB", "IHL"] if subject in unique_subjects] or ["DKAB", "IHL"]
                
                # Update UI elements
                years_list = ["Tüm yıllar"] + sorted(list(found_years), reverse=True)
                ders_list = self.available_subjects
                
                self.root.after(0, lambda: self.update_dropdown_values(years_list, ders_list))
                self.root.after(0, self.update_stats)
                self.root.after(0, self.update_question_limit)
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
        
    def update_dropdown_values(self, years, dersler):
        """Dropdown değerlerini günceller."""
        current_year = self.year_var.get()
        current_ders = self.ders_var.get()
        current_goto_year = self.goto_year_var.get()
        current_goto_ders = self.goto_ders_var.get()

        keys_with_all = ["Tüm dersler"] + dersler
        self.year_combo['values'] = years
        self.ders_combo['values'] = keys_with_all
        self.goto_year_combo['values'] = sorted([y for y in years if y != "Tüm yıllar"], reverse=True)
        self.goto_ders_combo['values'] = dersler

        if current_year in years:
            self.year_var.set(current_year)
        elif years:
            self.year_var.set(years[0])

        if current_ders not in keys_with_all and keys_with_all:
            self.ders_var.set(keys_with_all[0])
        else:
            self.ders_var.set(current_ders)

        goto_years = list(self.goto_year_combo['values'])
        if current_goto_year in goto_years:
            self.goto_year_var.set(current_goto_year)
        elif goto_years:
            self.goto_year_var.set(goto_years[0])

        if current_goto_ders not in dersler and dersler:
            self.goto_ders_var.set(dersler[0])
        else:
            self.goto_ders_var.set(current_goto_ders)

        self.update_question_limit()
        self._update_goto_question_list()
        self._update_konu_list()

    def on_ders_changed(self, event=None):
        """Ders değiştiğinde konu listesini ve soru limitini günceller."""
        self._update_konu_list()
        self.update_question_limit()

    def _update_konu_list(self, event=None):
        """Seçilen yıl ve derse göre mevcut konuları konu dropdown'ına yükler."""
        if not self.questions or not hasattr(self, 'konu_combo'):
            return

        selected_year = self.year_var.get()
        selected_ders = self.ders_var.get()

        qs = self.questions
        if selected_year != "Tüm yıllar":
            try:
                year = int(selected_year)
                qs = [q for q in qs if q['yil'] == year]
            except Exception:
                pass
        if selected_ders and selected_ders != "Tüm dersler":
            qs = [q for q in qs if q['ders'] == selected_ders]

        konular = sorted(set(q['konu'] for q in qs if q.get('konu')))
        values = ["Tüm konular"] + konular
        self.konu_combo['values'] = values

        current = self.konu_var.get()
        if current not in values:
            self.konu_var.set("Tüm konular")

    def resolve_visual_path(self, raw_path: str, year: int) -> str:
        """Görsel için göreli/tam yolu uygulamadaki gerçek dosya yoluna çevirir."""
        cleaned = raw_path.strip().rstrip(']').strip()
        if cleaned.startswith('[RESIM:'):
            cleaned = cleaned.split(':', 1)[1].strip()

        cleaned = cleaned.replace('/', os.sep).replace('\\', os.sep)
        base_dir = r"C:\Users\osman\Desktop\OSYM"
        filename = os.path.basename(cleaned)

        candidates = []
        if os.path.isabs(cleaned):
            candidates.append(os.path.normpath(cleaned))
        else:
            candidates.append(os.path.normpath(os.path.join(base_dir, cleaned)))
            candidates.append(os.path.normpath(os.path.join(base_dir, "Gorseller", str(year), filename)))
            candidates.append(os.path.normpath(os.path.join(base_dir, "Gorseller", f"{year} ihl", filename)))
            candidates.append(os.path.normpath(os.path.join(base_dir, "Gorseller", f"{year} IHL", filename)))

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

        return candidates[0] if candidates else cleaned

    def parse_questions_from_file(self, file_path: str, year: int, subject: str = "DKAB") -> List[Dict]:
        """Dosyadan soruları parse eder"""
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
                    question = self.parse_single_question(block, year, subject)
                    if question:
                        questions.append(question)
                        
        except Exception as e:
            print(f"Parse hatas? {year}: {e}")
            
        return questions

    def parse_single_question(self, text: str, year: int, subject: str = "DKAB") -> Dict:
        """Tek soruyu parse eder"""
        try:
            lines = text.strip().split('\n')
            
            soru_no = None
            soru_metni = []
            options = {}
            dogru_cevap = None
            aciklama = ""
            konu = ""
            gorsel_var = False
            gorsel_dosyalari = []
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('Soru ') and ':' in line:
                    soru_no_str = line.split()[1].replace(':', '')
                    try:
                        soru_no = int(soru_no_str)
                    except ValueError:
                        soru_no = None
                elif line.startswith('[RESIM:'):
                    gorsel_var = True
                    gorsel_dosyalari.append(self.resolve_visual_path(line, year))
                elif line.startswith('KONU:'):
                    konu = line.split(':', 1)[1].strip()
                elif line and not line.startswith('A)') and not line.startswith('B)') and not line.startswith('C)') and not line.startswith('D)') and not line.startswith('E)') and not line.startswith('Doğru Cevap:') and not line.startswith('Dogru Cevap:') and not line.startswith('DoÄŸru Cevap:') and not line.startswith('Do?ru Cevap:') and not line.startswith('Do??ru Cevap:') and not line.startswith('Açıklama:') and not line.startswith('Aciklama:') and not line.startswith('AÃ§Ä±klama:') and not line.startswith('A??klama:') and not line.startswith('A????klama:') and not line.startswith('Görsel') and not line.startswith('Gorsel') and not line.startswith('GÃ¶rsel') and not line.startswith('G?rsel') and not line.startswith('G??rsel') and not line.startswith('Dosya:') and not line.startswith('Konum:') and soru_no and not line.startswith('YIL:') and not line.startswith('DERS:'):
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
                    # Look globally in lines or just this line if it's there
                    dosya_adi = ""
                    if 'Görsel dosyası:' in line: dosya_adi = line.split('Görsel dosyası:')[1].strip()
                    elif 'GÃ¶rsel dosyasÄ±:' in line: dosya_adi = line.split('GÃ¶rsel dosyasÄ±:')[1].strip()
                    elif 'G?rsel dosyas?:' in line: dosya_adi = line.split('G?rsel dosyas?:')[1].strip()
                    elif 'Gorsel dosyasi:' in line: dosya_adi = line.split('Gorsel dosyasi:')[1].strip()
                    elif 'G??rsel dosyas??:' in line: dosya_adi = line.split('G??rsel dosyas??:')[1].strip()
                    elif 'Dosya:' in line: dosya_adi = line.split('Dosya:')[1].strip()
                    
                    if dosya_adi:
                        gorsel_dosyalari.append(self.resolve_visual_path(dosya_adi, year))
                
                i += 1
            
            if soru_no and len(options) >= 2 and dogru_cevap:
                return {
                    "yil": year,
                    "ders": subject,
                    "konu": konu if konu else subject,
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

    def get_question_limit_for_year(self, selected_year, selected_ders, selected_konu=None):
        """Yıla, derse ve konuya göre maksimum soru sayısını döner."""
        if self.questions:
            qs = self.questions
            if selected_year != "Tüm yıllar":
                try:
                    year = int(selected_year)
                    qs = [q for q in qs if q['yil'] == year]
                except Exception:
                    pass
            
            if selected_ders and selected_ders != "Tüm dersler":
                qs = [q for q in qs if q['ders'] == selected_ders]

            if selected_konu and selected_konu != "Tüm konular":
                qs = [q for q in qs if q.get('konu') == selected_konu]
            
            return len(qs) if qs else 75
        return 75

    def update_question_limit(self, event=None):
        """Seçilen yıla, derse ve konuya göre soru limitini günceller."""
        selected_year = self.year_var.get()
        selected_ders = self.ders_var.get()
        selected_konu = self.konu_var.get() if hasattr(self, 'konu_var') else "Tüm konular"
        max_questions = self.get_question_limit_for_year(selected_year, selected_ders, selected_konu)
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
            key = f"{q['yil']} {q['ders']}"
            year_dist[key] = year_dist.get(key, 0) + 1
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        stats_text = f"📊 TOPLAM SORU: {len(self.questions)}\n\n"
        stats_text += "📅 Sınav bazlı dağılım:\n"
        stats_text += "-" * 30 + "\n"
        
        for key in sorted(year_dist.keys(), reverse=True):
            stats_text += f"  {key}: {year_dist[key]} soru\n"
        
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
            selected_ders = self.ders_var.get()
            selected_konu = self.konu_var.get() if hasattr(self, 'konu_var') else "Tüm konular"
            max_questions = self.get_question_limit_for_year(selected_year, selected_ders, selected_konu)
            if num_questions < 1 or num_questions > max_questions:
                messagebox.showwarning("Uyarı", f"Soru sayısı 1-{max_questions} arasında olmalı!")
                return
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir soru sayısı girin!")
            return

        self._stop_countdown()

        # Filter questions by year, subject, and konu if selected
        available_questions = self.questions
        selected_year = self.year_var.get()
        selected_ders = self.ders_var.get()
        selected_konu = self.konu_var.get() if hasattr(self, 'konu_var') else "Tüm konular"
        
        if selected_year != "Tüm yıllar":
            year = int(selected_year)
            available_questions = [q for q in available_questions if q['yil'] == year]
        
        if selected_ders and selected_ders != "Tüm dersler":
            available_questions = [q for q in available_questions if q['ders'] == selected_ders]

        if selected_konu and selected_konu != "Tüm konular":
            available_questions = [q for q in available_questions if q.get('konu') == selected_konu]
            
        if not available_questions:
            messagebox.showwarning("Uyarı", "Seçilen kriterlere uygun soru bulunamadı!")
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
        self.active_mode = self.mode_var.get()
        self._start_elapsed_tracking()

        if self._is_timed_quiz():
            try:
                minutes = int(self.time_limit_var.get())
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir süre girin!")
                return
            if minutes < 1:
                messagebox.showwarning("Uyarı", "Süre en az 1 dakika olmalı!")
                return
            self._start_countdown(minutes)
        else:
            self.remaining_seconds = 0
            self._set_status_ready()
        
        # Start quiz
        self.show_question()
    
    def show_question(self):
        self.current_view = "question"
        """Soruyu gösterir"""
        if self.current_index >= len(self.quiz_questions):
            # If we're in review mode, show per-question evaluation instead of plain results.
            if self._uses_review_flow():
                self.show_review_screen()
            else:
                self.show_results()
            return
        
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        question = self.quiz_questions[self.current_index]
        self.question_start_time = time.monotonic()
        
        # Question card
        question_card = self.create_card(self.main_content, f"📝 Soru {self.current_index + 1}/{self.total_questions}")
        question_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content_frame = tk.Frame(question_card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Progress bar
        progress_frame = tk.Frame(content_frame, bg=self.colors['card'])
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        konu_display = f" | Konu: {question['konu']}" if question.get('konu') and question['konu'] != question['ders'] else ""
        progress_text = tk.Label(progress_frame, 
                                text=f"İlerleme: {self.current_index + 1}/{self.total_questions} | Sınav: {question['ders']} | Yıl: {question['yil']} | No: {question['soru_no']}{konu_display}", 
                                font=self.fonts['small'], 
                                fg=self.colors['text_secondary'], bg=self.colors['card'])
        progress_text.pack(side=tk.LEFT)

        time_info_frame = tk.Frame(content_frame, bg=self.colors['card'])
        time_info_frame.pack(fill=tk.X, pady=(0, 10))

        self.elapsed_text_var = tk.StringVar(
            value=f"Geçen Süre: {self._format_seconds(self.total_elapsed_seconds)}"
        )
        self.question_elapsed_text_var = tk.StringVar(value="Bu Soru: 00:00")

        tk.Label(time_info_frame,
                 textvariable=self.elapsed_text_var,
                 font=self.fonts['small'],
                 fg=self.colors['text_secondary'], bg=self.colors['card']).pack(side=tk.LEFT)

        tk.Label(time_info_frame,
                 textvariable=self.question_elapsed_text_var,
                 font=self.fonts['small'],
                 fg=self.colors['warning'], bg=self.colors['card']).pack(side=tk.LEFT, padx=(15, 0))

        if self._is_timed_quiz():
            self.timer_text_var = tk.StringVar(value=f"Kalan Süre: {self._format_seconds(self.remaining_seconds)}")
            timer_label = tk.Label(progress_frame,
                                   textvariable=self.timer_text_var,
                                   font=self.fonts['small'],
                                   fg=self.colors['warning'], bg=self.colors['card'])
            timer_label.pack(side=tk.RIGHT)
        
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
            if self._uses_review_flow():
                finish_command = self.show_review_screen
            finish_btn = self.create_button(nav_frame, "🏁", finish_command, self.colors['accent'])
            finish_btn.pack(side=tk.RIGHT, padx=5, ipady=2)
        
        # Restore selection from history if exists
        self.restore_selection_from_history(question)
    
    def select_option(self, var, option_num):
        """Seçenek seçildiğinde - moda göre davranır"""
        question = self.quiz_questions[self.current_index]
        
        # Check if already answered in Instant Mode
        if self._quiz_mode() == "Anında Cevap":
            for item in self.test_history:
                if (item['question']['yil'] == question['yil'] and 
                    item['question']['soru_no'] == question['soru_no'] and
                    item['question']['ders'] == question['ders']):
                    return
        
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
        if self._quiz_mode() == "Anında Cevap":
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
            
            # Store the answer for later review (Update if already exists)
            if not hasattr(self, 'user_answers'):
                self.user_answers = []
            
            existing_ans = None
            for ans in self.user_answers:
                if (ans['question']['yil'] == question['yil'] and 
                    ans['question']['soru_no'] == question['soru_no'] and
                    ans['question']['ders'] == question['ders']):
                    existing_ans = ans
                    break
            
            answer_data = {
                'question': question,
                'selected_option': selected_sik,
                'correct_option': question['dogru_cevap'],
                'is_correct': selected_sik == question['dogru_cevap']
            }
            
            if existing_ans:
                # Update existing entry
                existing_ans.update(answer_data)
            else:
                # Add new entry
                self.user_answers.append(answer_data)
            
            # Cancel any existing pending skip-timer
            if self._next_timer:
                self.root.after_cancel(self._next_timer)
                self._next_timer = None
            
            # Auto-advance after 2 seconds
            if self.current_index < len(self.quiz_questions) - 1:
                self._next_timer = self.root.after(2000, self.next_question)
            else:
                finish_target = self.show_results if self._quiz_mode() == "Süreli" else self.show_review_screen
                self._next_timer = self.root.after(2000, finish_target)
    
    def update_test_history(self, question, selected_sik):
        """Test geçmişini günceller"""
        # Find if this question is already in history
        for item in self.test_history:
            if (item['question']['yil'] == question['yil'] and 
                item['question']['soru_no'] == question['soru_no'] and
                item['question']['ders'] == question['ders']):
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
            if (item['question']['yil'] == question['yil'] and 
                item['question']['soru_no'] == question['soru_no'] and
                item['question']['ders'] == question['ders']):
                
                selected_sik = item['selected']
                is_correct = (selected_sik == question['dogru_cevap'])
                
                # Find the option number for this selection
                for option_num, sik_key in self.option_map.items():
                    if sik_key == selected_sik:
                        # Set the selection
                        self.option_vars[option_num].set(option_num)
                        
                        if self._quiz_mode() == "Anında Cevap":
                            if is_correct:
                                self.option_buttons[option_num].config(bg=self.colors['success'], fg='white')
                            else:
                                self.option_buttons[option_num].config(bg=self.colors['danger'], fg='white')
                                # Also highlight correct one
                                for opt_num, s_key in self.option_map.items():
                                    if s_key == question['dogru_cevap']:
                                        self.option_buttons[opt_num].config(bg=self.colors['success'], fg='white')
                                        break
                            # Show feedback on screen
                            self.show_feedback_on_screen(question, is_correct)
                        else:
                            # Test/Review mode - generic highlight
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
        user_choice_letter = self.option_map[selected]
        
        # Store the answer for later review (Update if exists)
        if not hasattr(self, 'user_answers'):
            self.user_answers = []
        
        existing_ans = None
        for ans in self.user_answers:
            if (ans['question']['yil'] == question['yil'] and 
                ans['question']['soru_no'] == question['soru_no'] and
                ans['question']['ders'] == question['ders']):
                existing_ans = ans
                break
        
        answer_data = {
            'question': question,
            'selected_option': user_choice_letter,
            'correct_option': question['dogru_cevap'],
            'is_correct': user_choice_letter == question['dogru_cevap']
        }
        
        if existing_ans:
            existing_ans.update(answer_data)
        else:
            self.user_answers.append(answer_data)
        
        # Color the selected option
        selected_button = self.option_buttons[selected]
        if user_choice_letter == question['dogru_cevap']:
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
        self.current_view = "review"
        """Değerlendirme ekranını gösterir"""
        self._store_current_question_time()
        if self.test_start_time is not None:
            self.total_elapsed_seconds = max(0, int(time.monotonic() - self.test_start_time))
        self._stop_countdown()
        self._stop_elapsed_tracking()
        self.remaining_seconds = 0
        self._set_status_ready()
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

        tk.Label(score_frame,
                 text=f"Toplam Süre: {self._format_seconds(self.total_elapsed_seconds)}",
                 font=self.fonts['small'], bg=self.colors['primary'], fg=self.colors['text_secondary']).pack(pady=(0, 12))
        
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
            
            konu_display = f", Konu: {q['konu']}" if q.get('konu') and q['konu'] != q['ders'] else ""
            review_content += f"Soru {i} (Sınav: {q['ders']}, Yıl: {q['yil']}, No: {q['soru_no']}{konu_display}) - {status}\n"
            review_content += f"Soru: {q['soru_metni'][:80]}...\n"
            review_content += f"Sizin cevabınız: {q['siklar'].get(answer['selected_option'], 'N/A')}\n"
            review_content += f"Doğru cevap: {q['siklar'].get(answer['correct_option'], 'N/A')}\n"
            review_content += f"Süre: {self._format_seconds(self.question_times.get(self._question_key(q), 0))}\n"
            
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
        """Seçilen yıla ve derse göre mevcut soru numaralarını günceller"""
        try:
            year = int(self.goto_year_var.get())
            ders = self.goto_ders_var.get()
            nums = sorted(set(q['soru_no'] for q in self.questions if q['yil'] == year and q['ders'] == ders))
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
            ders = self.goto_ders_var.get()
            q_no = int(self.goto_q_var.get())
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir yıl ve soru numarası girin!")
            return

        filtered_questions = [q for q in self.questions if q['yil'] == year and q['ders'] == ders]
        matches = [q for q in filtered_questions if q['soru_no'] == q_no]
        if not matches and filtered_questions:
            nums = sorted(set(q['soru_no'] for q in filtered_questions))
            messagebox.showwarning("UyarÄ±", f"{ders} {year} yÄ±lÄ± {q_no}. soru bulunamadÄ±!\n"
                                            f"Bu ders/yÄ±l iÃ§in yÃ¼klÃ¼ sorular: {nums}")
            return
        if not matches:
            messagebox.showwarning("Uyarı", f"{year} yılı {q_no}. soru bulunamadı!\n"
                                            f"Bu yıla ait yüklü sorular: "
                                            f"{sorted(set(q['soru_no'] for q in self.questions if q['yil'] == year))}")
            return

        self.show_specific_question(matches[0])

    def show_specific_question(self, question):
        self.current_view = "specific"
        self.current_specific_question = question
        """Tek bir soruyu inceleme modunda (cevap + açıklama göster) ekrana basar"""
        self._store_current_question_time()
        if self.test_start_time is not None:
            self.total_elapsed_seconds = max(0, int(time.monotonic() - self.test_start_time))
        self._stop_countdown()
        self._stop_elapsed_tracking()
        self.remaining_seconds = 0
        self._set_status_ready()
        for widget in self.main_content.winfo_children():
            widget.destroy()

        card = self.create_card(
            self.main_content,
            f"📖  {question['ders']} {question['yil']} – Soru {question['soru_no']}")
        card.pack(fill=tk.X, padx=10, pady=10)

        self.root.update_idletasks()
        available_height = max(self.canvas.winfo_height() - 40, 500)

        # Scrollable container
        canvas = tk.Canvas(card, bg=self.colors['card'], highlightthickness=0, height=available_height)
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=canvas.yview, style="Modern.Vertical.TScrollbar")
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
        konu_display = f"   |   📖 Konu: {question['konu']}" if question.get('konu') and question['konu'] != question['ders'] else ""
        tk.Label(meta_frame,
                 text=f"📅 Sınav: {question['ders']}   |   📅 Yıl: {question['yil']}   |   🔢 Soru No: {question['soru_no']}{konu_display}",
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

        # --- Komşu soru butonları (aynı ders içinde) ---
        year_qs = sorted([q for q in self.questions if q['yil'] == question['yil'] and q['ders'] == question['ders']],
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
        self._store_current_question_time()
        if self._next_timer:
            self.root.after_cancel(self._next_timer)
            self._next_timer = None
        self.current_index += 1
        self.show_question()
    
    def previous_question(self):
        """Önceki soruya döner"""
        self._store_current_question_time()
        if self._next_timer:
            self.root.after_cancel(self._next_timer)
            self._next_timer = None
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()
    
    def show_results(self):
        self.current_view = "results"
        """Sonu?lar? g?sterir - show_review_screen ile ayn? stil"""
        self._store_current_question_time()
        if self.test_start_time is not None:
            self.total_elapsed_seconds = max(0, int(time.monotonic() - self.test_start_time))
        self._stop_countdown()
        self._stop_elapsed_tracking()
        self.remaining_seconds = 0
        self._set_status_ready()

        for widget in self.main_content.winfo_children():
            widget.destroy()

        results_card = self.create_card(self.main_content, "?? TEST DE?ERLEND?RME")
        results_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        content_frame = tk.Frame(results_card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.score = sum(
            1
            for q in self.quiz_questions
            for item in self.test_history
            if (item['question']['yil'] == q['yil']
                and item['question']['soru_no'] == q['soru_no']
                and item['question']['ders'] == q['ders']
                and item['selected'] == q['dogru_cevap'])
        )

        percentage = (self.score / self.total_questions) * 100 if self.total_questions else 0.0

        score_frame = tk.Frame(content_frame, bg=self.colors['primary'], relief=tk.RIDGE, bd=2)
        score_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            score_frame,
            text=f"SKOR: {self.score}/{self.total_questions} (%{percentage:.1f})",
            font=self.fonts['header'],
            bg=self.colors['primary'],
            fg=self.colors['text']
        ).pack(pady=15)

        tk.Label(
            score_frame,
            text=f"Toplam S?re: {self._format_seconds(self.total_elapsed_seconds)}",
            font=self.fonts['small'],
            bg=self.colors['primary'],
            fg=self.colors['text_secondary']
        ).pack(pady=(0, 12))

        review_text = tk.Text(
            content_frame,
            font=self.fonts['body'],
            bg=self.colors['card'],
            fg=self.colors['text'],
            wrap=tk.WORD,
            height=15,
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        review_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        review_content = "SORU DE?ERLEND?RMES?:\n" + "=" * 50 + "\n\n"

        for i, q in enumerate(self.quiz_questions, 1):
            status = "??aretlenmedi"
            selected_txt = "N/A"
            correct_txt = q['siklar'].get(q['dogru_cevap'], 'N/A')
            is_correct = False
            elapsed = self.question_times.get(self._question_key(q), 0)

            for item in self.test_history:
                if (
                    item['question']['yil'] == q['yil']
                    and item['question']['soru_no'] == q['soru_no']
                    and item['question']['ders'] == q['ders']
                ):
                    selected_txt = q['siklar'].get(item['selected'], 'N/A')
                    is_correct = (item['selected'] == q['dogru_cevap'])
                    status = "? DO?RU" if is_correct else "? YANLI?"
                    break

            konu_display = (
                f", Konu: {q['konu']}"
                if q.get('konu') and q['konu'] != q['ders'] else ""
            )

            review_content += (
                f"Soru {i} (S?nav: {q['ders']}, Y?l: {q['yil']}, "
                f"No: {q['soru_no']}{konu_display}) - {status}\n"
            )
            review_content += f"Soru: {q['soru_metni'][:80]}...\n"
            review_content += f"Sizin cevab?n?z: {selected_txt}\n"
            review_content += f"Do?ru cevap: {correct_txt}\n"
            review_content += f"S?re: {self._format_seconds(elapsed)}\n"

            if not is_correct and q.get('aciklama'):
                review_content += f"A??klama: {q['aciklama'][:100]}...\n"

            review_content += "-" * 50 + "\n\n"

        review_text.insert(tk.END, review_content)
        review_text.config(state=tk.DISABLED)

        button_frame = tk.Frame(content_frame, bg=self.colors['card'])
        button_frame.pack(fill=tk.X, pady=20)

        new_test_btn = self.create_button(
            button_frame,
            "?? YEN? TEST",
            self.new_test,
            self.colors['success']
        )
        new_test_btn.pack(side=tk.LEFT, padx=10, ipady=8)

        menu_btn = self.create_button(
            button_frame,
            "?? ANA MEN?",
            self.show_welcome_screen,
            self.colors['text_secondary']
        )
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
