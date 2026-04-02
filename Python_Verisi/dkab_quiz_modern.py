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
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import threading
import wave

try:
    from similarity_analyzer import build_similarity_report, filter_questions
except ImportError:
    from Python_Verisi.similarity_analyzer import build_similarity_report, filter_questions

try:
    from project_paths import GORSSELLER_DIR, ROOT_DIR, WORDE_DIR
    from question_bank import (
        format_subject_label as format_exam_subject_label,
        has_dhbt_common_file as question_bank_has_dhbt_common_file,
        load_question_bank,
        parse_questions_from_file as parse_questions_from_exam_file,
        parse_single_question_block,
        should_skip_dhbt_common_question as question_bank_should_skip_dhbt_common_question,
    )
    from topic_catalog import (
        CANONICAL_TOPICS,
        map_summary_heading_to_topics,
        normalize_topic_name as catalog_normalize_topic_name,
        topic_sort_key,
    )
    from topic_text_parser import normalize_sentence_for_tts, parse_topic_text_file
except ImportError:
    from Python_Verisi.project_paths import GORSSELLER_DIR, ROOT_DIR, WORDE_DIR
    from Python_Verisi.question_bank import (
        format_subject_label as format_exam_subject_label,
        has_dhbt_common_file as question_bank_has_dhbt_common_file,
        load_question_bank,
        parse_questions_from_file as parse_questions_from_exam_file,
        parse_single_question_block,
        should_skip_dhbt_common_question as question_bank_should_skip_dhbt_common_question,
    )
    from Python_Verisi.topic_catalog import (
        CANONICAL_TOPICS,
        map_summary_heading_to_topics,
        normalize_topic_name as catalog_normalize_topic_name,
        topic_sort_key,
    )
    from Python_Verisi.topic_text_parser import normalize_sentence_for_tts, parse_topic_text_file

try:
    import winsound
except ImportError:
    winsound = None

PIPER_IMPORT_ERROR = None

ALLOWED_DHBT_TOPICS = list(CANONICAL_TOPICS)

ALL_YEARS_LABEL = "Tüm yıllar"
ALL_DERSLER_LABEL = "Tüm dersler"
ALL_KONULAR_LABEL = "Tüm konular"
MULTI_VALUE_SEPARATOR = " || "
SUMMARY_EXAM_FAMILY_ORDER = ("DHBT", "MBSTS", "ÖABT", "İHL")


class MultiSelectFilter:
    def __init__(self, parent, *, textvariable, all_label, values=None, command=None, colors=None):
        self.parent = parent
        self.textvariable = textvariable
        self.all_label = all_label
        self.command = command
        self.colors = colors or {}
        self.values = list(values or [])
        self.selected_values = []
        self.popup = None
        self.option_vars = {}

        self.button = tk.Button(
            parent,
            textvariable=self.textvariable,
            anchor="w",
            relief="solid",
            bd=1,
            padx=8,
            pady=6,
            bg=self.colors.get("primary", "#ffffff"),
            fg=self.colors.get("text", "#000000"),
            activebackground=self.colors.get("primary", "#ffffff"),
            activeforeground=self.colors.get("text", "#000000"),
            highlightthickness=0,
            command=self.open_panel,
        )

    def pack(self, *args, **kwargs):
        self.button.pack(*args, **kwargs)

    def destroy_popup(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        self.popup = None
        self.option_vars = {}

    def get_selected(self):
        return list(self.selected_values)

    def set_values(self, values):
        self.values = list(values or [])
        self.selected_values = [value for value in self.selected_values if value in self.values]
        self._refresh_label()
        self._refresh_popup_options()

    def set_selected(self, values, notify=False):
        clean_values = []
        seen = set()
        for value in values or []:
            if value in self.values and value not in seen:
                clean_values.append(value)
                seen.add(value)
        self.selected_values = clean_values
        self._refresh_label()
        self._refresh_popup_options()
        if notify and self.command:
            self.command()

    def open_panel(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.lift()
            self.popup.focus_force()
            return

        self.popup = tk.Toplevel(self.parent)
        self.popup.title(self.all_label)
        self.popup.transient(self.parent.winfo_toplevel())
        self.popup.resizable(False, False)
        self.popup.configure(bg=self.colors.get("card", "#ffffff"))
        self.popup.protocol("WM_DELETE_WINDOW", self.destroy_popup)

        self.parent.update_idletasks()
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height() + 2
        self.popup.geometry(f"320x340+{x}+{y}")

        header = tk.Label(
            self.popup,
            text=f"Secim: {self.all_label}",
            anchor="w",
            bg=self.colors.get("card", "#ffffff"),
            fg=self.colors.get("text", "#000000"),
            font=("Segoe UI", 9, "bold"),
        )
        header.pack(fill=tk.X, padx=10, pady=(10, 6))

        list_frame = tk.Frame(self.popup, bg=self.colors.get("border", "#d0d0d0"))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        canvas = tk.Canvas(
            list_frame,
            bg=self.colors.get("card", "#ffffff"),
            highlightthickness=0,
            bd=0,
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, style="Modern.Vertical.TScrollbar")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.options_container = tk.Frame(canvas, bg=self.colors.get("card", "#ffffff"))
        self.options_window = canvas.create_window((0, 0), window=self.options_container, anchor="nw")

        self.options_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(self.options_window, width=e.width)
        )

        controls = tk.Frame(self.popup, bg=self.colors.get("card", "#ffffff"))
        controls.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(
            controls,
            text="Tumunu Sec",
            command=self.select_all,
            bg=self.colors.get("accent", "#dddddd"),
            fg=self.colors.get("text", "#000000"),
            relief="flat",
        ).pack(side=tk.LEFT)
        tk.Button(
            controls,
            text="Temizle",
            command=self.clear_selection,
            bg=self.colors.get("primary", "#eeeeee"),
            fg=self.colors.get("text", "#000000"),
            relief="flat",
        ).pack(side=tk.LEFT, padx=6)
        tk.Button(
            controls,
            text="Kapat",
            command=self.destroy_popup,
            bg=self.colors.get("success", "#22c55e"),
            fg=self.colors.get("text", "#000000"),
            relief="flat",
        ).pack(side=tk.RIGHT)

        self._refresh_popup_options()

    def _refresh_popup_options(self):
        if not self.popup or not self.popup.winfo_exists() or not hasattr(self, "options_container"):
            return

        for child in self.options_container.winfo_children():
            child.destroy()

        self.option_vars = {}
        for value in self.values:
            var = tk.BooleanVar(value=value in self.selected_values)
            self.option_vars[value] = var
            chk = tk.Checkbutton(
                self.options_container,
                text=value,
                variable=var,
                anchor="w",
                command=self._on_option_toggled,
                bg=self.colors.get("card", "#ffffff"),
                fg=self.colors.get("text", "#000000"),
                selectcolor=self.colors.get("primary", "#ffffff"),
                activebackground=self.colors.get("card", "#ffffff"),
                activeforeground=self.colors.get("text", "#000000"),
                highlightthickness=0,
            )
            chk.pack(fill=tk.X, padx=8, pady=2)

    def _on_option_toggled(self):
        self.selected_values = [
            value for value in self.values
            if self.option_vars.get(value) and self.option_vars[value].get()
        ]
        self._refresh_label()
        if self.command:
            self.command()

    def _refresh_label(self):
        if not self.selected_values:
            label = self.all_label
        elif len(self.selected_values) == 1:
            label = self.selected_values[0]
        elif len(self.selected_values) <= 3:
            label = ", ".join(self.selected_values)
        else:
            label = f"{len(self.selected_values)} secim yapildi"
        self.textvariable.set(label)

    def select_all(self):
        self.selected_values = list(self.values)
        self._refresh_label()
        self._refresh_popup_options()
        if self.command:
            self.command()

    def clear_selection(self):
        self.selected_values = []
        self._refresh_label()
        self._refresh_popup_options()
        if self.command:
            self.command()


def _bootstrap_project_venv_packages():
    script_dir = Path(__file__).resolve().parent
    candidate_roots = [
        script_dir.parent,
        script_dir,
    ]

    for root_dir in candidate_roots:
        venv_dir = root_dir / ".venv"
        site_packages = venv_dir / "Lib" / "site-packages"
        scripts_dir = venv_dir / "Scripts"

        if site_packages.exists():
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.insert(0, site_packages_str)

            if scripts_dir.exists():
                os.environ["PATH"] = (
                    f"{scripts_dir}{os.pathsep}{os.environ.get('PATH', '')}"
                )
            return True

    return False


try:
    from piper import PiperVoice, SynthesisConfig
except Exception as exc:
    PiperVoice = None
    SynthesisConfig = None
    PIPER_IMPORT_ERROR = str(exc)

    if _bootstrap_project_venv_packages():
        try:
            from piper import PiperVoice, SynthesisConfig
            PIPER_IMPORT_ERROR = None
        except Exception as retry_exc:
            PiperVoice = None
            SynthesisConfig = None
            PIPER_IMPORT_ERROR = str(retry_exc)


class OfflineTurkishTTS:
    """Yerel Piper modeliyle çevrimdışı Türkçe okuma yapar."""

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.model_dir = self.base_dir / "tts_models" / "piper"
        self.cache_dir = self.model_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._voice_cache = {}
        self._request_token = 0
        self._lock = threading.Lock()
        self._last_error = PIPER_IMPORT_ERROR
        self.voice_catalog = self._discover_local_voices()

    def _discover_local_voices(self):
        voices = {}
        if winsound is None:
            self._last_error = "winsound modülü yüklenemedi."
            return voices

        if PiperVoice is None or SynthesisConfig is None:
            if not self._last_error:
                self._last_error = "Piper modülü yüklenemedi."
            return voices

        if not self.model_dir.exists():
            self._last_error = f"Model klasörü bulunamadı: {self.model_dir}"
            return voices

        for model_path in sorted(self.model_dir.glob("tr_*.onnx")):
            config_path = model_path.with_suffix(".onnx.json")
            if not config_path.exists():
                continue

            voice_id = model_path.stem
            voices[voice_id] = {
                "id": voice_id,
                "label": self._format_voice_label(voice_id),
                "model_path": model_path,
                "config_path": config_path,
            }

        if voices:
            self._last_error = None
        else:
            self._last_error = (
                f"Türkçe Piper modeli bulunamadı: {self.model_dir}"
            )

        return voices

    def _format_voice_label(self, voice_id):
        parts = voice_id.split("-")
        quality_map = {
            "low": "Ekonomik",
            "medium": "Orta",
            "high": "Yüksek",
        }

        if len(parts) >= 3 and parts[0].lower() == "tr_tr":
            speaker_name = parts[1].upper()
            quality = quality_map.get(parts[2].lower(), parts[2].capitalize())
            return f"Piper Türkçe {speaker_name} ({quality})"

        return f"Piper {voice_id}"

    def is_available(self):
        return bool(self.voice_catalog)

    def get_voice_choices(self):
        return [
            (voice_info["id"], voice_info["label"])
            for voice_info in self.voice_catalog.values()
        ]

    def get_default_voice_label(self):
        choices = self.get_voice_choices()
        if choices:
            return choices[0][1]
        return "Türkçe ses modeli bulunamadı"

    def get_last_error(self):
        return self._last_error

    def _load_voice(self, voice_id):
        if voice_id not in self.voice_catalog:
            raise ValueError("Seçilen Türkçe ses modeli bulunamadı.")

        with self._lock:
            if voice_id not in self._voice_cache:
                voice_info = self.voice_catalog[voice_id]
                self._voice_cache[voice_id] = PiperVoice.load(
                    voice_info["model_path"],
                    config_path=voice_info["config_path"],
                )

            return self._voice_cache[voice_id]

    def _cleanup_cache(self, keep_name=None):
        try:
            wav_files = sorted(
                self.cache_dir.glob("speech_*.wav"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        except Exception:
            return

        for old_file in wav_files[4:]:
            if keep_name and old_file.name == keep_name:
                continue
            try:
                old_file.unlink()
            except OSError:
                pass

    def cleanup_all_cache(self):
        try:
            wav_files = list(self.cache_dir.glob("speech_*.wav"))
        except Exception:
            return

        for wav_file in wav_files:
            try:
                wav_file.unlink()
            except OSError:
                pass

    def _speed_to_length_scale(self, speed_value):
        speed_value = max(0.5, min(2.0, float(speed_value)))
        return round(1.0 / speed_value, 3)

    def stop(self):
        self._request_token += 1
        if winsound is not None:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except RuntimeError:
                pass

    def speak(self, text, voice_id, speed_value=1.0, on_ready=None, on_error=None):
        normalized_text = " ".join(str(text or "").split())
        if not normalized_text:
            if on_error:
                on_error("Okunacak metin bulunamadı.")
            return False

        if not self.is_available():
            if on_error:
                on_error("Çevrimdışı Türkçe ses modeli hazır değil.")
            return False

        self.stop()
        self._request_token += 1
        token = self._request_token

        worker = threading.Thread(
            target=self._speak_worker,
            args=(normalized_text, voice_id, speed_value, token, on_ready, on_error),
            daemon=True,
        )
        worker.start()
        return True

    def _speak_worker(self, text, voice_id, speed_value, token, on_ready, on_error):
        try:
            voice = self._load_voice(voice_id)
            output_path = self.cache_dir / f"speech_{token}.wav"
            self._cleanup_cache(keep_name=output_path.name)

            syn_config = SynthesisConfig(
                length_scale=self._speed_to_length_scale(speed_value)
            )
            with wave.open(str(output_path), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file, syn_config=syn_config)

            with wave.open(str(output_path), "rb") as wav_file:
                frame_rate = wav_file.getframerate()
                frame_count = wav_file.getnframes()
                duration_seconds = (frame_count / frame_rate) if frame_rate else 0.0

            if token != self._request_token:
                try:
                    output_path.unlink()
                except OSError:
                    pass
                return

            winsound.PlaySound(
                str(output_path),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )

            if on_ready:
                on_ready(output_path, duration_seconds)
        except Exception as exc:
            self._last_error = str(exc)
            if on_error:
                on_error(str(exc))

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
        self.available_subjects = [
            "DKAB",
            "IHL",
            "MBSTS",
            "DHBT Ortak (1-20)",
            "DHBT Lisans",
            "DHBT Önlisans",
            "DHBT Ortaöğretim",
        ]
        self._next_timer = None
        self._countdown_job = None
        self._elapsed_job = None
        self.remaining_seconds = 0
        self.test_start_time = None
        self.question_start_time = None
        self.total_elapsed_seconds = 0
        self.question_times = {}
        self.active_mode = None
        self.base_dir = Path(__file__).resolve().parent
        self.settings_file = str(self.base_dir / "dkab_quiz_settings.json")
        self.speech_engine = OfflineTurkishTTS(self.base_dir)
        self.speech_voice_choices = self.speech_engine.get_voice_choices()
        self.speech_voice_map = {
            label: voice_id for voice_id, label in self.speech_voice_choices
        }
        self.speech_status_var = tk.StringVar(
            value=self._initial_speech_status_text()
        )
        self._speech_sequence_job = None
        self._speech_sequence_token = 0
        self._summary_exam_families_by_topic: Dict[str, Set[str]] = {}
        self._summary_question_refs_by_topic: Dict[str, Dict[str, List[Dict[str, object]]]] = {}
        self._summary_exam_index_key = None
        self.persisted_settings = self.load_persisted_settings()

        self.theme_palettes = {
            "Gece Lacivert": {
                'bg': '#0b1220',
                'card': '#121c2e',
                'accent': '#38bdf8',
                'primary': '#1c2a44',
                'success': '#22c55e',
                'warning': '#f59e0b',
                'danger': '#f87171',
                'text': '#f8fafc',
                'text_secondary': '#94a3b8',
                'border': '#26354d'
            },
            "Zumrut": {
                'bg': '#081915',
                'card': '#102923',
                'accent': '#34d399',
                'primary': '#183a31',
                'success': '#22c55e',
                'warning': '#fbbf24',
                'danger': '#f87171',
                'text': '#ecfdf5',
                'text_secondary': '#a7f3d0',
                'border': '#214b41'
            },
            "Gun Batimi": {
                'bg': '#22161b',
                'card': '#352129',
                'accent': '#fb7185',
                'primary': '#4a2830',
                'success': '#34d399',
                'warning': '#f59e0b',
                'danger': '#f87171',
                'text': '#fff7ed',
                'text_secondary': '#fdba74',
                'border': '#5e3743'
            },
            "Acik Modern": {
                'bg': '#edf3ff',
                'card': '#ffffff',
                'accent': '#0ea5e9',
                'primary': '#e0ecff',
                'success': '#16a34a',
                'warning': '#d97706',
                'danger': '#dc2626',
                'text': '#0f172a',
                'text_secondary': '#64748b',
                'border': '#d6e2f3'
            }
        }
        self.current_theme = self.persisted_settings.get("theme", "Gece Lacivert")
        self.colors = self.theme_palettes[self.current_theme].copy()
        self.root.configure(bg=self.colors['bg'])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Font styles
        self.fonts = {
            'title': ('Bahnschrift SemiBold', 28),
            'subtitle': ('Segoe UI Semilight', 13),
            'header': ('Bahnschrift SemiBold', 16),
            'body': ('Segoe UI', 11),
            'button': ('Bahnschrift SemiBold', 11),
            'small': ('Segoe UI', 9)
        }

        self.setup_ui()

    def load_persisted_settings(self):
        """Kaydedilen ayarlari diskten okur."""
        defaults = {
            "theme": "Gece Lacivert",
            "year": ALL_YEARS_LABEL,
            "ders": ALL_DERSLER_LABEL,
            "konu": ALL_KONULAR_LABEL,
            "mode": "Anında Cevap",
            "time_limit": "10",
            "time_hours": "0",
            "time_minutes": "10",
            "time_seconds": "0",
            "order": "Sorular Rastgele",
            "num": "10",
            "goto_year": "2019",
            "goto_ders": "DKAB",
            "goto_q": "1",
            "speech_voice": self.speech_engine.get_default_voice_label(),
            "speech_rate": "1.00",
            "speech_read_question": "1",
            "speech_read_options": "0",
            "speech_read_answer": "0",
            "speech_wait_ms": "450",
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
            "time_limit": self.time_minutes_var.get(),
            "time_hours": self.time_hours_var.get(),
            "time_minutes": self.time_minutes_var.get(),
            "time_seconds": self.time_seconds_var.get(),
            "order": self.order_var.get(),
            "num": self.num_var.get(),
            "goto_year": self.goto_year_var.get(),
            "goto_ders": self.goto_ders_var.get(),
            "goto_q": self.goto_q_var.get(),
            "speech_voice": self.speech_voice_var.get(),
            "speech_rate": f"{self.speech_rate_var.get():.2f}",
            "speech_read_question": "1" if self.speech_read_question_var.get() else "0",
            "speech_read_options": "1" if self.speech_read_options_var.get() else "0",
            "speech_read_answer": "1" if self.speech_read_answer_var.get() else "0",
            "speech_wait_ms": str(int(self.speech_wait_ms_var.get())),
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
            self.time_hours_var,
            self.time_minutes_var,
            self.time_seconds_var,
            self.order_var,
            self.num_var,
            self.goto_year_var,
            self.goto_ders_var,
            self.goto_q_var,
            self.speech_voice_var,
            self.speech_rate_var,
            self.speech_read_question_var,
            self.speech_read_options_var,
            self.speech_read_answer_var,
            self.speech_wait_ms_var,
        ]
        for var in vars_to_watch:
            var.trace_add("write", lambda *_: self.save_persisted_settings())

    def apply_persisted_settings(self):
        """Kaydedilen ayarlari arayuze uygular."""
        self.theme_var.set(self.persisted_settings.get("theme", self.current_theme))
        self.year_var.set(self.persisted_settings.get("year", ALL_YEARS_LABEL))
        self.ders_var.set(self.persisted_settings.get("ders", ALL_DERSLER_LABEL))
        self.konu_var.set(self.persisted_settings.get("konu", ALL_KONULAR_LABEL))
        self.mode_var.set(self.persisted_settings.get("mode", "Anında Cevap"))
        self.time_hours_var.set(self.persisted_settings.get("time_hours", "0"))
        self.time_minutes_var.set(self.persisted_settings.get("time_minutes", self.persisted_settings.get("time_limit", "10")))
        self.time_seconds_var.set(self.persisted_settings.get("time_seconds", "0"))
        saved_order = self.persisted_settings.get("order", "Sorular Rastgele")
        if saved_order == "Rastgele":
            saved_order = "Sorular Rastgele"
        self.order_var.set(saved_order)
        self.num_var.set(self.persisted_settings.get("num", "10"))
        self.goto_year_var.set(self.persisted_settings.get("goto_year", "2019"))
        self.goto_ders_var.set(self.persisted_settings.get("goto_ders", "DKAB"))
        self.goto_q_var.set(self.persisted_settings.get("goto_q", "1"))
        saved_voice = self.persisted_settings.get(
            "speech_voice",
            self.speech_engine.get_default_voice_label(),
        )
        valid_voice_labels = [label for _, label in self.speech_voice_choices]
        if valid_voice_labels:
            if saved_voice not in valid_voice_labels:
                saved_voice = valid_voice_labels[0]
        else:
            saved_voice = self.speech_engine.get_default_voice_label()
        self.speech_voice_var.set(saved_voice)
        try:
            saved_rate = float(self.persisted_settings.get("speech_rate", "1.00"))
        except ValueError:
            saved_rate = 1.0
        self.speech_rate_var.set(max(0.7, min(1.6, saved_rate)))
        self.speech_read_question_var.set(
            self._read_bool_setting(
                self.persisted_settings,
                "speech_read_question",
                fallback=self.persisted_settings.get("speech_auto_mode", "Sadece soru") != "Kapalı",
            )
        )
        self.speech_read_options_var.set(
            self._read_bool_setting(
                self.persisted_settings,
                "speech_read_options",
                fallback=self.persisted_settings.get("speech_auto_mode") == "Soru ve şıkları oku",
            )
        )
        self.speech_read_answer_var.set(
            self._read_bool_setting(
                self.persisted_settings,
                "speech_read_answer",
                fallback=self.persisted_settings.get("speech_feedback_mode") == "Doğru cevabı söyle",
            )
        )
        try:
            saved_wait_ms = int(self.persisted_settings.get("speech_wait_ms", "450"))
        except ValueError:
            saved_wait_ms = 450
        self.speech_wait_ms_var.set(max(0, min(5000, saved_wait_ms)))
        self.update_speech_wait_label()
        self.update_speech_rate_label()
        self._restore_filter_widgets_from_vars()
        self._set_speech_status(self._initial_speech_status_text())
        self.on_mode_changed()

    def _serialize_multi_values(self, values, all_label):
        clean_values = [str(value) for value in values or [] if str(value).strip()]
        return MULTI_VALUE_SEPARATOR.join(clean_values) if clean_values else all_label

    def _deserialize_multi_values(self, raw_value, all_label):
        text = str(raw_value or "").strip()
        if not text or text == all_label:
            return []
        if MULTI_VALUE_SEPARATOR in text:
            return [item for item in text.split(MULTI_VALUE_SEPARATOR) if item]
        if "," in text and text != all_label:
            return [item.strip() for item in text.split(",") if item.strip()]
        return [text]

    def _set_filter_selection(self, key, values):
        values = list(values or [])
        if key == "year":
            self.year_var.set(self._serialize_multi_values(values, ALL_YEARS_LABEL))
            if hasattr(self, "year_filter"):
                self.year_filter.set_selected(values)
        elif key == "ders":
            self.ders_var.set(self._serialize_multi_values(values, ALL_DERSLER_LABEL))
            if hasattr(self, "ders_filter"):
                self.ders_filter.set_selected(values)
        elif key == "konu":
            self.konu_var.set(self._serialize_multi_values(values, ALL_KONULAR_LABEL))
            if hasattr(self, "konu_filter"):
                self.konu_filter.set_selected(values)

    def _restore_filter_widgets_from_vars(self):
        if hasattr(self, "year_filter"):
            self.year_filter.set_selected(
                self._deserialize_multi_values(self.year_var.get(), ALL_YEARS_LABEL)
            )
        if hasattr(self, "ders_filter"):
            self.ders_filter.set_selected(
                self._deserialize_multi_values(self.ders_var.get(), ALL_DERSLER_LABEL)
            )
        if hasattr(self, "konu_filter"):
            self.konu_filter.set_selected(
                self._deserialize_multi_values(self.konu_var.get(), ALL_KONULAR_LABEL)
            )

    def _selected_years(self):
        return self._deserialize_multi_values(self.year_var.get(), ALL_YEARS_LABEL)

    def _selected_subjects(self):
        return self._deserialize_multi_values(self.ders_var.get(), ALL_DERSLER_LABEL)

    def _selected_topics(self):
        return self._deserialize_multi_values(self.konu_var.get(), ALL_KONULAR_LABEL)

    def _on_year_filter_changed(self):
        if hasattr(self, "year_filter"):
            self.year_var.set(self._serialize_multi_values(self.year_filter.get_selected(), ALL_YEARS_LABEL))
        self.on_ders_changed()

    def _on_ders_filter_changed(self):
        if hasattr(self, "ders_filter"):
            self.ders_var.set(self._serialize_multi_values(self.ders_filter.get_selected(), ALL_DERSLER_LABEL))
        self.on_ders_changed()

    def _on_konu_filter_changed(self):
        if hasattr(self, "konu_filter"):
            self.konu_var.set(self._serialize_multi_values(self.konu_filter.get_selected(), ALL_KONULAR_LABEL))
        self.update_question_limit()

    def _apply_question_filters(self, questions, years=None, subjects=None, topics=None):
        filtered = list(questions)
        selected_years = years if years is not None else self._selected_years()
        selected_subjects = subjects if subjects is not None else self._selected_subjects()
        selected_topics = topics if topics is not None else self._selected_topics()

        if selected_years:
            year_set = set()
            for year in selected_years:
                try:
                    year_set.add(int(year))
                except Exception:
                    pass
            if year_set:
                filtered = [q for q in filtered if q['yil'] in year_set]

        if selected_subjects:
            subject_set = set(selected_subjects)
            filtered = [q for q in filtered if q['ders'] in subject_set]

        if selected_topics:
            topic_set = set(selected_topics)
            filtered = [q for q in filtered if q.get('konu') in topic_set]

        return filtered

    def _shuffle_questions_enabled(self):
        return self.order_var.get() in ("Rastgele", "Sorular Rastgele", "Ikisi de Rastgele")

    def _shuffle_options_enabled(self):
        return self.order_var.get() in ("Şıklar Rastgele", "Ikisi de Rastgele")

    def _read_bool_setting(self, data, key, fallback=False):
        raw_value = data.get(key)
        if raw_value is None:
            return bool(fallback)
        return str(raw_value).strip().lower() in {"1", "true", "evet", "yes", "on"}

    def _contains_arabic_text(self, text):
        return bool(re.search(r"[\u0600-\u06FF]", str(text or "")))

    def _replace_roman_numerals_for_speech(self, text):
        roman_map = {
            "I": "1",
            "II": "2",
            "III": "3",
            "IV": "4",
            "V": "5",
            "VI": "6",
            "VII": "7",
            "VIII": "8",
            "IX": "9",
            "X": "10",
            "XI": "11",
            "XII": "12",
        }

        pattern = re.compile(
            r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])"
            r"(XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)"
            r"(?![A-Za-zÇĞİÖŞÜçğıöşü])"
        )
        return pattern.sub(lambda match: roman_map.get(match.group(1), match.group(1)), text)

    def _replace_roman_numerals_for_speech(self, text):
        pattern = re.compile(
            r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])"
            r"(M{0,3}(?:CM|CD|D?C{0,3})"
            r"(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{1,3}|I))"
            r"(\.?)"
            r"(?![A-Za-zÇĞİÖŞÜçğıöşü])"
        )
        roman_values = {
            "I": 1,
            "V": 5,
            "X": 10,
            "L": 50,
            "C": 100,
            "D": 500,
            "M": 1000,
        }

        ones = {
            0: "",
            1: "bir",
            2: "iki",
            3: "üç",
            4: "dört",
            5: "beş",
            6: "altı",
            7: "yedi",
            8: "sekiz",
            9: "dokuz",
        }
        tens = {
            0: "",
            1: "on",
            2: "yirmi",
            3: "otuz",
            4: "kırk",
            5: "elli",
            6: "altmış",
            7: "yetmiş",
            8: "seksen",
            9: "doksan",
        }
        ordinal_map = {
            "bir": "birinci",
            "iki": "ikinci",
            "üç": "üçüncü",
            "dört": "dördüncü",
            "beş": "beşinci",
            "altı": "altıncı",
            "yedi": "yedinci",
            "sekiz": "sekizinci",
            "dokuz": "dokuzuncu",
            "on": "onuncu",
            "yirmi": "yirminci",
            "otuz": "otuzuncu",
            "kırk": "kırkıncı",
            "elli": "ellinci",
            "altmış": "altmışıncı",
            "yetmiş": "yetmişinci",
            "seksen": "sekseninci",
            "doksan": "doksanıncı",
            "yüz": "yüzüncü",
            "bin": "bininci",
        }

        def roman_to_int(value):
            total = 0
            previous_value = 0
            for char in reversed(value):
                current_value = roman_values[char]
                if current_value < previous_value:
                    total -= current_value
                else:
                    total += current_value
                    previous_value = current_value
            return total

        def int_to_turkish(value):
            number = int(value)
            if number == 0:
                return "sıfır"

            parts = []
            if number >= 1000:
                thousands = number // 1000
                if thousands > 1:
                    parts.append(ones[thousands])
                parts.append("bin")
                number %= 1000
            if number >= 100:
                hundreds = number // 100
                if hundreds > 1:
                    parts.append(ones[hundreds])
                parts.append("yüz")
                number %= 100
            if number >= 10:
                parts.append(tens[number // 10])
                number %= 10
            if number:
                parts.append(ones[number])
            return " ".join(part for part in parts if part)

        def to_ordinal_words(words):
            parts = [part for part in words.split() if part]
            if not parts:
                return words
            parts[-1] = ordinal_map.get(parts[-1], parts[-1])
            return " ".join(parts)

        def replace(match):
            number = roman_to_int(match.group(1))
            spoken = int_to_turkish(number)
            if match.group(2) == ".":
                spoken = to_ordinal_words(spoken)
            return spoken

        return pattern.sub(replace, str(text or ""))

    def _transliterate_arabic_text(self, text):
        base_map = {
            "ا": "a",
            "أ": "e",
            "إ": "i",
            "آ": "a",
            "ٱ": "a",
            "ب": "b",
            "ت": "t",
            "ث": "s",
            "ج": "c",
            "ح": "h",
            "خ": "h",
            "د": "d",
            "ذ": "z",
            "ر": "r",
            "ز": "z",
            "س": "s",
            "ش": "ş",
            "ص": "s",
            "ض": "d",
            "ط": "t",
            "ظ": "z",
            "ع": "a",
            "غ": "g",
            "ف": "f",
            "ق": "g",
            "ك": "k",
            "ل": "l",
            "م": "m",
            "ن": "n",
            "ه": "h",
            "ة": "e",
            "و": "v",
            "ي": "y",
            "ى": "a",
            "ئ": "i",
            "ؤ": "u",
            "ء": "",
        }
        vowel_map = {
            "َ": "a",
            "ِ": "i",
            "ُ": "u",
            "ً": "",
            "ٍ": "",
            "ٌ": "",
            "ْ": "",
        }
        punctuation_map = str.maketrans({
            "،": " ",
            "؛": " ",
            "؟": " ",
            "ـ": "",
            "(": " ",
            ")": " ",
        })

        text = str(text or "").translate(punctuation_map)
        text = re.sub(r"[\u0660-\u0669\d]+", " ", text)

        result = []
        i = 0
        while i < len(text):
            char = text[i]

            if char == "ّ":
                if result:
                    result.append(result[-1])
                i += 1
                continue

            if char in vowel_map:
                result.append(vowel_map[char])
                i += 1
                continue

            if char == "ا" and result and result[-1].endswith("a"):
                result.append("a")
                i += 1
                continue

            if char == "و":
                prev = result[-1] if result else ""
                next_char = text[i + 1] if i + 1 < len(text) else ""
                if prev.endswith("u"):
                    result.append("u")
                    i += 1
                    continue
                if next_char in {"َ", "ِ", "ُ"}:
                    result.append("v")
                else:
                    result.append("u" if not prev else "v")
                i += 1
                continue

            if char == "ي":
                prev = result[-1] if result else ""
                next_char = text[i + 1] if i + 1 < len(text) else ""
                if prev.endswith("i"):
                    result.append("i")
                elif prev.endswith("a"):
                    result.append("y")
                elif next_char in {"َ", "ِ", "ُ"}:
                    result.append("y")
                else:
                    result.append("i" if not prev else "y")
                i += 1
                continue

            if char in base_map:
                result.append(base_map[char])
            else:
                result.append(char)

            i += 1

        transliterated = "".join(result)
        transliterated = re.sub(r"\s+", " ", transliterated)
        transliterated = re.sub(r"aa+", "aa", transliterated)
        transliterated = re.sub(r"ii+", "ii", transliterated)
        transliterated = re.sub(r"uu+", "uu", transliterated)
        transliterated = re.sub(r"\balşş", "eşş", transliterated, flags=re.IGNORECASE)
        transliterated = re.sub(r"\bvalss", "vess", transliterated, flags=re.IGNORECASE)
        transliterated = re.sub(r"\bguray", "gurey", transliterated, flags=re.IGNORECASE)
        transliterated = re.sub(r"\bkuray", "kurey", transliterated, flags=re.IGNORECASE)
        transliterated = re.sub(r"\bgureyşi\b", "gureyş", transliterated, flags=re.IGNORECASE)
        transliterated = re.sub(r"\bliilafi\b", "liilefi", transliterated, flags=re.IGNORECASE)
        transliterated = re.sub(r"\biilafihim\b", "iilefihim", transliterated, flags=re.IGNORECASE)
        transliterated = re.sub(r"\brihlaea\b", "rihlete", transliterated, flags=re.IGNORECASE)
        return transliterated.strip()

    def _initial_speech_status_text(self):
        if self.speech_engine.is_available():
            return "Çevrimdışı Türkçe ses hazır."

        last_error = self.speech_engine.get_last_error()
        if last_error:
            return f"Ses sistemi hazır değil: {last_error}"
        return "Türkçe ses modeli bulunamadı."

    def update_speech_rate_label(self, *_):
        if hasattr(self, "speech_rate_value_var"):
            self.speech_rate_value_var.set(
                f"Okuma Hızı: {self.speech_rate_var.get():.2f}x"
            )

    def update_speech_wait_label(self, *_):
        if hasattr(self, "speech_wait_value_var"):
            self.speech_wait_value_var.set(
                f"Sonraki soruya geçiş: {int(self.speech_wait_ms_var.get())} ms"
            )

    def _set_speech_status(self, text):
        if hasattr(self, "speech_status_var"):
            self.speech_status_var.set(text)

    def _selected_speech_voice_id(self):
        if not self.speech_voice_choices:
            return None
        selected_label = self.speech_voice_var.get()
        voice_id = self.speech_voice_map.get(selected_label)
        if voice_id:
            return voice_id
        return self.speech_voice_choices[0][0]

    def _speech_finish_buffer_seconds(self, text):
        raw_text = str(text or "")
        sentence_breaks = len(re.findall(r"[.!?;:…]", raw_text))
        arabic_bonus = 0.55 if self._contains_arabic_text(raw_text) else 0.0
        length_bonus = min(1.2, len(raw_text) / 180.0)
        return 0.65 + arabic_bonus + length_bonus + (sentence_breaks * 0.08)

    def _normalize_speech_text(self, text):
        normalized = normalize_sentence_for_tts(str(text or "").replace("\n", " "))
        normalized = self._replace_roman_numerals_for_speech(normalized)
        abbreviation_rules = [
            (r"\bHz\.\s*", "Hazreti "),
            (r"\bM\.\s*Ö\.\s*", "milattan önce "),
            (r"\bM\.\s*S\.\s*", "milattan sonra "),
            (r"\b(?:s\.a\.v\.|s\.a\.s\.|sav\.|sas\.)\s*", "sallallahu aleyhi ve sellem "),
            (r"\b(?:r\.a\.|ra\.)\s*", "radıyallahu anh "),
            (r"\b(?:a\.s\.|as\.)\s*", "aleyhisselam "),
            (r"\b(?:k\.s\.|ks\.)\s*", "kuddise sirruhu "),
            (r"\b(?:c\.c\.|cc\.)\s*", "celle celaluhu "),
        ]
        for pattern, replacement in abbreviation_rules:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        normalized = re.sub(
            r"(?<=[A-Za-zÇĞİÖŞÜçğıöşü])\s+b\.\s+(?=[A-Za-zÇĞİÖŞÜçğıöşü])",
            " bin ",
            normalized,
        )
        if self._contains_arabic_text(normalized):
            normalized = self._transliterate_arabic_text(normalized)
        return " ".join(normalized.split())

    def _option_read_label(self, option_letter):
        option_names = {
            "A": "A",
            "B": "Be",
            "C": "Ce",
            "D": "De",
            "E": "E",
        }
        return option_names.get(option_letter, option_letter)

    def build_question_audio_text(self, question, include_question=True, include_options=False):
        parts = []

        if include_question:
            question_text = self._normalize_speech_text(question.get("soru_metni", ""))
            if question_text:
                parts.append(
                    f"Soru {question.get('soru_no', self.current_index + 1)}: {question_text}"
                )

        if include_options:
            for option_letter in ("A", "B", "C", "D", "E"):
                option_text = question.get("siklar", {}).get(option_letter)
                if option_text:
                    parts.append(
                        f"{self._option_read_label(option_letter)} şıkkı. "
                        f"{self._normalize_speech_text(option_text)}"
                    )

        return " ".join(part for part in parts if part)

    def build_answer_audio_text(self, question):
        correct_option = question.get("dogru_cevap")
        correct_text = question.get("siklar", {}).get(correct_option, "")
        if not correct_option or not correct_text:
            return "Bu soru için doğru cevap bilgisi bulunamadı."

        return (
            f"Doğru cevap {self._option_read_label(correct_option)} şıkkı. "
            f"{self._normalize_speech_text(correct_text)}"
        )

    def _cancel_speech_sequence(self):
        self._speech_sequence_token += 1
        if self._speech_sequence_job:
            try:
                self.root.after_cancel(self._speech_sequence_job)
            except Exception:
                pass
            self._speech_sequence_job = None

    def _is_sequence_token_current(self, token):
        return token == self._speech_sequence_token

    def _schedule_sequence_step(self, delay_ms, token, callback):
        if not self._is_sequence_token_current(token):
            return

        def _run():
            self._speech_sequence_job = None
            if self._is_sequence_token_current(token):
                callback()

        self._speech_sequence_job = self.root.after(max(0, int(delay_ms)), _run)

    def _auto_read_is_enabled(self):
        return any([
            self.speech_read_question_var.get(),
            self.speech_read_options_var.get(),
            self.speech_read_answer_var.get(),
        ])

    def speak_text(self, text, status_prefix="Ses okunuyor", on_finished=None, sequence_token=None):
        text = self._normalize_speech_text(text)
        voice_id = self._selected_speech_voice_id()
        if not voice_id:
            self._set_speech_status("Türkçe ses modeli bulunamadı.")
            return

        self._set_speech_status(f"{status_prefix}...")

        def on_ready(_, duration_seconds):
            self.root.after(
                0,
                lambda: self._set_speech_status(
                    f"{status_prefix}. Durdur ile kesebilirsin."
                ),
            )
            if on_finished:
                extra_buffer = self._speech_finish_buffer_seconds(text)
                delay_ms = int(max(0.6, duration_seconds + extra_buffer) * 1000)
                token = sequence_token if sequence_token is not None else self._speech_sequence_token
                self.root.after(
                    0,
                    lambda: self._schedule_sequence_step(delay_ms, token, on_finished),
                )

        def on_error(error_message):
            self.root.after(
                0,
                lambda: self._set_speech_status(f"Ses hatası: {error_message}"),
            )
            if on_finished:
                token = sequence_token if sequence_token is not None else self._speech_sequence_token
                self.root.after(
                    0,
                    lambda: self._schedule_sequence_step(400, token, on_finished),
                )

        started = self.speech_engine.speak(
            text,
            voice_id=voice_id,
            speed_value=self.speech_rate_var.get(),
            on_ready=on_ready,
            on_error=on_error,
        )
        if not started:
            self._set_speech_status("Ses başlatılamadı.")
            if on_finished:
                token = sequence_token if sequence_token is not None else self._speech_sequence_token
                self._schedule_sequence_step(400, token, on_finished)

    def stop_speech(self, reset_status=True, cancel_sequence=True):
        if cancel_sequence:
            self._cancel_speech_sequence()
        self.speech_engine.stop()
        if reset_status:
            if self.current_view == "question" and self._auto_read_is_enabled():
                self._set_speech_status("Ses durduruldu. Devam Et ile bu sorudan tekrar baslayip test sonuna kadar ilerler.")
            else:
                self._set_speech_status(self._initial_speech_status_text())

    def resume_auto_read(self):
        if self.current_view != "question" or not getattr(self, "quiz_questions", None):
            self._set_speech_status("Devam etmek icin once aktif bir soru acin.")
            return

        if not self._auto_read_is_enabled():
            self._set_speech_status("Otomatik devam icin soldaki Soru, Siklar veya Cevap seceneklerinden en az biri acik olmali.")
            return

        if self.current_index >= len(self.quiz_questions):
            self._set_speech_status("Aktif soru bulunamadi.")
            return

        question = self.quiz_questions[self.current_index]
        self.maybe_auto_read_question(question)

    def preview_speech_voice(self):
        sample_text = (
            "Merhaba. Bu uygulama soruları Türkçe, çevrimdışı ve ayarlanabilir hızla okuyabilir."
        )
        self.speak_text(sample_text, status_prefix="Türkçe ses testi oynatılıyor")

    def maybe_auto_read_question(self, question):
        if self.current_view != "question":
            return

        if not self._auto_read_is_enabled():
            self._set_speech_status(self._initial_speech_status_text())
            return

        self._cancel_speech_sequence()
        sequence_token = self._speech_sequence_token
        first_text = self.build_question_audio_text(
            question,
            include_question=self.speech_read_question_var.get(),
            include_options=self.speech_read_options_var.get(),
        )

        if first_text:
            self.speak_text(
                first_text,
                status_prefix="Otomatik okuma sürüyor",
                on_finished=lambda q=question, t=sequence_token: self._continue_auto_read_sequence(q, t),
                sequence_token=sequence_token,
            )
        else:
            self._continue_auto_read_sequence(question, sequence_token)

    def _store_user_answer(self, question, selected_option):
        if not hasattr(self, 'user_answers'):
            self.user_answers = []

        answer_data = {
            'question': question,
            'selected_option': selected_option,
            'correct_option': question['dogru_cevap'],
            'is_correct': selected_option == question['dogru_cevap']
        }

        for existing_answer in self.user_answers:
            if (
                existing_answer['question']['yil'] == question['yil']
                and existing_answer['question']['soru_no'] == question['soru_no']
                and existing_answer['question']['ders'] == question['ders']
            ):
                existing_answer.update(answer_data)
                return existing_answer

        self.user_answers.append(answer_data)
        return answer_data

    def _auto_mark_correct_answer(self, question):
        correct_option = question['dogru_cevap']
        correct_button_num = next(
            (option_num for option_num, option_key in self.option_map.items() if option_key == correct_option),
            None,
        )
        if correct_button_num is None:
            return

        already_answered = any(
            item['question']['yil'] == question['yil']
            and item['question']['soru_no'] == question['soru_no']
            and item['question']['ders'] == question['ders']
            for item in self.test_history
        )

        self.update_test_history(question, correct_option)
        self._store_user_answer(question, correct_option)

        for key, var in self.option_vars.items():
            var.set("")
            self.option_buttons[key].config(bg=self.colors['border'], fg=self.colors['text'])

        self.option_vars[correct_button_num].set(correct_button_num)
        self.option_buttons[correct_button_num].config(bg=self.colors['success'], fg='white')

        if self._quiz_mode() == "Anında Cevap":
            if not already_answered:
                self.score += 1

    def _continue_auto_read_sequence(self, question, sequence_token):
        if not self._is_sequence_token_current(sequence_token):
            return

        if self.speech_read_answer_var.get():
            self._auto_mark_correct_answer(question)
            self.speak_text(
                self.build_answer_audio_text(question),
                status_prefix="Doğru cevap okunuyor",
                on_finished=lambda q=question, t=sequence_token: self._advance_after_auto_read(q, t),
                sequence_token=sequence_token,
            )
        else:
            self._advance_after_auto_read(question, sequence_token)

    def _advance_after_auto_read(self, question, sequence_token):
        if not self._is_sequence_token_current(sequence_token):
            return

        def _move_next():
            if not self._is_sequence_token_current(sequence_token):
                return

            if self.current_index < len(self.quiz_questions) - 1:
                self.current_index += 1
                self.show_question()
            else:
                if self._uses_review_flow():
                    self.show_review_screen()
                else:
                    self.show_results()

        self._schedule_sequence_step(self.speech_wait_ms_var.get(), sequence_token, _move_next)

    def speak_question_only(self, question):
        self.speak_text(
            self.build_question_audio_text(question, include_question=True, include_options=False),
            status_prefix="Soru okunuyor",
        )

    def speak_question_and_options(self, question):
        self.speak_text(
            self.build_question_audio_text(question, include_question=True, include_options=True),
            status_prefix="Soru ve şıklar okunuyor",
        )

    def speak_correct_answer(self, question):
        self.speak_text(
            self.build_answer_audio_text(question),
            status_prefix="Doğru cevap okunuyor",
        )

    def speak_answer_feedback(self, question, is_correct):
        if not self.speech_read_answer_var.get():
            return

        result_text = "Cevabın doğru." if is_correct else "Cevabın yanlış."
        speech_text = f"{result_text} {self.build_answer_audio_text(question)}"
        self.speak_text(speech_text, status_prefix="Cevap geri bildirimi okunuyor")

    def create_speech_controls(self, parent, question, include_navigation=False):
        speech_frame = tk.Frame(parent, bg=self.colors['card'], relief=tk.RIDGE, bd=1)
        speech_frame.pack(fill=tk.X, pady=(0, 15))

        header_frame = tk.Frame(speech_frame, bg=self.colors['card'])
        header_frame.pack(fill=tk.X, padx=12, pady=(10, 6))

        tk.Label(
            header_frame,
            text="🔊 Sesli Okuma",
            font=('Segoe UI', 9, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card'],
        ).pack(side=tk.LEFT)

        tk.Label(
            header_frame,
            textvariable=self.speech_status_var,
            font=('Segoe UI', 8),
            fg=self.colors['text_secondary'],
            bg=self.colors['card'],
            wraplength=360,
            justify=tk.RIGHT,
        ).pack(side=tk.RIGHT)

        buttons_frame = tk.Frame(speech_frame, bg=self.colors['card'])
        buttons_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        actions = [
            ("Soruyu Oku", lambda q=question: self.speak_question_only(q), self.colors['accent']),
            ("Soru + Şıklar", lambda q=question: self.speak_question_and_options(q), self.colors['primary']),
            ("Cevabı Oku", lambda q=question: self.speak_correct_answer(q), self.colors['warning']),
            ("Devam Et", self.resume_auto_read, self.colors['success']),
            ("Durdur", self.stop_speech, self.colors['danger']),
        ]

        controls_enabled = self.speech_engine.is_available()
        for text, command, color in actions:
            button = self.create_button(buttons_frame, text, command, color)
            button.pack(side=tk.LEFT, padx=(0, 8), ipadx=4, ipady=3)
            if not controls_enabled:
                button.config(state=tk.DISABLED, cursor="arrow")

        if include_navigation:
            self.create_compact_question_navigation(buttons_frame)

    def create_compact_question_navigation(self, parent):
        if not getattr(self, 'quiz_questions', None):
            return

        nav_shell = tk.Frame(parent, bg=self.colors['card'])
        nav_shell.pack(side=tk.LEFT, padx=(4, 0))

        tk.Frame(
            nav_shell,
            bg=self.colors['border'],
            width=1,
            height=28,
        ).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=2)

        nav_frame = tk.Frame(nav_shell, bg=self.colors['card'])
        nav_frame.pack(side=tk.LEFT)

        compact_font = ('Segoe UI', 8, 'bold')
        compact_padx = 8
        compact_pady = 5

        if self.current_index > 0:
            prev_btn = self.create_button(
                nav_frame, "<", self.previous_question, self.colors['text_secondary']
            )
            prev_btn.config(font=compact_font, padx=compact_padx, pady=compact_pady)
            prev_btn.pack(side=tk.LEFT, padx=(0, 4), ipady=1)

        tk.Label(
            nav_frame,
            text=f"Soru {self.current_index + 1}/{self.total_questions}",
            font=('Segoe UI', 8, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text'],
        ).pack(side=tk.LEFT, padx=(0, 4))

        if self.current_index < len(self.quiz_questions) - 1:
            next_btn = self.create_button(
                nav_frame, ">", self.next_question, self.colors['success']
            )
            next_btn.config(font=compact_font, padx=compact_padx, pady=compact_pady)
            next_btn.pack(side=tk.LEFT, padx=(0, 4), ipady=1)
        else:
            finish_command = self.show_results
            if self._uses_review_flow():
                finish_command = self.show_review_screen

            finish_btn = self.create_button(
                nav_frame, "Bitir", finish_command, self.colors['accent']
            )
            finish_btn.config(font=compact_font, padx=compact_padx, pady=compact_pady)
            finish_btn.pack(side=tk.LEFT, padx=(0, 4), ipady=1)

        if self._uses_review_flow():
            finish_test_btn = self.create_button(
                nav_frame, "Testi Bitir", self.confirm_finish_test, self.colors['danger']
            )
            finish_test_btn.config(font=('Segoe UI', 7, 'bold'), padx=7, pady=compact_pady)
            finish_test_btn.pack(side=tk.LEFT, ipady=1)

    def on_close(self):
        self.stop_speech(reset_status=False)
        self.speech_engine.cleanup_all_cache()
        self.root.destroy()

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
            insertcolor=self.colors['text'],
            relief='flat',
            padding=6
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
            background=self.colors['accent'],
            troughcolor=self.colors['bg'],
            bordercolor=self.colors['border'],
            arrowcolor=self.colors['text'],
            darkcolor=self.darken_color(self.colors['accent']),
            lightcolor=self.lighten_color(self.colors['accent']),
            gripcount=0,
            width=10
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
        self.root.after(200, lambda: self.load_questions(show_message=False))

    def rebuild_ui(self):
        """Tema degisimi sonrasi arayuzu koruyarak yeniden kurar."""
        saved = {
            'year': getattr(self, 'year_var', None).get() if hasattr(self, 'year_var') else 'Tum yillar',
            'mode': getattr(self, 'mode_var', None).get() if hasattr(self, 'mode_var') else 'Aninda Cevap',
            'time_hours': getattr(self, 'time_hours_var', None).get() if hasattr(self, 'time_hours_var') else '0',
            'time_minutes': getattr(self, 'time_minutes_var', None).get() if hasattr(self, 'time_minutes_var') else '10',
            'time_seconds': getattr(self, 'time_seconds_var', None).get() if hasattr(self, 'time_seconds_var') else '0',
            'order': getattr(self, 'order_var', None).get() if hasattr(self, 'order_var') else 'Sorular Rastgele',
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
        self._restore_filter_widgets_from_vars()
        self.mode_var.set(saved['mode'])
        self.time_hours_var.set(saved['time_hours'])
        self.time_minutes_var.set(saved['time_minutes'])
        self.time_seconds_var.set(saved['time_seconds'])
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
        header = tk.Frame(parent, bg=self.colors['card'], height=92, highlightthickness=1,
                          highlightbackground=self.colors['border'])
        header.pack(fill=tk.X, padx=22, pady=(22, 12))
        header.pack_propagate(False)

        accent_bar = tk.Frame(header, bg=self.colors['accent'], width=6)
        accent_bar.pack(side=tk.LEFT, fill=tk.Y)

        title_frame = tk.Frame(header, bg=self.colors['card'])
        title_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=18)

        badge = tk.Label(title_frame, text="DKAB ÖABT", font=('Bahnschrift SemiBold', 10),
                         fg=self.colors['accent'], bg=self.colors['card'])
        badge.pack(anchor=tk.W, pady=(12, 0))

        title_label = tk.Label(
            title_frame,
            text="Pratik Sınav Paneli",
            font=self.fonts['title'],
            fg=self.colors['text'],
            bg=self.colors['card']
        )
        title_label.pack(anchor=tk.W)

        subtitle_label = tk.Label(
            title_frame,
            text="2013-2025 Din Kültürü ve Ahlak Bilgisi Öğretmenliği soru çalışma alanı",
            font=self.fonts['subtitle'],
            fg=self.colors['text_secondary'],
            bg=self.colors['card']
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 12))

        status_wrap = tk.Frame(header, bg=self.colors['primary'], highlightthickness=1,
                               highlightbackground=self.colors['border'])
        status_wrap.pack(side=tk.RIGHT, padx=18, pady=18)

        self.status_label = tk.Label(
            status_wrap,
            text="🔴 Hazır Değil",
            font=self.fonts['button'],
            fg=self.colors['danger'],
            bg=self.colors['primary'],
            padx=14,
            pady=10
        )
        self.status_label.pack()
        
    def create_sidebar(self, parent):
        """Sol sidebar oluşturur (Kaydırılabilir)"""
        sidebar_outer = tk.Frame(parent, bg=self.colors['card'], width=284, highlightthickness=1,
                                 highlightbackground=self.colors['border'])
        sidebar_outer.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        sidebar_outer.pack_propagate(False)
        
        self.sidebar_canvas = tk.Canvas(sidebar_outer, bg=self.colors['card'], highlightthickness=0, width=262)
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
        
        self.year_var = tk.StringVar(value=ALL_YEARS_LABEL)
        self.year_display_var = tk.StringVar(value=ALL_YEARS_LABEL)
        self.year_filter = MultiSelectFilter(
            settings_card,
            textvariable=self.year_display_var,
            all_label=ALL_YEARS_LABEL,
            values=[],
            command=self._on_year_filter_changed,
            colors=self.colors,
        )
        self.year_filter.pack(padx=5, pady=0, fill=tk.X)

        # Subject selection
        tk.Label(settings_card, text="Ders:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.ders_var = tk.StringVar(value=ALL_DERSLER_LABEL)
        self.ders_display_var = tk.StringVar(value=ALL_DERSLER_LABEL)
        self.ders_filter = MultiSelectFilter(
            settings_card,
            textvariable=self.ders_display_var,
            all_label=ALL_DERSLER_LABEL,
            values=self.available_subjects,
            command=self._on_ders_filter_changed,
            colors=self.colors,
        )
        self.ders_filter.pack(padx=5, pady=0, fill=tk.X)

        # Konu selection
        tk.Label(settings_card, text="Konu:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.konu_var = tk.StringVar(value=ALL_KONULAR_LABEL)
        self.konu_display_var = tk.StringVar(value=ALL_KONULAR_LABEL)
        self.konu_filter = MultiSelectFilter(
            settings_card,
            textvariable=self.konu_display_var,
            all_label=ALL_KONULAR_LABEL,
            values=[],
            command=self._on_konu_filter_changed,
            colors=self.colors,
        )
        self.konu_filter.pack(padx=5, pady=0, fill=tk.X)
        
        # Test mode selection
        tk.Label(settings_card, text="Mod:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.mode_var = tk.StringVar(value="Anında Cevap")
        mode_options = ["Anında Cevap", "Test Sonu Değerlendir", "Süreli"]
        self.mode_combo = ttk.Combobox(settings_card, textvariable=self.mode_var, 
                                      values=mode_options, state="readonly", width=14, style='Modern.TCombobox')
        self.mode_combo.pack(padx=5, pady=0, fill=tk.X)
        self.mode_combo.bind("<<ComboboxSelected>>", self.on_mode_changed)

        tk.Label(settings_card, text="Süre (s/dk/sn):", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.time_hours_var = tk.StringVar(value="0")
        self.time_minutes_var = tk.StringVar(value="10")
        self.time_seconds_var = tk.StringVar(value="0")

        time_frame = tk.Frame(settings_card, bg=self.colors['card'])
        time_frame.pack(padx=5, pady=0, anchor=tk.W)

        self.time_hour_spinbox = tk.Spinbox(time_frame, from_=0, to=23, textvariable=self.time_hours_var,
                                            width=3, font=('Segoe UI', 8), format="%02.0f")
        self.time_hour_spinbox.pack(side=tk.LEFT)
        tk.Label(time_frame, text="s", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT, padx=(2, 6))

        self.time_minute_spinbox = tk.Spinbox(time_frame, from_=0, to=59, textvariable=self.time_minutes_var,
                                              width=3, font=('Segoe UI', 8), format="%02.0f")
        self.time_minute_spinbox.pack(side=tk.LEFT)
        tk.Label(time_frame, text="dk", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT, padx=(2, 6))

        self.time_second_spinbox = tk.Spinbox(time_frame, from_=0, to=59, textvariable=self.time_seconds_var,
                                              width=3, font=('Segoe UI', 8), format="%02.0f")
        self.time_second_spinbox.pack(side=tk.LEFT)
        tk.Label(time_frame, text="sn", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(side=tk.LEFT, padx=(2, 0))

        # Question order selection
        tk.Label(settings_card, text="Sıra:", font=('Segoe UI', 8), 
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))
        
        self.order_var = tk.StringVar(value="Sorular Rastgele")
        order_options = ["Sorular Rastgele", "Şıklar Rastgele", "Ikisi de Rastgele", "Sıralı"]
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

        speech_card = self.create_card(sidebar, "🔊 Sesli Okuma")
        speech_card.pack(fill=tk.X, padx=2, pady=2)

        tk.Label(speech_card, text="Ses:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        voice_labels = [label for _, label in self.speech_voice_choices]
        if not voice_labels:
            voice_labels = [self.speech_engine.get_default_voice_label()]

        self.speech_voice_var = tk.StringVar(value=voice_labels[0])
        self.speech_voice_combo = ttk.Combobox(
            speech_card,
            textvariable=self.speech_voice_var,
            values=voice_labels,
            state="readonly",
            width=18,
            style='Modern.TCombobox'
        )
        self.speech_voice_combo.pack(padx=5, pady=0, fill=tk.X)

        tk.Label(speech_card, text="Test boyunca sırayla oku:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(4, 0))

        speech_tick_frame = tk.Frame(speech_card, bg=self.colors['card'])
        speech_tick_frame.pack(fill=tk.X, padx=5, pady=(2, 2))

        self.speech_read_question_var = tk.BooleanVar(value=True)
        self.speech_read_options_var = tk.BooleanVar(value=False)
        self.speech_read_answer_var = tk.BooleanVar(value=False)

        checkbutton_style = {
            "bg": self.colors['card'],
            "fg": self.colors['text'],
            "activebackground": self.colors['card'],
            "activeforeground": self.colors['text'],
            "selectcolor": self.colors['primary'],
            "anchor": tk.W,
            "font": ('Segoe UI', 8),
            "highlightthickness": 0,
        }

        self.speech_question_check = tk.Checkbutton(
            speech_tick_frame,
            text="Soru",
            variable=self.speech_read_question_var,
            **checkbutton_style,
        )
        self.speech_question_check.pack(fill=tk.X)

        self.speech_options_check = tk.Checkbutton(
            speech_tick_frame,
            text="Şıklar",
            variable=self.speech_read_options_var,
            **checkbutton_style,
        )
        self.speech_options_check.pack(fill=tk.X)

        self.speech_answer_check = tk.Checkbutton(
            speech_tick_frame,
            text="Cevap",
            variable=self.speech_read_answer_var,
            **checkbutton_style,
        )
        self.speech_answer_check.pack(fill=tk.X)

        tk.Label(speech_card, text="Okuma hızı:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(4, 0))

        self.speech_rate_var = tk.DoubleVar(value=1.0)
        self.speech_rate_value_var = tk.StringVar(value="Okuma Hızı: 1.00x")
        self.speech_rate_scale = tk.Scale(
            speech_card,
            from_=0.7,
            to=1.6,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.speech_rate_var,
            showvalue=False,
            highlightthickness=0,
            bg=self.colors['card'],
            fg=self.colors['text'],
            troughcolor=self.colors['primary'],
            activebackground=self.colors['accent']
        )
        self.speech_rate_scale.pack(padx=5, pady=(0, 0), fill=tk.X)
        self.speech_rate_var.trace_add("write", self.update_speech_rate_label)

        tk.Label(speech_card, textvariable=self.speech_rate_value_var, font=('Segoe UI', 8),
                fg=self.colors['text_secondary'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(0, 4))

        tk.Label(speech_card, text="Bekleme süresi:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(2, 0))

        self.speech_wait_ms_var = tk.IntVar(value=450)
        self.speech_wait_value_var = tk.StringVar(value="Sonraki soruya geçiş: 450 ms")
        self.speech_wait_scale = tk.Scale(
            speech_card,
            from_=0,
            to=5000,
            resolution=250,
            orient=tk.HORIZONTAL,
            variable=self.speech_wait_ms_var,
            showvalue=False,
            highlightthickness=0,
            bg=self.colors['card'],
            fg=self.colors['text'],
            troughcolor=self.colors['primary'],
            activebackground=self.colors['accent']
        )
        self.speech_wait_scale.pack(padx=5, pady=(0, 0), fill=tk.X)
        self.speech_wait_ms_var.trace_add("write", self.update_speech_wait_label)

        tk.Label(speech_card, textvariable=self.speech_wait_value_var, font=('Segoe UI', 8),
                fg=self.colors['text_secondary'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(0, 4))

        speech_buttons = tk.Frame(speech_card, bg=self.colors['card'])
        speech_buttons.pack(fill=tk.X, padx=5, pady=(0, 4))

        self.preview_voice_button = self.create_button(
            speech_buttons,
            "Sesi Test Et",
            self.preview_speech_voice,
            self.colors['accent']
        )
        self.preview_voice_button.config(font=('Segoe UI', 7, 'bold'), padx=6, pady=5)
        self.preview_voice_button.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=1)

        self.resume_voice_button = self.create_button(
            speech_buttons,
            "Devam Et",
            self.resume_auto_read,
            self.colors['success']
        )
        self.resume_voice_button.config(font=('Segoe UI', 7, 'bold'), padx=6, pady=5)
        self.resume_voice_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=1)

        self.stop_voice_button = self.create_button(
            speech_buttons,
            "Durdur",
            self.stop_speech,
            self.colors['danger']
        )
        self.stop_voice_button.config(font=('Segoe UI', 7, 'bold'), padx=6, pady=5)
        self.stop_voice_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=1)

        tk.Label(speech_card, textvariable=self.speech_status_var, font=('Segoe UI', 7),
                fg=self.colors['text_secondary'], bg=self.colors['card'],
                wraplength=200, justify=tk.LEFT).pack(padx=5, pady=(0, 4), fill=tk.X)

        if not self.speech_engine.is_available():
            self.speech_voice_combo.config(state="disabled")
            self.speech_question_check.config(state=tk.DISABLED)
            self.speech_options_check.config(state=tk.DISABLED)
            self.speech_answer_check.config(state=tk.DISABLED)
            self.speech_rate_scale.config(state=tk.DISABLED)
            self.speech_wait_scale.config(state=tk.DISABLED)
            self.preview_voice_button.config(state=tk.DISABLED, cursor="arrow")
            self.resume_voice_button.config(state=tk.DISABLED, cursor="arrow")
            self.stop_voice_button.config(state=tk.DISABLED, cursor="arrow")
        
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

        self.goto_year_var = tk.StringVar(value="")
        goto_years = []
        self.goto_year_combo = ttk.Combobox(goto_card, textvariable=self.goto_year_var,
                                            values=goto_years, state="readonly", width=14, style='Modern.TCombobox')
        self.goto_year_combo.pack(padx=5, pady=0, fill=tk.X)
        self.goto_year_combo.bind("<<ComboboxSelected>>", self._on_goto_filter_changed)

        tk.Label(goto_card, text="Ders:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.goto_ders_var = tk.StringVar(value="")
        self.goto_ders_combo = ttk.Combobox(goto_card, textvariable=self.goto_ders_var,
                                            values=self.available_subjects, state="readonly", width=14, style='Modern.TCombobox')
        self.goto_ders_combo.pack(padx=5, pady=0, fill=tk.X)
        self.goto_ders_combo.bind("<<ComboboxSelected>>", self._on_goto_filter_changed)

        tk.Label(goto_card, text="Soru No:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['card']).pack(anchor=tk.W, padx=5, pady=(3, 0))

        self.goto_q_var = tk.StringVar(value="1")
        self.goto_q_combo = ttk.Combobox(goto_card, textvariable=self.goto_q_var,
                                         values=[str(i) for i in range(1, 76)],
                                         state="normal", width=14, style='Modern.TCombobox')
        self.goto_q_combo.pack(padx=5, pady=0, fill=tk.X)

        self.goto_hint_label = tk.Label(
            goto_card,
            text="",
            font=('Segoe UI', 7),
            fg=self.colors['text_secondary'],
            bg=self.colors['card'],
            wraplength=180,
            justify=tk.LEFT,
        )
        self.goto_hint_label.pack(anchor=tk.W, padx=5, pady=(2, 4), fill=tk.X)

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

        # --- Kodlamalı Özet Kartı ---
        ozet_card = self.create_card(sidebar, "📝 Özet Notlar")
        ozet_card.pack(fill=tk.X, padx=2, pady=2)
        
        ozet_btn = self.create_button(ozet_card, "📖 Kodlamalı Özet",
                                      self.show_kodlamali_ozet, self.colors['success'])
        ozet_btn.pack(padx=5, pady=(5, 2), fill=tk.X, ipady=2)

        ozet2_btn = self.create_button(ozet_card, "📄 DKAB Özet",
                                       self.show_ozet, self.colors['accent'])
        ozet2_btn.pack(padx=5, pady=(0, 5), fill=tk.X, ipady=2)

        self.on_mode_changed()
        
    def create_main_content(self, parent):
        """Ana içerik alanı oluşturur (Kaydırılabilir)"""
        self.main_container = tk.Frame(parent, bg=self.colors['card'], highlightthickness=1,
                                       highlightbackground=self.colors['border'])
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

    def _start_countdown(self, total_seconds):
        """Süreli test için geri sayımı başlatır."""
        self._stop_countdown()
        self.remaining_seconds = max(0, int(total_seconds))
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
        if not hasattr(self, "time_hour_spinbox"):
            return

        spinbox_state = "normal" if self.mode_var.get() == "Süreli" else "disabled"
        self.time_hour_spinbox.config(state=spinbox_state)
        self.time_minute_spinbox.config(state=spinbox_state)
        self.time_second_spinbox.config(state=spinbox_state)
        self._set_status_ready()

    def create_card(self, parent, title):
        """Modern kart oluşturur"""
        card = tk.Frame(parent, bg=self.colors['card'], bd=0, highlightthickness=1,
                        highlightbackground=self.colors['border'])
        
        header = tk.Frame(card, bg=self.colors['primary'], height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        accent = tk.Frame(header, bg=self.colors['accent'], width=4)
        accent.pack(side=tk.LEFT, fill=tk.Y)

        title_label = tk.Label(
            header,
            text=title,
            font=('Bahnschrift SemiBold', 10),
            fg=self.colors['text'],
            bg=self.colors['primary']
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=4)
        
        return card
        
    def create_button(self, parent, text, command, color):
        """Modern buton oluşturur"""
        button = tk.Button(parent, text=text, command=command,
                          font=self.fonts['button'],
                          bg=color, fg=self.colors['text'],
                          relief=tk.FLAT, cursor="hand2",
                          bd=0, padx=14, pady=10,
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
        color = color.lstrip('#')
        r = min(255, int(color[0:2], 16) + 18)
        g = min(255, int(color[2:4], 16) + 18)
        b = min(255, int(color[4:6], 16) + 18)
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def darken_color(self, color):
        """Rengi koyulaştırır"""
        color = color.lstrip('#')
        r = max(0, int(color[0:2], 16) - 18)
        g = max(0, int(color[2:4], 16) - 18)
        b = max(0, int(color[4:6], 16) - 18)
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def show_welcome_screen(self):
        self.current_view = "welcome"
        self.stop_speech(reset_status=False)
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

        hero = tk.Frame(content_frame, bg=self.colors['primary'], highlightthickness=1,
                        highlightbackground=self.colors['border'])
        hero.pack(fill=tk.X, padx=16, pady=(8, 18))

        tk.Label(
            hero,
            text="DKAB ÖABT PRATİK SINAVINA HOŞ GELDİNİZ",
            font=self.fonts['header'],
            bg=self.colors['primary'],
            fg=self.colors['text']
        ).pack(anchor=tk.W, padx=20, pady=(18, 6))

        tk.Label(
            hero,
            text="Soruları hızlıca filtreleyin, süreli test çözün ve sonuçları net biçimde değerlendirin.",
            font=self.fonts['body'],
            bg=self.colors['primary'],
            fg=self.colors['text_secondary'],
            justify=tk.LEFT
        ).pack(anchor=tk.W, padx=20, pady=(0, 18))

        welcome_text = (
            "Özellikler:\n"
            "• Daha temiz ve odaklı çalışma ekranı\n"
            "• Sorulari, siklari veya ikisini birden rastgele karistirma\n"
            "• Yıl ve konu bazlı filtreleme\n"
            "• Anında cevap ve süreli test desteği\n"
            "• Açıklama, süre ve performans takibi\n\n"
            "Başlamak için:\n"
            "1. Sol panelden filtreleri seçin\n"
            "2. Soru sayısını belirleyin\n"
            "3. \"BAŞLAT\" düğmesiyle teste girin"
        )

        welcome_label = tk.Label(
            content_frame,
            text=welcome_text,
            font=self.fonts['body'],
            bg=self.colors['card'],
            fg=self.colors['text'],
            justify=tk.LEFT,
            anchor=tk.NW
        )
        welcome_label.pack(fill=tk.BOTH, expand=True, padx=22, pady=(6, 24))
        
    def show_ozet(self):
        """DKAB Ozet dosyasini gosterir (dkab_ozet.txt)"""
        self._show_ozet_file(
            filename="dkab_ozet.txt",
            title="📄 DKAB Özet Notlar",
            view_name="ozet",
        )

    def show_kodlamali_ozet(self):
        """DKAB Kodlamali Ozet dosyasini gosterir (dkab_kodlamali_ozet.txt)"""
        self._show_ozet_file(
            filename="dkab_kodlamali_ozet.txt",
            title="📝 DKAB Kodlamalı Özet",
            view_name="kodlamali_ozet",
        )

    def _turkish_upper(self, text: str) -> str:
        return str(text or "").replace("i", "İ").replace("ı", "I").upper()

    def _load_ozet_parser_result(self, ozet_file: Path, file_content: str):
        try:
            parsed = parse_topic_text_file(ozet_file)
        except Exception as exc:
            parsed = {
                "topic_blocks": [],
                "main_section_to_topics": {},
                "main_section_counts": {},
                "topic_counts": {},
                "warnings": [f"Özet ayrıştırılamadı: {exc}"],
            }

        topic_blocks = list(parsed.get("topic_blocks", []))
        if not topic_blocks and file_content.strip():
            topic_blocks = [
                {
                    "topic": "Giriş / Genel",
                    "main_cat": "Diğer",
                    "main_section": "Diğer",
                    "sentences": [{"raw": file_content.strip(), "norm": file_content.strip()}],
                    "mapped_topics": [],
                    "start_line": 1,
                }
            ]

        return (
            topic_blocks,
            dict(parsed.get("main_section_to_topics", {})),
            dict(parsed.get("main_section_counts", {})),
            dict(parsed.get("topic_counts", {})),
            list(parsed.get("warnings", [])),
        )

    def _summary_exam_family_for_subject(self, subject: str) -> str:
        normalized_subject = format_exam_subject_label(str(subject or ""))
        if normalized_subject == "DKAB":
            return "ÖABT"
        if normalized_subject == "IHL":
            return "İHL"
        if normalized_subject == "MBSTS":
            return "MBSTS"
        if normalized_subject.startswith("DHBT"):
            return "DHBT"
        return ""

    def _ensure_summary_exam_index(self):
        source_questions = list(self.questions)
        if not source_questions:
            try:
                source_questions, _, _ = load_question_bank(
                    base_dir=WORDE_DIR,
                    default_topic=None,
                    visual_resolver=self.resolve_visual_path,
                )
            except Exception:
                source_questions = []

        cache_key = tuple(
            sorted(
                (
                    str(question.get("yil", "")),
                    str(question.get("ders", "")),
                    str(question.get("konu", "")),
                )
                for question in source_questions
            )
        )
        if cache_key == self._summary_exam_index_key:
            return

        topic_to_exam_families: Dict[str, Set[str]] = {}
        topic_to_question_refs: Dict[str, Dict[str, List[Dict[str, object]]]] = {}
        for question in source_questions:
            topic_name = catalog_normalize_topic_name(question.get("konu", ""))
            exam_family = self._summary_exam_family_for_subject(question.get("ders", ""))
            if not topic_name or not exam_family:
                continue
            topic_to_exam_families.setdefault(topic_name, set()).add(exam_family)
            topic_to_question_refs.setdefault(topic_name, {}).setdefault(exam_family, []).append(
                {
                    "yil": question.get("yil"),
                    "soru_no": question.get("soru_no"),
                    "ders": str(question.get("ders", "") or ""),
                }
            )

        for family_map in topic_to_question_refs.values():
            for ref_list in family_map.values():
                ref_list.sort(
                    key=lambda item: (
                        int(item.get("yil", 0) or 0),
                        str(item.get("ders", "")),
                        int(item.get("soru_no", 0) or 0),
                    )
                )

        self._summary_exam_families_by_topic = topic_to_exam_families
        self._summary_question_refs_by_topic = topic_to_question_refs
        self._summary_exam_index_key = cache_key

    def _summary_topics_for_block(self, block: Dict) -> List[str]:
        topics: List[str] = []
        candidates = list(block.get("mapped_topics", []))
        candidates.extend(map_summary_heading_to_topics(block.get("topic", "")))
        candidates.extend(map_summary_heading_to_topics(block.get("main_cat", "")))

        seen = set()
        for candidate in candidates:
            normalized = catalog_normalize_topic_name(candidate)
            if normalized and normalized not in seen:
                topics.append(normalized)
                seen.add(normalized)
        return topics

    def _summary_exam_badges_for_block(self, block: Dict) -> List[str]:
        self._ensure_summary_exam_index()

        found_families = set()
        for topic_name in self._summary_topics_for_block(block):
            found_families.update(self._summary_exam_families_by_topic.get(topic_name, set()))

        return [family for family in SUMMARY_EXAM_FAMILY_ORDER if family in found_families]

    def _summary_question_refs_for_block(self, block: Dict) -> Dict[str, List[Dict[str, object]]]:
        self._ensure_summary_exam_index()

        grouped_refs: Dict[str, List[Dict[str, object]]] = {}
        seen_keys = set()

        for topic_name in self._summary_topics_for_block(block):
            family_map = self._summary_question_refs_by_topic.get(topic_name, {})
            for family, ref_list in family_map.items():
                for ref in ref_list:
                    ref_key = (
                        family,
                        ref.get("ders"),
                        ref.get("yil"),
                        ref.get("soru_no"),
                    )
                    if ref_key in seen_keys:
                        continue
                    grouped_refs.setdefault(family, []).append(ref)
                    seen_keys.add(ref_key)

        for ref_list in grouped_refs.values():
            ref_list.sort(
                key=lambda item: (
                    int(item.get("yil", 0) or 0),
                    str(item.get("ders", "")),
                    int(item.get("soru_no", 0) or 0),
                )
            )

        return grouped_refs

    def _format_summary_ref_entry(self, family: str, ref: Dict[str, object]) -> str:
        year = ref.get("yil", "?")
        question_no = ref.get("soru_no", "?")
        subject = format_exam_subject_label(str(ref.get("ders", "") or ""))

        if family == "DHBT":
            detail = subject.replace("DHBT ", "", 1).strip() or "Genel"
            detail = detail.replace("Ortak (1-20) (1-20)", "Ortak (1-20)")
            return f"{year} {detail} S{question_no}"
        if family == "ÖABT":
            return f"{year} DKAB S{question_no}"
        if family == "İHL":
            return f"{year} İHL S{question_no}"
        return f"{year} S{question_no}"

    def _show_ozet_reference_panel(self, block: Dict) -> None:
        if not hasattr(self, "ozet_reference_text"):
            return

        heading = str(block.get("topic", "") or block.get("main_cat", "")).strip() or "Seçili Başlık"
        grouped_refs = self._summary_question_refs_for_block(block)

        lines = [f"{heading}"]
        if not grouped_refs:
            lines.append("Bu başlık için eşleşen yıl/soru referansı bulunamadı.")
        else:
            for family in SUMMARY_EXAM_FAMILY_ORDER:
                ref_list = grouped_refs.get(family, [])
                if not ref_list:
                    continue
                entries = ", ".join(self._format_summary_ref_entry(family, ref) for ref in ref_list)
                lines.append(f"{family}: {entries}")

        self.ozet_reference_text.config(state=tk.NORMAL)
        self.ozet_reference_text.delete("1.0", tk.END)
        self.ozet_reference_text.insert("1.0", "\n".join(lines))
        self.ozet_reference_text.config(state=tk.DISABLED)

    def _should_show_summary_badges_for_block(self, block: Dict) -> bool:
        heading_text = ""
        sentences = list(block.get("sentences", []))
        if sentences:
            heading_text = str(sentences[0].get("raw", "")).strip()
        if not heading_text:
            heading_text = str(block.get("topic", "")).strip()
        if not heading_text:
            return False

        if heading_text.startswith(("•", "-", "*", "\uf077", "\uf0b7", "\uf0a7", "\uf0b6")):
            return False

        alpha_chars = [char for char in heading_text if char.isalpha()]
        uppercase_ratio = (
            sum(1 for char in alpha_chars if char.isupper()) / len(alpha_chars)
            if alpha_chars
            else 0
        )
        looks_like_short_label = heading_text.endswith(":") and len(heading_text) <= 90
        looks_like_heading = len(heading_text) <= 80 and not re.search(r"[.!?]", heading_text)

        if block.get("topic") == "Giriş / Genel":
            return bool(alpha_chars) and (uppercase_ratio >= 0.65 or looks_like_heading)

        return looks_like_short_label or (looks_like_heading and uppercase_ratio >= 0.35)

    def _decorate_ozet_text_with_exam_badges(self, text_widget: tk.Text) -> None:
        badge_styles = {
            "DHBT": {"background": self.colors["warning"], "foreground": "#0f172a"},
            "MBSTS": {"background": self.colors["success"], "foreground": "#f8fafc"},
            "ÖABT": {"background": self.colors["accent"], "foreground": "#f8fafc"},
            "İHL": {"background": self.colors["danger"], "foreground": "#f8fafc"},
        }

        for family, style in badge_styles.items():
            text_widget.tag_configure(
                f"exam_badge_{family}",
                font=("Segoe UI", 8, "bold"),
                **style,
            )

        inserted_lines = set()
        text_widget.config(state=tk.NORMAL)
        for block in self.ozet_topic_data:
            start_line = block.get("start_line")
            if not start_line or start_line in inserted_lines:
                continue
            if not self._should_show_summary_badges_for_block(block):
                continue

            badges = self._summary_exam_badges_for_block(block)
            if not badges:
                continue

            inserted_lines.add(start_line)
            text_widget.insert(f"{start_line}.end", "   ")
            for family in badges:
                text_widget.insert(
                    f"{start_line}.end",
                    f" {family} ",
                    (f"exam_badge_{family}",),
                )
                text_widget.insert(f"{start_line}.end", " ")
        text_widget.config(state=tk.DISABLED)

    def _show_ozet_file(self, filename, title, view_name):
        self.current_view = view_name
        self.stop_speech(reset_status=False)
        self._stop_countdown()
        self._stop_elapsed_tracking()
        self.remaining_seconds = 0
        self._set_status_ready()
        
        for widget in self.main_content.winfo_children():
            widget.destroy()
            
        ozet_card = self.create_card(self.main_content, title)
        ozet_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuration frame
        config_frame = tk.Frame(ozet_card, bg=self.colors['card'])
        config_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        tk.Label(config_frame, text="Derslere Git:", font=('Segoe UI', 9, 'bold'), bg=self.colors['card'], fg=self.colors['success']).pack(side=tk.LEFT)
        self.ozet_main_nav_var = tk.StringVar(value="Tümü")
        self.ozet_main_nav_combo = ttk.Combobox(config_frame, textvariable=self.ozet_main_nav_var, state="readonly", width=25, style='Modern.TCombobox')
        self.ozet_main_nav_combo.pack(side=tk.LEFT, padx=(5, 15))

        tk.Label(config_frame, text="Konuya Git:", font=('Segoe UI', 9, 'bold'), bg=self.colors['card'], fg=self.colors['accent']).pack(side=tk.LEFT)
        self.ozet_nav_var = tk.StringVar(value="Tümü")
        self.ozet_nav_combo = ttk.Combobox(config_frame, textvariable=self.ozet_nav_var, state="readonly", width=30, style='Modern.TCombobox')
        self.ozet_nav_combo.pack(side=tk.LEFT, padx=(5, 15))
        
        tk.Label(config_frame, text="Ara:", font=('Segoe UI', 9), bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        self.ozet_search_var = tk.StringVar()
        self.ozet_search_entry = tk.Entry(config_frame, textvariable=self.ozet_search_var, width=20, bg=self.colors['bg'], fg=self.colors['text'], insertbackground=self.colors['text'], relief=tk.FLAT)
        self.ozet_search_entry.pack(side=tk.LEFT, padx=5, ipady=3)
        
        # Audio Configuration frame (moved down)
        audio_config_frame = tk.Frame(ozet_card, bg=self.colors['card'])
        audio_config_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        tk.Label(audio_config_frame, text="Okuma Konusu:", font=('Segoe UI', 9), bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        self.ozet_topic_var = tk.StringVar(value="Tümü")
        self.ozet_topic_combo = ttk.Combobox(audio_config_frame, textvariable=self.ozet_topic_var, state="readonly", width=25, style='Modern.TCombobox')
        self.ozet_topic_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        tk.Label(audio_config_frame, text="Mod:", font=('Segoe UI', 9), bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        self.ozet_mode_var = tk.StringVar(value="Sırayla Oku")
        self.ozet_mode_combo = ttk.Combobox(audio_config_frame, textvariable=self.ozet_mode_var, values=["Sırayla Oku", "Sadece Seçili", "Rastgele Karışık"], state="readonly", width=16, style='Modern.TCombobox')
        self.ozet_mode_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        tk.Label(audio_config_frame, text="Tur:", font=('Segoe UI', 9), bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        self.ozet_repeat_var = tk.StringVar(value="1")
        ozet_repeat_spin = tk.Spinbox(audio_config_frame, from_=1, to=100, textvariable=self.ozet_repeat_var, width=4)
        ozet_repeat_spin.pack(side=tk.LEFT, padx=(5, 10))
        
        tk.Label(audio_config_frame, text="Hız:", font=('Segoe UI', 9), bg=self.colors['card'], fg=self.colors['text']).pack(side=tk.LEFT)
        speed_scale = tk.Scale(audio_config_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.speech_rate_var, showvalue=True, width=10, length=80, bg=self.colors['card'], fg=self.colors['text'], highlightthickness=0, troughcolor=self.colors['bg'])
        speed_scale.pack(side=tk.LEFT, padx=(5, 0))
        
        self.ozet_follow_var = tk.BooleanVar(value=True)
        tk.Checkbutton(audio_config_frame, text="Takip Et", variable=self.ozet_follow_var, bg=self.colors['card'], fg=self.colors['text'], font=('Segoe UI', 9), selectcolor=self.colors['bg']).pack(side=tk.LEFT, padx=(10, 0))

        badge_info_label = tk.Label(
            ozet_card,
            text="Sınav rozetleri yalnızca görsel bilgi içindir, seslendirme bunları okumaz.",
            font=("Segoe UI", 8, "italic"),
            bg=self.colors['card'],
            fg=self.colors['text_secondary'],
            anchor="w",
        )
        badge_info_label.pack(fill=tk.X, padx=20, pady=(6, 4))

        reference_card = tk.Frame(
            ozet_card,
            bg=self.colors['primary'],
            highlightbackground=self.colors['border'],
            highlightthickness=1,
        )
        reference_card.pack(fill=tk.X, padx=20, pady=(0, 8))

        reference_title = tk.Label(
            reference_card,
            text="Başlığa tıkla: yıl / soru referansları burada görünür",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['text'],
            anchor="w",
        )
        reference_title.pack(fill=tk.X, padx=10, pady=(8, 4))

        self.ozet_reference_text = tk.Text(
            reference_card,
            height=5,
            wrap=tk.WORD,
            font=("Segoe UI", 8),
            bg=self.colors['primary'],
            fg=self.colors['text_secondary'],
            insertbackground=self.colors['text'],
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=0,
        )
        self.ozet_reference_text.pack(fill=tk.X, padx=0, pady=(0, 8))
        self.ozet_reference_text.insert(
            "1.0",
            "Henüz bir başlık seçilmedi. Rozetli konu satırına tıklayın; ayrıntılar seslendirmeye dahil edilmez.",
        )
        self.ozet_reference_text.config(state=tk.DISABLED)

        controls = tk.Frame(ozet_card, bg=self.colors['card'])
        controls.pack(fill=tk.X, padx=20, pady=10)
        
        text_frame = tk.Frame(ozet_card, bg=self.colors['border'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        txt = tk.Text(text_frame, wrap=tk.WORD, font=self.fonts['body'],
                     bg=self.colors['card'], fg=self.colors['text'],
                     padx=10, pady=10, bd=0)
        txt.tag_configure("highlight", background=self.colors['warning'], foreground="#000000")
        
        scroll = ttk.Scrollbar(text_frame, command=txt.yview, style="Modern.Vertical.TScrollbar")
        txt.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right-click menu for notes
        def add_personal_note():
            try:
                selected_text = txt.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
                if not selected_text: return
            except:
                return
                
            note_win = tk.Toplevel(self.root)
            note_win.title("Not Ekle")
            note_win.geometry("400x300")
            note_win.configure(bg=self.colors['bg'])
            
            tk.Label(note_win, text=f"Seçili Metin: {selected_text[:50]}...", font=('Segoe UI', 9, 'italic'), bg=self.colors['bg'], fg=self.colors['text_secondary']).pack(pady=10)
            note_entry = tk.Text(note_win, height=8, width=40, bg=self.colors['card'], fg=self.colors['text'], insertbackground=self.colors['text'])
            note_entry.pack(padx=20, pady=5)
            
            def save_note():
                note = note_entry.get("1.0", tk.END).strip()
                if note:
                    notes_file = self.base_dir / "ozet_notlarim.txt"
                    with open(notes_file, "a", encoding="utf-8") as f:
                        f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M')} ---\n")
                        f.write(f"Metin: {selected_text}\n")
                        f.write(f"Not: {note}\n")
                    messagebox.showinfo("Başarılı", "Notunuz 'ozet_notlarim.txt' dosyasına kaydedildi.")
                    note_win.destroy()
            
            self.create_button(note_win, "KAYDET", save_note, self.colors['success']).pack(pady=10)

        def show_context_menu(event):
            menu = tk.Menu(self.root, tearoff=0, bg=self.colors['card'], fg=self.colors['text'])
            menu.add_command(label="Not Ekle", command=add_personal_note)
            menu.post(event.x_root, event.y_row) # Wait, it should be x_root, y_root
            
        # Re-defining show_context_menu properly
        def show_context_menu(event):
            menu = tk.Menu(self.root, tearoff=0, bg=self.colors['card'], fg=self.colors['text'])
            menu.add_command(label="📝 Seçili Metne Not Ekle", command=add_personal_note)
            menu.post(event.x_root, event.y_root)

        txt.bind("<Button-3>", show_context_menu)
        
        ozet_file = self.base_dir / filename
        file_content = f"{filename} dosyası bulunamadı veya boş."
        try:
            if ozet_file.exists():
                with open(ozet_file, "r", encoding="utf-8") as f:
                    file_content = f.read().strip()
        except Exception as e:
            file_content = f"Okuma hatası: {e}"
            
        txt.insert(tk.END, file_content)
        txt.config(state=tk.DISABLED)
        
        if not hasattr(self, 'ozet_topic_data'):
            self.ozet_topic_data = []
            
        if not hasattr(self, 'ozet_play_queue'):
            self.ozet_play_queue = []
            
        if not hasattr(self, 'ozet_current_index'):
            self.ozet_current_index = 0
        (
            parsed_topics,
            main_category_to_topics,
            main_category_counts,
            topic_counts,
            parser_warnings,
        ) = self._load_ozet_parser_result(ozet_file, file_content)
        self.ozet_topic_data = parsed_topics
        self.ozet_parser_warnings = parser_warnings
        self._decorate_ozet_text_with_exam_badges(txt)
        self._ozet_blocks_by_line = {
            int(block["start_line"]): block
            for block in self.ozet_topic_data
            if block.get("start_line")
        }

        def show_block_references_for_line(line_number):
            try:
                block = self._ozet_blocks_by_line.get(int(line_number))
            except Exception:
                block = None
            if block and self._should_show_summary_badges_for_block(block):
                self._show_ozet_reference_panel(block)

        def on_text_left_click(event):
            text_index = txt.index(f"@{event.x},{event.y}")
            line_number = text_index.split(".", 1)[0]
            show_block_references_for_line(line_number)

        txt.bind("<Button-1>", on_text_left_click, add="+")
        
        # UI Setup for Hierarchical Filter
        def format_label(name, count):
            return f"{name} ({count})" if count > 0 else name

        all_main_cats = ["Tümü"] + sorted(list(main_category_to_topics.keys()), key=lambda x: file_content.find(x) if x in file_content else 9999)
        main_cat_labels = [format_label(c, main_category_counts.get(c, 0)) for c in all_main_cats]
        self.ozet_main_nav_combo.config(values=main_cat_labels)
        
        # Mapping from labels back to original names
        self._main_label_to_name = {format_label(c, main_category_counts.get(c, 0)): c for c in all_main_cats}
        
        def on_main_cat_change(*args):
            label = self.ozet_main_nav_var.get()
            selected_main = self._main_label_to_name.get(label, "Tümü")
            
            if selected_main == "Tümü" or selected_main == "Ders Seçiniz...":
                # List all unique sub-topics
                all_subs = []
                seen = set()
                for t in parsed_topics:
                    if t["topic"] not in seen:
                        all_subs.append(t["topic"])
                        seen.add(t["topic"])
                sub_labels = ["Tümü"] + [format_label(s, topic_counts.get(s, 0)) for s in all_subs]
                self._sub_label_to_name = {format_label(s, topic_counts.get(s, 0)): s for s in all_subs}
                self._sub_label_to_name["Tümü"] = "Tümü"
                self.ozet_nav_combo.config(values=sub_labels)
                self.ozet_topic_combo.config(values=sub_labels)
                self.ozet_nav_var.set("Tümü")
                self.ozet_topic_var.set("Tümü")
            else:
                sub_topics = main_category_to_topics.get(selected_main, [])
                sub_labels = ["Tümü"] + [format_label(s, topic_counts.get(s, 0)) for s in sub_topics]
                self._sub_label_to_name = {format_label(s, topic_counts.get(s, 0)): s for s in sub_topics}
                self._sub_label_to_name["Tümü"] = "Tümü"
                self.ozet_nav_combo.config(values=sub_labels)
                self.ozet_topic_combo.config(values=sub_labels)
                self.ozet_nav_var.set("Tümü")
                self.ozet_topic_var.set("Tümü")
            
            if selected_main != "Tümü" and selected_main != "Ders Seçiniz...":
                navigate_to_main_topic()

        self.ozet_main_nav_var.trace_add("write", on_main_cat_change)

        def navigate_to_main_topic(event=None):
            label = self.ozet_main_nav_var.get()
            selected = self._main_label_to_name.get(label, "Tümü")
            if not selected or selected in ["Tümü", "Ders Seçiniz..."]:
                return
            
            txt.config(state=tk.NORMAL)
            txt.tag_remove("main_nav_highlight", "1.0", tk.END)
            
            # Find exact line starting with lesson name.
            search_pattern = self._turkish_upper(selected)
            
            pos = "1.0"
            while True:
                pos = txt.search(search_pattern, pos, stopindex=tk.END, nocase=True)
                if not pos:
                    break
                
                if pos.split('.')[1] == '0':
                    line_end = txt.index(f"{pos} lineend")
                    line_content = txt.get(pos, line_end).strip()
                    if self._turkish_upper(line_content).startswith(search_pattern):
                        txt.see(pos)
                        txt.tag_add("main_nav_highlight", pos, line_end)
                        txt.tag_configure("main_nav_highlight", background=self.colors['success'], foreground="white")
                        show_block_references_for_line(pos.split(".", 1)[0])
                        break
                pos = f"{pos}+1c"
            
            txt.config(state=tk.DISABLED)

        self.ozet_main_nav_combo.bind("<<ComboboxSelected>>", navigate_to_main_topic)

        def navigate_to_topic(event=None):
            label = self.ozet_nav_var.get()
            selected = getattr(self, '_sub_label_to_name', {}).get(label, label)
            if not selected or selected in ["Tümü", "Seçiniz..."]:
                return
            
            txt.config(state=tk.NORMAL)
            txt.tag_remove("nav_highlight", "1.0", tk.END)
            
            pos = "1.0"
            while True:
                pos = txt.search(selected, pos, stopindex=tk.END)
                if not pos:
                    break
                
                if pos.split('.')[1] == '0':
                    line_end = txt.index(f"{pos} lineend")
                    txt.see(pos)
                    txt.tag_add("nav_highlight", pos, line_end)
                    txt.tag_configure("nav_highlight", background=self.colors['accent'], foreground="white")
                    show_block_references_for_line(pos.split(".", 1)[0])
                    break
                pos = f"{pos}+1c"
                
            txt.config(state=tk.DISABLED)

        self.ozet_nav_combo.bind("<<ComboboxSelected>>", navigate_to_topic)
        
        # Initial populate of sub topics
        on_main_cat_change()

        def search_in_text(event=None):
            query = self.ozet_search_var.get().strip()
            if not query:
                return
            
            txt.config(state=tk.NORMAL)
            txt.tag_remove("search_highlight", "1.0", tk.END)
            
            # Start searching from current position or start
            start_pos = txt.index(tk.INSERT) or "1.0"
            if event and event.keysym == "Return": # If enter pressed, find next
                start_pos = f"{start_pos}+1c"
            else:
                start_pos = "1.0"

            pos = txt.search(query, start_pos, stopindex=tk.END, nocase=True)
            if not pos and start_pos != "1.0": # Wrap around
                pos = txt.search(query, "1.0", stopindex=tk.END, nocase=True)
                
            if pos:
                txt.see(pos)
                txt.mark_set(tk.INSERT, pos)
                end_pos = f"{pos}+{len(query)}c"
                txt.tag_add("search_highlight", pos, end_pos)
                txt.tag_configure("search_highlight", background=self.colors['warning'], foreground="black")
            else:
                self._set_speech_status(f"'{query}' metinde bulunamadı.")
            
            txt.config(state=tk.DISABLED)

        self.ozet_search_entry.bind("<Return>", search_in_text)
        
        search_btn = self.create_button(config_frame, "🔍 ARA", search_in_text, self.colors['primary'])
        search_btn.config(pady=5, padx=10)
        search_btn.pack(side=tk.LEFT, padx=5)
            
        def on_config_change(*args):
            self.ozet_play_queue = []
            self.ozet_current_index = 0
            
        self.ozet_topic_var.trace_add("write", on_config_change)
        self.ozet_main_nav_var.trace_add("write", on_config_change)
        self.ozet_nav_var.trace_add("write", on_config_change)
        self.ozet_mode_var.trace_add("write", on_config_change)
        self.ozet_repeat_var.trace_add("write", on_config_change)

        def build_play_queue():
            queue = []
            mode = self.ozet_mode_var.get()
            
            # Decision Logic: Which topic to start from?
            # 1. Check Audio-specific Topic (Okuma Konusu)
            selected = self.ozet_topic_var.get()
            if not selected or selected in ["Tümü", "Seçiniz..."]:
                # 2. Check Navigation Topic (Konuya Git)
                selected = self.ozet_nav_var.get()
                if not selected or selected in ["Tümü", "Seçiniz..."]:
                    # 3. Check Ders Navigation (Derslere Git)
                    selected = self.ozet_main_nav_var.get()
                    if not selected or selected in ["Tümü", "Ders Seçiniz..."]:
                        selected = "Tümü"
            
            # Map back from label to name if necessary
            selected = getattr(self, '_sub_label_to_name', {}).get(selected, selected)
            selected = self._main_label_to_name.get(selected, selected)
            
            try: loops = max(1, int(self.ozet_repeat_var.get()))
            except: loops = 1
            
            selected_blocks = []
            if mode == "Sırayla Oku" and selected != "Tümü":
                # Find the first occurrence of either the main_cat or the topic
                start_idx = 0
                for i, t in enumerate(self.ozet_topic_data):
                    if t["topic"] == selected or t["main_cat"] == selected:
                        start_idx = i
                        break
                selected_blocks = self.ozet_topic_data[start_idx:]
            elif mode == "Sadece Seçili" and selected != "Tümü":
                # If a Ders is selected, read all topics belonging to that Ders
                selected_blocks = [t for t in self.ozet_topic_data if t["topic"] == selected or t["main_cat"] == selected]
            else:
                selected_blocks = list(self.ozet_topic_data)
                
            if mode == "Rastgele Karışık":
                random.shuffle(selected_blocks)
                
            for _ in range(loops):
                for block in selected_blocks:
                    queue.extend(block["sentences"])
                    
            self.ozet_play_queue = queue
            self.ozet_current_index = 0

        def play_next_sentence():
            if self.current_view not in ("kodlamali_ozet", "ozet") or not self.ozet_play_queue:
                return
                
            if self.ozet_current_index >= len(self.ozet_play_queue):
                self._set_speech_status("Seçili okuma tamamlandı.")
                self.ozet_current_index = 0
                self.ozet_play_queue = []
                txt.tag_remove("highlight", "1.0", tk.END)
                return
                
            sentence_obj = self.ozet_play_queue[self.ozet_current_index]
            self.ozet_current_index += 1
            
            raw_s = sentence_obj["raw"]
            norm_s = sentence_obj["norm"]
            
            txt.tag_remove("highlight", "1.0", tk.END)
            if self.ozet_follow_var.get() and raw_s:
                search_text = raw_s
                if len(search_text) > 50:
                    search_text = search_text[:50]
                start_idx = txt.search(search_text, "1.0", stopindex=tk.END, exact=True)
                if start_idx:
                    end_idx = f"{start_idx}+{len(raw_s)}c"
                    txt.tag_add("highlight", start_idx, end_idx)
                    txt.see(start_idx)
            
            self._cancel_speech_sequence()
            seq_token = self._speech_sequence_token
            
            self.speak_text(
                norm_s,
                status_prefix=f"Okunuyor ({self.ozet_current_index}/{len(self.ozet_play_queue)})",
                on_finished=play_next_sentence,
                sequence_token=seq_token
            )

        def read_aloud():
            self.stop_speech()
            if not self.speech_engine.is_available():
                messagebox.showerror("Hata", "Çevrimdışı Türkçe ses modeli bulunamadı.")
                return
                
            if not self.ozet_play_queue:
                build_play_queue()
                
            if not self.ozet_play_queue:
                self._set_speech_status("Okunacak metin yok.")
                return
                
            if self.ozet_current_index > 0 and self.ozet_current_index < len(self.ozet_play_queue):
                self.ozet_current_index -= 1
                
            play_next_sentence()
            
        def read_from_start():
            self.stop_speech()
            build_play_queue()
            if self.ozet_play_queue:
                read_aloud()
            else:
                self._set_speech_status("Okunacak metin yok.")
            
        def stop_aloud():
            self.stop_speech()
            self._set_speech_status(f"Durduruldu. Kaldığı yer: {self.ozet_current_index}/{len(self.ozet_play_queue)}")
            
        def edit_file():
            if str(os.name) == 'nt':
                os.startfile(str(ozet_file))
            else:
                messagebox.showinfo("Bilgi", "Dosyayı manuel olarak düzenleyin:\n" + str(ozet_file))
                
        def refresh_text():
            self.ozet_play_queue = []
            self.ozet_current_index = 0
            self._show_ozet_file(filename, title, view_name)

        read_btn = self.create_button(controls, "▶️ OKU / DEVAM", read_aloud, self.colors['primary'])
        read_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        restart_btn = self.create_button(controls, "⏮️ BAŞTAN OKU", read_from_start, self.colors['accent'])
        restart_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        stop_btn = self.create_button(controls, "⏹️ DURDUR", stop_aloud, self.colors['danger'])
        stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        edit_btn = self.create_button(controls, "✏️ AÇ/DÜZENLE", edit_file, self.colors['warning'])
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))

        refresh_btn = self.create_button(controls, "🔄 YENİLE", refresh_text, self.colors['success'])
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

    def check_new_files(self):
        """Yeni eklenen dosyaları kontrol eder"""
        import re
        import json
        from datetime import datetime
        
        base_path = WORDE_DIR
        last_check_file = self.base_dir / "last_check.json"
        
        try:
            if last_check_file.exists():
                with open(last_check_file, 'r', encoding='utf-8') as f:
                    last_check = json.load(f)
            else:
                last_check = {"files": {}, "last_run": ""}
        except:
            last_check = {"files": {}, "last_run": ""}
        
        current_files = {}
        new_files = []
        
        if base_path.exists():
            for file_path in base_path.iterdir():
                filename = file_path.name
                match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
                if match:
                    mod_time = file_path.stat().st_mtime
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
        
        analiz_card = self.create_card(self.main_content, "Soru Analizi")
        analiz_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        content_frame = tk.Frame(analiz_card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        base_path = WORDE_DIR
        years_data = defaultdict(lambda: defaultdict(int))
        konu_data = defaultdict(lambda: defaultdict(int))
        total_questions = 0
        all_parsed_questions = []
        
        if base_path.exists():
            for file_path in base_path.iterdir():
                filename = file_path.name
                match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
                if match:
                    year = int(match.group(1))
                    subject = self.format_subject_label(match.group(2))
                    questions = self.parse_questions_from_file(file_path, year, subject)
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

        def create_analysis_table_area(parent, height=220):
            area_frame = tk.Frame(parent, bg=self.colors['card'])
            area_frame.pack(fill=tk.X, padx=15, pady=(0, 5))

            canvas_wrap = tk.Frame(area_frame, bg=self.colors['border'])
            canvas_wrap.pack(fill=tk.X, expand=True)

            table_canvas = tk.Canvas(
                canvas_wrap,
                bg=self.colors['card'],
                highlightthickness=0,
                bd=0,
                height=height,
            )
            y_scroll = ttk.Scrollbar(
                canvas_wrap,
                orient="vertical",
                command=table_canvas.yview,
                style="Modern.Vertical.TScrollbar",
            )
            x_scroll = ttk.Scrollbar(
                area_frame,
                orient="horizontal",
                command=table_canvas.xview,
            )
            table_canvas.configure(
                yscrollcommand=y_scroll.set,
                xscrollcommand=x_scroll.set,
            )

            y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            table_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            x_scroll.pack(fill=tk.X)

            table_inner = tk.Frame(table_canvas, bg=self.colors['border'])
            table_window = table_canvas.create_window((0, 0), window=table_inner, anchor="nw")

            def _refresh_table_scroll(_event=None):
                table_canvas.configure(scrollregion=table_canvas.bbox("all"))

            def _fit_table_width(event):
                requested_width = table_inner.winfo_reqwidth()
                table_canvas.itemconfigure(table_window, width=max(event.width, requested_width))

            table_inner.bind("<Configure>", _refresh_table_scroll)
            table_canvas.bind("<Configure>", _fit_table_width)

            return table_inner
        
        tk.Label(content_frame, text="📅 YILLARA GÖRE DAĞILIM",
                font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(pady=(15, 5))
        
        table_frame = create_analysis_table_area(content_frame, height=170)
        
        analysis_subjects = sorted({q['ders'] for q in all_parsed_questions})
        headers = ["Yıl"] + analysis_subjects + ["Toplam"]
        for i, h in enumerate(headers):
            tk.Label(table_frame, text=h, font=('Segoe UI', 11, 'bold'),
                    bg=self.colors['primary'], fg=self.colors['text'], width=16).grid(row=0, column=i, padx=1, pady=1)
        
        sorted_years = sorted(years_data.keys(), reverse=True)
        for row_idx, year in enumerate(sorted_years, 1):
            subject_counts = [years_data[year][subject] for subject in analysis_subjects]
            total_count = sum(subject_counts)
            bg = self.colors['card'] if row_idx % 2 == 0 else self.colors['primary']
            for col_idx, val in enumerate([str(year)] + [str(c) for c in subject_counts] + [str(total_count)]):
                tk.Label(table_frame, text=val, font=('Segoe UI', 11),
                        bg=bg, fg=self.colors['text'], width=16).grid(row=row_idx, column=col_idx, padx=1, pady=1)
        
        tk.Label(content_frame, text="📚 KONULARA GÖRE DAĞILIM",
                font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(pady=(20, 5))
        
        konu_table = create_analysis_table_area(content_frame, height=280)
        
        konu_headers = ["Konu"] + analysis_subjects + ["Toplam"]
        for i, h in enumerate(konu_headers):
            tk.Label(konu_table, text=h, font=('Segoe UI', 11, 'bold'),
                    bg=self.colors['primary'], fg=self.colors['text'], width=24).grid(row=0, column=i, padx=1, pady=1)
        
        konu_totals = {}
        for konu in konu_data:
            konu_totals[konu] = sum(konu_data[konu][subject] for subject in analysis_subjects)
        
        sorted_konular = sorted(konu_totals.items(), key=lambda x: x[1], reverse=True)
        
        for row_idx, (konu, total) in enumerate(sorted_konular, 1):
            subject_counts = [konu_data[konu][subject] for subject in analysis_subjects]
            bg = self.colors['card'] if row_idx % 2 == 0 else self.colors['primary']
            for col_idx, val in enumerate([konu[:24]] + [str(c) for c in subject_counts] + [str(total)]):
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
            
            matris_inner = create_analysis_table_area(content_frame, height=320)
            
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
            selected_year, selected_subject, selected_topic = self.get_analysis_filter_values(include_year=True)
            scope_questions = filter_questions(
                all_parsed_questions,
                year=selected_year,
                subject=selected_subject,
                topic=selected_topic,
            )
            history_questions = filter_questions(
                all_parsed_questions,
                year=None,
                subject=selected_subject,
                topic=selected_topic,
            )
            use_semantic = len(scope_questions) <= 250
            report = build_similarity_report(
                scope_questions,
                history_questions=history_questions,
                use_semantic=use_semantic,
            )

            tk.Label(content_frame, text="🔍 BENZER SORULAR VE ÇIKIŞ EĞİLİMİ",
                    font=('Segoe UI', 11, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(pady=(20, 5))
            tk.Label(
                content_frame,
                text="Seçili filtreye göre benzer soru kalıpları, sık çıkan soru tipleri, alt konu ipuçları ve veri tabanlı muhtemel başlıklar gösterilir.",
                font=('Segoe UI', 9),
                bg=self.colors['card'],
                fg=self.colors['text_secondary'],
                wraplength=780,
                justify="left",
            ).pack(padx=15, pady=(0, 8), anchor="w")

            tk.Label(
                content_frame,
                text=self.format_analysis_scope_text(report['scope_total'], report['history_total']),
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['primary'],
                fg=self.colors['text'],
                anchor="w",
                justify="left",
            ).pack(fill=tk.X, padx=15, pady=(0, 10), ipady=5)

            tk.Label(
                content_frame,
                text=f"Aday tarama: {report.get('candidate_pair_count', 0)} çift | Semantik: {report.get('semantic_backend', 'kapali')}",
                font=('Segoe UI', 8),
                bg=self.colors['card'],
                fg=self.colors['text_secondary'],
                justify="left",
                anchor="w",
            ).pack(fill=tk.X, padx=15, pady=(0, 8))

            if not scope_questions:
                tk.Label(
                    content_frame,
                    text="Bu filtrede analiz edilecek soru bulunamadı. Yıl, ders veya konu filtresini biraz genişletip tekrar deneyin.",
                    font=('Segoe UI', 10),
                    bg=self.colors['card'],
                    fg=self.colors['text'],
                    wraplength=780,
                    justify="left",
                ).pack(padx=15, pady=10, anchor="w")
            else:
                summary_frame = tk.Frame(content_frame, bg=self.colors['border'])
                summary_frame.pack(fill=tk.X, padx=15, pady=5)

                left_col = tk.Frame(summary_frame, bg=self.colors['card'])
                left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

                right_col = tk.Frame(summary_frame, bg=self.colors['card'])
                right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 1), pady=1)

                tk.Label(left_col, text="📌 Öne Çıkan Soru Tipleri",
                        font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(anchor="w", padx=10, pady=(8, 4))
                for row in report['question_types'][:6]:
                    tk.Label(
                        left_col,
                        text=f"• {row['question_type']}: {row['count']} soru",
                        font=('Segoe UI', 9),
                        bg=self.colors['card'],
                        fg=self.colors['text'],
                        justify="left",
                    ).pack(anchor="w", padx=14, pady=1)

                right_title = "📚 Kapsamdaki Konular"
                right_rows = report['topic_counts'][:6]
                if selected_topic:
                    right_title = "🧩 Alt Konu İpuçları"
                    right_rows = []

                tk.Label(right_col, text=right_title,
                        font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(anchor="w", padx=10, pady=(8, 4))

                if right_rows:
                    for row in right_rows:
                        tk.Label(
                            right_col,
                            text=f"• {row['topic']}: {row['count']} soru",
                            font=('Segoe UI', 9),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            justify="left",
                        ).pack(anchor="w", padx=14, pady=1)
                else:
                    for item in report['subtopics_by_topic'][:4]:
                        phrase_text = ", ".join(item['phrases']) if item['phrases'] else "Belirgin alt konu bulunamadı"
                        tk.Label(
                            right_col,
                            text=f"• {item['topic']}: {phrase_text}",
                            font=('Segoe UI', 9),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            wraplength=360,
                            justify="left",
                        ).pack(anchor="w", padx=14, pady=1)

                subtopic_frame = tk.Frame(content_frame, bg=self.colors['border'])
                subtopic_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

                tk.Label(subtopic_frame, text="🧭 Konu ve Alt Konu İpuçları",
                        font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(anchor="w", padx=10, pady=(8, 4))

                if report['subtopics_by_topic']:
                    for item in report['subtopics_by_topic'][:6]:
                        phrase_text = ", ".join(item['phrases']) if item['phrases'] else "Belirgin alt konu bulunamadı"
                        tk.Label(
                            subtopic_frame,
                            text=f"• {item['topic']}: {phrase_text}",
                            font=('Segoe UI', 9),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            wraplength=760,
                            justify="left",
                        ).pack(anchor="w", padx=14, pady=1)
                else:
                    tk.Label(
                        subtopic_frame,
                        text="Bu kapsamda yeterli alt konu ipucu bulunamadı.",
                        font=('Segoe UI', 9),
                        bg=self.colors['card'],
                        fg=self.colors['text'],
                    ).pack(anchor="w", padx=14, pady=(0, 8))

                cluster_frame = tk.Frame(content_frame, bg=self.colors['border'])
                cluster_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

                tk.Label(cluster_frame, text="🧠 Tekrarlayan ÖSYM Soru Kalıpları",
                        font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(anchor="w", padx=10, pady=(8, 4))

                if report['clusters']:
                    for index, cluster in enumerate(report['clusters'][:6], 1):
                        years_text = ", ".join(str(year) for year in cluster['years'][:6]) if cluster['years'] else "?"
                        phrase_text = ", ".join(cluster['phrases']) if cluster['phrases'] else "Alt konu ipucu yok"
                        cluster_text = (
                            f"{index}. {cluster['topic'] or 'Konu yok'} | {cluster['question_type']} | "
                            f"{cluster['size']} soru | Yıllar: {years_text} | Alt konu: {phrase_text}"
                        )
                        tk.Label(
                            cluster_frame,
                            text=cluster_text,
                            font=('Segoe UI', 9),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            wraplength=760,
                            justify="left",
                        ).pack(anchor="w", padx=14, pady=2)
                else:
                    tk.Label(
                        cluster_frame,
                        text="Belirgin tekrar eden soru kalıbı bulunamadı.",
                        font=('Segoe UI', 9),
                        bg=self.colors['card'],
                        fg=self.colors['text'],
                    ).pack(anchor="w", padx=14, pady=(0, 8))

                prediction_frame = tk.Frame(content_frame, bg=self.colors['border'])
                prediction_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

                tk.Label(prediction_frame, text="📈 Çıkması Muhtemel Başlıklar",
                        font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(anchor="w", padx=10, pady=(8, 4))
                tk.Label(
                    prediction_frame,
                    text="Bu alan kesin tahmin değildir; geçmiş tekrar, yıl yayılımı ve son yıllardaki görünme sıklığına göre veri tabanlı bir öncelik listesi üretir.",
                    font=('Segoe UI', 8),
                    bg=self.colors['card'],
                    fg=self.colors['text_secondary'],
                    wraplength=760,
                    justify="left",
                ).pack(anchor="w", padx=14, pady=(0, 6))

                if report['likely_topics'] and not selected_topic:
                    for row in report['likely_topics'][:6]:
                        years_text = ", ".join(str(year) for year in row['years'][-5:]) if row['years'] else "?"
                        tk.Label(
                            prediction_frame,
                            text=f"• {row['topic']} | skor {row['score']:.1f} | toplam {row['count']} | son yıllar katkısı {row['recent_count']} | yıllar: {years_text}",
                            font=('Segoe UI', 9),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            wraplength=760,
                            justify="left",
                        ).pack(anchor="w", padx=14, pady=1)

                if report['likely_subtopics']:
                    subtopic_title = "Muhtemel alt konular"
                    if selected_topic:
                        subtopic_title = f"Muhtemel alt konular ({selected_topic})"

                    tk.Label(
                        prediction_frame,
                        text=subtopic_title,
                        font=('Segoe UI', 9, 'bold'),
                        bg=self.colors['card'],
                        fg=self.colors['text'],
                    ).pack(anchor="w", padx=14, pady=(8, 3))

                    for row in report['likely_subtopics'][:6]:
                        years_text = ", ".join(str(year) for year in row['years'][-4:]) if row['years'] else "?"
                        tk.Label(
                            prediction_frame,
                            text=f"• {row['subtopic']} | skor {row['score']:.1f} | tekrar {row['count']} | yıllar: {years_text}",
                            font=('Segoe UI', 9),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            wraplength=760,
                            justify="left",
                        ).pack(anchor="w", padx=18, pady=1)

                pair_frame = tk.Frame(content_frame, bg=self.colors['border'])
                pair_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

                tk.Label(pair_frame, text="🎯 Güçlü Benzer Soru Eşleşmeleri",
                        font=('Segoe UI', 10, 'bold'), bg=self.colors['card'], fg=self.colors['text']).pack(anchor="w", padx=10, pady=(8, 4))

                if not report['similar_pairs']:
                    tk.Label(
                        pair_frame,
                        text="Bu filtrede güçlü benzer soru çifti bulunamadı.",
                        font=('Segoe UI', 9),
                        bg=self.colors['card'],
                        fg=self.colors['text'],
                    ).pack(anchor="w", padx=14, pady=(0, 8))
                else:
                    for pair in report['similar_pairs'][:12]:
                        q1 = pair['q1']
                        q2 = pair['q2']
                        overlap_text = ", ".join(pair['overlap_terms']) if pair['overlap_terms'] else "Belirgin ortak anahtar yok"
                        header_text = (
                            f"• %{int(pair['score'] * 100)} eşleşme | "
                            f"{q1['yil']} {q1['ders']} Soru {q1['soru_no']} ↔ "
                            f"{q2['yil']} {q2['ders']} Soru {q2['soru_no']}"
                        )
                        meta_text = (
                            f"  Konu: {q1['konu'] or '-'} / {q2['konu'] or '-'} | "
                            f"Tip: {q1['question_type']} / {q2['question_type']} | "
                            f"Ortak izler: {overlap_text}"
                        )
                        preview_1 = (q1['soru_metni'] or "").replace('\n', ' ')[:110]
                        preview_2 = (q2['soru_metni'] or "").replace('\n', ' ')[:110]

                        tk.Label(
                            pair_frame,
                            text=header_text,
                            font=('Segoe UI', 9, 'bold'),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            justify="left",
                        ).pack(anchor="w", padx=14, pady=(2, 0))
                        tk.Label(
                            pair_frame,
                            text=meta_text,
                            font=('Segoe UI', 8),
                            bg=self.colors['card'],
                            fg=self.colors['text_secondary'],
                            wraplength=760,
                            justify="left",
                        ).pack(anchor="w", padx=18, pady=(0, 1))
                        tk.Label(
                            pair_frame,
                            text=f"  A: {preview_1}...",
                            font=('Segoe UI', 8),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            wraplength=760,
                            justify="left",
                        ).pack(anchor="w", padx=18, pady=0)
                        tk.Label(
                            pair_frame,
                            text=f"  B: {preview_2}...",
                            font=('Segoe UI', 8),
                            bg=self.colors['card'],
                            fg=self.colors['text'],
                            wraplength=760,
                            justify="left",
                        ).pack(anchor="w", padx=18, pady=(0, 3))
        
        back_btn = self.create_button(content_frame, "🔙 GERİ",
                                      self.show_welcome_screen, self.colors['text_secondary'])
        back_btn.pack(pady=20, ipady=5)
        
    def format_subject_label(self, subject):
        """Dosya adindaki ders etiketini ekranda gosterilecek forma cevirir."""
        subject = str(subject or "").replace("_", " ").strip()
        replacements = {
            "MBSTS": "MBSTS",
            "Onlisans": "Önlisans",
            "Ortaogretim": "Ortaöğretim",
            "ogretim": "öğretim",
            "DHBT Ortak": "DHBT Ortak (1-20)",
        }
        for source, target in replacements.items():
            subject = subject.replace(source, target)
        return subject

    def has_dhbt_common_file(self, year: int) -> bool:
        return (WORDE_DIR / f"{year}_DHBT_Ortak_Sorulari.txt").exists()

    def should_skip_dhbt_common_question(self, year: int, subject: str, soru_no: int) -> bool:
        if soru_no > 20:
            return False
        if subject not in {"DHBT Lisans", "DHBT Önlisans", "DHBT Ortaöğretim"}:
            return False
        return self.has_dhbt_common_file(year)

    def format_subject_label(self, subject):
        return format_exam_subject_label(subject)

    def has_dhbt_common_file(self, year: int) -> bool:
        return question_bank_has_dhbt_common_file(year, base_dir=WORDE_DIR)

    def should_skip_dhbt_common_question(self, year: int, subject: str, soru_no: int) -> bool:
        return question_bank_should_skip_dhbt_common_question(year, subject, soru_no, base_dir=WORDE_DIR)

    def get_analysis_filter_values(self, include_year=True):
        """Analiz ekraninda kullanilacak mevcut filtreleri dondurur."""
        year = None
        subject = None
        topic = None

        if include_year and hasattr(self, 'year_var'):
            selected_years = self._selected_years()
            if selected_years:
                year = ", ".join(selected_years)

        if hasattr(self, 'ders_var'):
            selected_subjects = self._selected_subjects()
            if selected_subjects:
                subject = ", ".join(selected_subjects)

        if hasattr(self, 'konu_var'):
            selected_topics = self._selected_topics()
            if selected_topics:
                topic = ", ".join(selected_topics)

        return year, subject, topic

    def format_analysis_scope_text(self, scope_total, history_total=None, include_year=True):
        """Aktif filtre kapsamını analiz ekranında gösterilecek metne dönüştürür."""
        year, subject, topic = self.get_analysis_filter_values(include_year=include_year)

        parts = [
            f"Yıl: {year if year else 'Tüm yıllar'}",
            f"Ders: {subject if subject else 'Tüm dersler'}",
            f"Konu: {topic if topic else 'Tüm konular'}",
            f"Havuz: {scope_total} soru",
        ]

        if history_total is not None and history_total != scope_total:
            parts.append(f"Tahmin havuzu: {history_total} soru")

        return " | ".join(parts)

    def load_questions(self, show_message=True):
        """Soruları yükler"""
        def load_in_background():
            try:
                import re
                base_path = WORDE_DIR
                loaded_questions = []
                unique_subjects = set()
                found_years = set()
                
                if base_path.exists():
                    for file_path in base_path.iterdir():
                        filename = file_path.name
                        match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
                        if match:
                            year = int(match.group(1))
                            subject = self.format_subject_label(match.group(2))
                            year_questions = self.parse_questions_from_file(file_path, year, subject)
                            loaded_questions.extend(year_questions)
                            found_years.add(str(year))
                            unique_subjects.add(subject)
                            print(f"{year} {subject} sınavından {len(year_questions)} soru yüklendi")
                
                self.questions = loaded_questions
                self.subjects = sorted(list(unique_subjects))
                self.available_subjects = sorted(list(unique_subjects)) or list(self.available_subjects)
                
                # Update UI elements
                years_list = ["Tüm yıllar"] + sorted(list(found_years), reverse=True)
                ders_list = self.available_subjects
                
                self.root.after(0, lambda: self.update_dropdown_values(years_list, ders_list))
                self.root.after(0, self.update_stats)
                self.root.after(0, self.update_question_limit)
                self.root.after(0, lambda: self.questions_loaded_successfully(show_message=show_message))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Sorular yüklenirken hata oluştu: {e}"))
        
        # Show loading message
        self.load_button.config(text="⏳ YÜKLENİYOR...", bg=self.colors['text_secondary'])
        self.root.after(100, load_in_background)

    def load_questions(self, show_message=True):
        """Sorulari ortak soru deposu uzerinden yukler."""
        def load_in_background():
            try:
                loaded_questions, found_years, unique_subjects = load_question_bank(
                    base_dir=WORDE_DIR,
                    default_topic=None,
                    visual_resolver=self.resolve_visual_path,
                )

                self.questions = loaded_questions
                self.subjects = sorted(list(unique_subjects))
                self.available_subjects = sorted(list(unique_subjects)) or list(self.available_subjects)

                years_list = ["Tüm yıllar"] + sorted(list(found_years), reverse=True)
                ders_list = self.available_subjects

                self.root.after(0, lambda: self.update_dropdown_values(years_list, ders_list))
                self.root.after(0, self.update_stats)
                self.root.after(0, self.update_question_limit)
                self.root.after(0, lambda: self.questions_loaded_successfully(show_message=show_message))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Sorular yüklenirken hata oluştu: {e}"))

        self.load_button.config(text="⏳ YÜKLENİYOR...", bg=self.colors['text_secondary'])
        self.root.after(100, load_in_background)

    def questions_loaded_successfully(self, show_message=True):
        """Sorular başarıyla yüklendiğinde"""
        self.load_button.config(text=f"✅ {len(self.questions)} SORU YÜKLENDİ", bg=self.colors['success'])
        self.status_label.config(text="🟢 Hazır", fg=self.colors['success'])
        if show_message:
            messagebox.showinfo("Başarılı", f"Toplam {len(self.questions)} soru yüklendi!")
        
    def update_dropdown_values(self, years, dersler):
        """Dropdown değerlerini günceller."""
        current_years = self._selected_years()
        current_dersler = self._selected_subjects()
        current_goto_year = self.goto_year_var.get()
        current_goto_ders = self.goto_ders_var.get()

        available_years = [y for y in years if y != ALL_YEARS_LABEL]
        self.year_filter.set_values(available_years)
        self.ders_filter.set_values(dersler)
        self.goto_year_combo['values'] = sorted(available_years, reverse=True)
        self.goto_ders_combo['values'] = dersler

        self._set_filter_selection("year", [year for year in current_years if year in available_years])
        self._set_filter_selection("ders", [ders for ders in current_dersler if ders in dersler])

        goto_years = list(self.goto_year_combo['values'])
        if current_goto_year in goto_years:
            self.goto_year_var.set(current_goto_year)
        elif goto_years:
            self.goto_year_var.set(goto_years[0])

        if current_goto_ders not in dersler and dersler:
            self.goto_ders_var.set(dersler[0])
        else:
            self.goto_ders_var.set(current_goto_ders)

        self._sync_filter_dropdowns()
        self._sync_goto_dropdowns()
        self.update_question_limit()
        self._update_goto_question_list()
        self._update_konu_list()

    def on_ders_changed(self, event=None):
        """Ders değiştiğinde konu listesini ve soru limitini günceller."""
        self._sync_filter_dropdowns()
        self._update_konu_list()
        self.update_question_limit()

    def _available_years_for_subject(self, subject, include_all=False):
        years = sorted({str(q['yil']) for q in self.questions}, reverse=True)
        selected_subjects = []
        if isinstance(subject, (list, tuple, set)):
            selected_subjects = [item for item in subject if item]
        elif subject and subject != ALL_DERSLER_LABEL:
            selected_subjects = [subject]
        if selected_subjects:
            years = sorted({str(q['yil']) for q in self.questions if q['ders'] in selected_subjects}, reverse=True)
        return ([ALL_YEARS_LABEL] + years) if include_all else years

    def _available_subjects_for_year(self, year, include_all=False):
        dersler = sorted({q['ders'] for q in self.questions})
        selected_years = []
        if isinstance(year, (list, tuple, set)):
            selected_years = [item for item in year if item]
        elif year and year != ALL_YEARS_LABEL:
            selected_years = [year]
        if selected_years:
            year_ints = set()
            for item in selected_years:
                try:
                    year_ints.add(int(item))
                except Exception:
                    pass
            if year_ints:
                dersler = sorted({q['ders'] for q in self.questions if q['yil'] in year_ints})
        return ([ALL_DERSLER_LABEL] + dersler) if include_all else dersler

    def _sync_filter_dropdowns(self):
        """Ana filtrelerde sadece gerçekte var olan yıl/ders kombinasyonlarını gösterir."""
        if not self.questions:
            return

        selected_years = self._selected_years()
        selected_dersler = self._selected_subjects()

        allowed_years = self._available_years_for_subject(selected_dersler, include_all=False)
        self.year_filter.set_values(allowed_years)
        self._set_filter_selection("year", [year for year in selected_years if year in allowed_years])

        allowed_subjects = self._available_subjects_for_year(self._selected_years(), include_all=False)
        self.ders_filter.set_values(allowed_subjects)
        self._set_filter_selection("ders", [ders for ders in selected_dersler if ders in allowed_subjects])

        allowed_years = self._available_years_for_subject(self._selected_subjects(), include_all=False)
        self.year_filter.set_values(allowed_years)
        self._set_filter_selection("year", [year for year in self._selected_years() if year in allowed_years])

    def _sync_goto_dropdowns(self):
        """Soruya Git alaninda yalnizca mevcut sınav kombinasyonlarini gosterir."""
        if not self.questions:
            return

        selected_year = self.goto_year_var.get()
        selected_ders = self.goto_ders_var.get()

        allowed_years = self._available_years_for_subject(selected_ders, include_all=False)
        self.goto_year_combo['values'] = allowed_years
        if selected_year not in allowed_years:
            selected_year = allowed_years[0] if allowed_years else ""
            self.goto_year_var.set(selected_year)

        allowed_subjects = self._available_subjects_for_year(selected_year, include_all=False)
        self.goto_ders_combo['values'] = allowed_subjects
        if selected_ders not in allowed_subjects:
            selected_ders = allowed_subjects[0] if allowed_subjects else ""
            self.goto_ders_var.set(selected_ders)

        allowed_years = self._available_years_for_subject(self.goto_ders_var.get(), include_all=False)
        self.goto_year_combo['values'] = allowed_years
        if self.goto_year_var.get() not in allowed_years:
            self.goto_year_var.set(allowed_years[0] if allowed_years else "")

    def _update_konu_list(self, event=None):
        """Seçilen yıl ve derse göre mevcut konuları konu dropdown'ına yükler."""
        if not self.questions or not hasattr(self, 'konu_filter'):
            return

        qs = self._apply_question_filters(
            self.questions,
            years=self._selected_years(),
            subjects=self._selected_subjects(),
            topics=[],
        )

        normalized_topics = {
            self.normalize_topic_name(q.get('konu'))
            for q in qs
            if self.normalize_topic_name(q.get('konu'))
        }

        selected_subjects = set(self._selected_subjects())
        is_dhbt_only = bool(selected_subjects) and all(
            subject.startswith("DHBT") for subject in selected_subjects
        )

        if is_dhbt_only:
            konular = sorted(
                {topic for topic in normalized_topics if topic in ALLOWED_DHBT_TOPICS},
                key=lambda topic: topic_sort_key("DHBT", topic),
            )
        else:
            konular = sorted(normalized_topics)
        self.konu_filter.set_values(konular)
        self._set_filter_selection("konu", [konu for konu in self._selected_topics() if konu in konular])

    def resolve_visual_path(self, raw_path: str, year: int) -> str:
        """Görsel için göreli/tam yolu uygulamadaki gerçek dosya yoluna çevirir."""
        cleaned = raw_path.strip().rstrip(']').strip()
        if cleaned.startswith('[RESIM:'):
            cleaned = cleaned.split(':', 1)[1].strip()

        cleaned = cleaned.replace('/', os.sep).replace('\\', os.sep)
        base_dir = ROOT_DIR
        filename = os.path.basename(cleaned)

        candidates = []
        if os.path.isabs(cleaned):
            candidates.append(os.path.normpath(cleaned))
        else:
            candidates.append(os.path.normpath(os.path.join(str(base_dir), cleaned)))
            candidates.append(os.path.normpath(os.path.join(str(GORSSELLER_DIR), str(year), filename)))
            candidates.append(os.path.normpath(os.path.join(str(GORSSELLER_DIR), f"{year} ihl", filename)))
            candidates.append(os.path.normpath(os.path.join(str(GORSSELLER_DIR), f"{year} IHL", filename)))

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
            
            answer_markers = (
                'Doğru Cevap:',
                'Dogru Cevap:',
                'DoÄŸru Cevap:',
                'Do?ru Cevap:',
                'Do??ru Cevap:',
            )

            for block in soru_blocks:
                if 'Soru ' in block and any(marker in block for marker in answer_markers):
                    question = self.parse_single_question(block, year, subject)
                    if question:
                        questions.append(question)
                        
        except Exception as e:
            print(f"Parse hatasi {year}: {e}")
            
        return questions

    def normalize_topic_name(self, topic: str) -> str:
        """Konu adlarindaki bozuk karakterleri ve bilinen varyasyonlari duzeltir."""
        return catalog_normalize_topic_name(topic)

    def parse_single_question(self, text: str, year: int, subject: str = "DKAB") -> Dict:
        """Tek soruyu parse eder"""
        try:
            lines = text.strip().split('\n')
            
            soru_no = None
            soru_metni = []
            options = {}
            dogru_cevap = None
            aciklama = ""
            topic_candidates = []
            gorsel_var = False
            gorsel_dosyalari = []
            
            answer_prefixes = (
                'Doğru Cevap:',
                'Dogru Cevap:',
                'DoÄŸru Cevap:',
                'Do?ru Cevap:',
                'Do??ru Cevap:',
            )
            explanation_prefixes = (
                'Açıklama:',
                'Aciklama:',
                'AÃ§Ä±klama:',
                'A??klama:',
                'A????klama:',
            )
            visual_prefixes = (
                'Görsel',
                'Gorsel',
                'GÃ¶rsel',
                'G?rsel',
                'G??rsel',
                'Dosya:',
                'Konum:',
            )

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
                    normalized_topic = self.normalize_topic_name(line.split(':', 1)[1].strip())
                    if normalized_topic:
                        topic_candidates.append(normalized_topic)
                elif (
                    line
                    and not line.startswith(('A)', 'B)', 'C)', 'D)', 'E)'))
                    and not line.startswith(answer_prefixes)
                    and not line.startswith(explanation_prefixes)
                    and not line.startswith(visual_prefixes)
                    and soru_no
                    and not line.startswith('YIL:')
                    and not line.startswith('DERS:')
                ):
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
                elif line.startswith(answer_prefixes):
                    dogru_cevap = line.split(':', 1)[1].strip()
                elif line.startswith(explanation_prefixes):
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
                    elif 'Görsel dosya adı:' in line: dosya_adi = line.split('Görsel dosya adı:')[1].strip()
                    elif 'Gorsel dosya adi:' in line: dosya_adi = line.split('Gorsel dosya adi:')[1].strip()
                    elif 'Dosya:' in line: dosya_adi = line.split('Dosya:')[1].strip()
                    
                    if dosya_adi:
                        gorsel_dosyalari.append(self.resolve_visual_path(dosya_adi, year))
                
                i += 1
            
            konu = ""
            for candidate in topic_candidates:
                if candidate in ALLOWED_DHBT_TOPICS:
                    konu = candidate
                    break
            if not konu and topic_candidates:
                konu = topic_candidates[-1]

            if (
                soru_no
                and len(options) >= 2
                and dogru_cevap
                and not self.should_skip_dhbt_common_question(year, subject, soru_no)
            ):
                return {
                    "yil": year,
                    "ders": subject,
                    "konu": self.normalize_topic_name(konu) if konu else subject,
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
            print(f"Parse hatasi: {e}")
            
        return None

    def parse_questions_from_file(self, file_path: str, year: int, subject: str = "DKAB") -> List[Dict]:
        """Dosyadan soruları ortak parser ile yükler."""
        return parse_questions_from_exam_file(
            Path(file_path),
            year,
            subject,
            base_dir=WORDE_DIR,
            default_topic=None,
            visual_resolver=self.resolve_visual_path,
        )

    def parse_single_question(self, text: str, year: int, subject: str = "DKAB") -> Dict:
        """Tek soruyu ortak parser ile çözer."""
        return parse_single_question_block(
            text,
            year,
            subject,
            base_dir=WORDE_DIR,
            default_topic=None,
            visual_resolver=self.resolve_visual_path,
        )

    def get_question_limit_for_year(self, selected_year, selected_ders, selected_konu=None):
        """Yıla, derse ve konuya göre maksimum soru sayısını döner."""
        if self.questions:
            selected_years = selected_year if isinstance(selected_year, (list, tuple, set)) else self._deserialize_multi_values(selected_year, ALL_YEARS_LABEL)
            selected_dersler = selected_ders if isinstance(selected_ders, (list, tuple, set)) else self._deserialize_multi_values(selected_ders, ALL_DERSLER_LABEL)
            selected_konular = selected_konu if isinstance(selected_konu, (list, tuple, set)) else self._deserialize_multi_values(selected_konu, ALL_KONULAR_LABEL)
            qs = self._apply_question_filters(self.questions, selected_years, selected_dersler, selected_konular)
            return len(qs) if qs else 75
        return 75

    def update_question_limit(self, event=None):
        """Seçilen yıla, derse ve konuya göre soru limitini günceller."""
        selected_year = self._selected_years()
        selected_ders = self._selected_subjects()
        selected_konu = self._selected_topics() if hasattr(self, 'konu_var') else []
        max_questions = self.get_question_limit_for_year(selected_year, selected_ders, selected_konu)
        self.num_spinbox.config(to=max_questions)
        self.num_var.set(str(max_questions if max_questions >= 1 else 1))

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
        self.stop_speech(reset_status=False)
        if not self.questions:
            messagebox.showwarning("Uyarı", "Önce soruları yükleyin!")
            return
        
        try:
            num_questions = int(self.num_var.get())
            selected_year = self._selected_years()
            selected_ders = self._selected_subjects()
            selected_konu = self._selected_topics() if hasattr(self, 'konu_var') else []
            max_questions = self.get_question_limit_for_year(selected_year, selected_ders, selected_konu)
            if num_questions < 1 or num_questions > max_questions:
                messagebox.showwarning("Uyarı", f"Soru sayısı 1-{max_questions} arasında olmalı!")
                return
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir soru sayısı girin!")
            return

        self._stop_countdown()

        # Filter questions by year, subject, and konu if selected
        available_questions = self._apply_question_filters(self.questions)
            
        if not available_questions:
            messagebox.showwarning("Uyarı", "Seçilen kriterlere uygun soru bulunamadı!")
            return
        
        if len(available_questions) < num_questions:
            num_questions = len(available_questions)
        
        # Select question order according to user preference
        if self._shuffle_questions_enabled():
            self.quiz_questions = random.sample(available_questions, num_questions)
        else:
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
                hours = int(self.time_hours_var.get())
                minutes = int(self.time_minutes_var.get())
                seconds = int(self.time_seconds_var.get())
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir süre girin!")
                return
            if hours < 0 or minutes < 0 or seconds < 0:
                messagebox.showwarning("Uyarı", "Süre alanları negatif olamaz!")
                return
            total_seconds = hours * 3600 + minutes * 60 + seconds
            if total_seconds <= 0:
                messagebox.showwarning("Uyarı", "Süre 0 saniyeden büyük olmalı!")
                return
            self._start_countdown(total_seconds)
        else:
            self.remaining_seconds = 0
            self._set_status_ready()
        
        # Start quiz
        self.show_question()
    
    def show_question(self):
        self.current_view = "question"
        self.stop_speech(reset_status=False)
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

        self.create_speech_controls(content_frame, question, include_navigation=True)
        
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
        
        # Shuffle options only when the selected order mode requests it
        if self._shuffle_options_enabled():
            random.shuffle(options)
        
        self.option_vars = {}
        self.option_map = {}
        self.option_buttons = {}
        
        for i, (key, value) in enumerate(options, 1):
            self.option_map[str(i)] = key
            display_label = f"{key})"
            
            option_frame = tk.Frame(options_frame, bg=self.colors['card'])
            option_frame.pack(fill=tk.X, pady=8)
            
            # Option button
            var = tk.StringVar()
            self.option_vars[str(i)] = var
            
            option_btn = tk.Button(option_frame, text=f"{display_label} {value}", 
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
        
        # Testi Bitir button (only in review flow modes: Test Sonu Değerlendir and Süreli)
        if self._uses_review_flow():
            finish_test_btn = self.create_button(nav_frame, "🛑 TESTİ BİTİR", 
                                                self.confirm_finish_test, self.colors['danger'])
            finish_test_btn.pack(side=tk.RIGHT, padx=5, ipady=2)
        
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
        
        nav_frame.pack_forget()

        # Restore selection from history if exists
        self.restore_selection_from_history(question)
        self.maybe_auto_read_question(question)
    
    def confirm_finish_test(self):
        """Testi bitirmek için onay dialogu gösterir"""
        answered = len(self.user_answers) if hasattr(self, 'user_answers') else 0
        unanswered = self.total_questions - answered
        
        if unanswered > 0:
            result = messagebox.askyesno(
                "Emin misiniz?",
                f"Testi bitirmek istediğinizden emin misiniz?\n\n"
                f"Yanıtlanan soru: {answered}\n"
                f"Yanıtlanmayan soru: {unanswered}\n\n"
                f"Yanıtlanmayan sorular değerlendirilmeyecektir."
            )
        else:
            result = messagebox.askyesno(
                "Emin misiniz?",
                "Testi bitirmek istediğinizden emin misiniz?"
            )
        
        if result:
            if self._uses_review_flow():
                self.show_review_screen()
            else:
                self.show_results()
    
    def select_option(self, var, option_num):
        """Seçenek seçildiğinde - moda göre davranır"""
        self._cancel_speech_sequence()
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
                self.speak_answer_feedback(question, True)
            else:
                selected_button.config(bg=self.colors['danger'], fg='white')
                # Also highlight the correct answer in green
                for opt_num, sik_key in self.option_map.items():
                    if sik_key == question['dogru_cevap']:
                        self.option_buttons[opt_num].config(bg=self.colors['success'], fg='white')
                        break
                # Show error message on the same screen
                self.show_feedback_on_screen(question, False)
                self.speak_answer_feedback(question, False)
        else:
            # Review mode - just highlight selection, no colors, auto-advance after 2 seconds
            self.option_buttons[option_num].config(bg=self.colors['accent'], fg='white')
            
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
                            self.option_buttons[option_num].config(bg=self.colors['accent'], fg='white')
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
        self._cancel_speech_sequence()
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
        
        self.speak_answer_feedback(
            question,
            user_choice_letter == question['dogru_cevap']
        )
        
        # Move to next question
        if self.current_index < len(self.quiz_questions) - 1:
            self.current_index += 1
            self.show_question()
        else:
            # Show review screen
            self.show_review_screen()
    
    def show_review_screen(self):
        self.current_view = "review"
        self.stop_speech(reset_status=False)
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
            self._update_goto_hint(ders, nums)
        except Exception:
            pass

    def _on_goto_filter_changed(self, event=None):
        """Soruya Git yil/ders secimleri degistiginde dropdownlari esler."""
        self._sync_goto_dropdowns()
        self._update_goto_question_list()

    def _update_goto_hint(self, ders, nums):
        """Soruya Git alaninda secilen dersin soru araligini aciklar."""
        if not hasattr(self, 'goto_hint_label'):
            return

        if not nums:
            self.goto_hint_label.config(text="Bu seçim için yüklü soru bulunamadı.")
            return

        min_no = min(nums)
        max_no = max(nums)

        if ders == "DHBT Ortak (1-20)":
            hint = "Ortak blok gösteriliyor. Bu bölümde yalnızca 1-20 arası sorular var."
        elif ders in {"DHBT Lisans", "DHBT Önlisans", "DHBT Ortaöğretim"}:
            hint = f"Bu ders için özel bölüm gösteriliyor. Kullanılabilir soru aralığı: {min_no}-{max_no}."
        else:
            hint = f"Kullanılabilir soru aralığı: {min_no}-{max_no}."

        self.goto_hint_label.config(text=hint)

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
        self.stop_speech(reset_status=False)
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

        self.create_speech_controls(inner, question)

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
            fg = 'white' if is_correct else self.colors['text']
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

        self.maybe_auto_read_question(question)

    def next_question(self):
        """Sonraki soruya geçer"""
        self.stop_speech(reset_status=False)
        self._store_current_question_time()
        if self._next_timer:
            self.root.after_cancel(self._next_timer)
            self._next_timer = None
        self.current_index += 1
        self.show_question()
    
    def previous_question(self):
        """Önceki soruya döner"""
        self.stop_speech(reset_status=False)
        self._store_current_question_time()
        if self._next_timer:
            self.root.after_cancel(self._next_timer)
            self._next_timer = None
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()
    
    def show_results(self):
        self.current_view = "results"
        self.stop_speech(reset_status=False)
        """Sonuçları gösterir - show_review_screen ile aynı stil"""
        self._store_current_question_time()
        if self.test_start_time is not None:
            self.total_elapsed_seconds = max(0, int(time.monotonic() - self.test_start_time))
        self._stop_countdown()
        self._stop_elapsed_tracking()
        self.remaining_seconds = 0
        self._set_status_ready()

        for widget in self.main_content.winfo_children():
            widget.destroy()

        results_card = self.create_card(self.main_content, "📋 TEST DEĞERLENDİRME")
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
            text=f"Toplam Süre: {self._format_seconds(self.total_elapsed_seconds)}",
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

        review_content = "SORU DEĞERLENDİRMESİ:\n" + "=" * 50 + "\n\n"

        for i, q in enumerate(self.quiz_questions, 1):
            status = "İşaretlenmedi"
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
                    status = "✅ DOĞRU" if is_correct else "❌ YANLIŞ"
                    break

            konu_display = (
                f", Konu: {q['konu']}"
                if q.get('konu') and q['konu'] != q['ders'] else ""
            )

            review_content += (
                f"Soru {i} (Sınav: {q['ders']}, Yıl: {q['yil']}, "
                f"No: {q['soru_no']}{konu_display}) - {status}\n"
            )
            review_content += f"Soru: {q['soru_metni'][:80]}...\n"
            review_content += f"Sizin cevabınız: {selected_txt}\n"
            review_content += f"Doğru cevap: {correct_txt}\n"
            review_content += f"Süre: {self._format_seconds(elapsed)}\n"

            if not is_correct and q.get('aciklama'):
                review_content += f"Açıklama: {q['aciklama'][:100]}...\n"

            review_content += "-" * 50 + "\n\n"

        review_text.insert(tk.END, review_content)
        review_text.config(state=tk.DISABLED)

        button_frame = tk.Frame(content_frame, bg=self.colors['card'])
        button_frame.pack(fill=tk.X, pady=20)

        new_test_btn = self.create_button(
            button_frame,
            "🔄 YENİ TEST",
            self.new_test,
            self.colors['success']
        )
        new_test_btn.pack(side=tk.LEFT, padx=10, ipady=8)

        menu_btn = self.create_button(
            button_frame,
            "🏠 ANA MENÜ",
            self.show_welcome_screen,
            self.colors['text_secondary']
        )
        menu_btn.pack(side=tk.LEFT, padx=10, ipady=8)

    def new_test(self):
        """Yeni test başlatır"""
        self.stop_speech(reset_status=False)
        self.start_quiz()

def main():
    root = tk.Tk()
    app = ModernDKABQuiz(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        try:
            app.on_close()
        except Exception:
            root.destroy()

if __name__ == "__main__":
    main()
