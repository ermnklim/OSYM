#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DKAB ÖABT Sınav Analiz Aracı
Yıllara ve konulara göre soru dağılımı analizi
Otomatik güncellenir - yeni sınav eklendiğinde bildirim yapar
"""

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from project_paths import PYTHON_VERISI_DIR, WORDE_DIR
    from question_bank import (
        format_subject_label as format_exam_subject_label,
        has_dhbt_common_file as question_bank_has_dhbt_common_file,
        iter_exam_files,
        load_question_bank,
        parse_questions_from_file as parse_questions_from_exam_file,
        parse_single_question_block,
        should_skip_dhbt_common_question as question_bank_should_skip_dhbt_common_question,
    )
    from topic_catalog import (
        is_known_topic,
        normalize_topic_name,
        sort_topics_for_exam_family,
    )
    from topic_text_parser import parse_topic_text_file
except ImportError:
    from Python_Verisi.project_paths import PYTHON_VERISI_DIR, WORDE_DIR
    from Python_Verisi.question_bank import (
        format_subject_label as format_exam_subject_label,
        has_dhbt_common_file as question_bank_has_dhbt_common_file,
        iter_exam_files,
        load_question_bank,
        parse_questions_from_file as parse_questions_from_exam_file,
        parse_single_question_block,
        should_skip_dhbt_common_question as question_bank_should_skip_dhbt_common_question,
    )
    from Python_Verisi.topic_catalog import (
        is_known_topic,
        normalize_topic_name,
        sort_topics_for_exam_family,
    )
    from Python_Verisi.topic_text_parser import parse_topic_text_file

ANALYSIS_FILE = PYTHON_VERISI_DIR / "analiz_sonuc.txt"
ANALYSIS_JSON = PYTHON_VERISI_DIR / "analiz_data.json"
LAST_CHECK_FILE = PYTHON_VERISI_DIR / "last_check.json"
EXAM_DIR = WORDE_DIR

EXAM_FAMILY_LABELS = {
    "DKAB": "ÖABT DKAB",
    "IHL": "ÖABT İHL",
    "MBSTS": "MBSTS",
}

SUBTOPIC_KEYWORDS = {
    "Kur'an-ı Kerim ve Tecvid": [
        ("Tecvit kuralları", [r"idgam", r"ihfa", r"izhar", r"iklab", r"med", r"vakf", r"\btecvit\b"]),
        ("Mahreç ve sıfat", [r"mahreç", r"mahrec", r"sıfat", r"sifat", r"safir", r"hemş", r"hems", r"gunne", r"tefess"]),
        ("Kıraat", [r"kıraat", r"kiraat", r"nafi", r"ibn kesir", r"ibn amir", r"kisai", r"aşere", r"mücahid"]),
        ("Kur'an tarihi", [r"mushaf", r"hareke", r"noktalan", r"eb[üu]'?l-esved", r"halil b\. ahmed", r"cem['’]"]),
        ("Sure ve kavim bilgisi", [r"\bsure\b", r"\bayet\b", r"ashab", r"kavim", r"meryem", r"mutaffif", r"medyen"]),
    ],
    "Tefsir": [
        ("Sebeb-i nüzul", [r"sebeb[- ]i nüzul", r"sebeb[- ]i nuzul", r"nüzul", r"nuzul"]),
        ("Nesih", [r"nesih", r"mensuh", r"nasih"]),
        ("Mekki-Medeni", [r"mekki", r"medeni"]),
        ("Tefsir usulü", [r"tefsir", r"tevil", r"rivayet", r"dirayet", r"içtimai", r"ictimai"]),
        ("Kur'an ilimleri", [r"vücuh", r"nezair", r"mübhemat", r"müşkil", r"müteşab", r"mecaz"]),
        ("Kıssalar ve sureler", [r"kıssa", r"sure", r"meryem", r"ashab", r"peygamber"]),
    ],
    "Hadis": [
        ("Hadis usulü", [r"sened", r"isnad", r"rav", r"muttasıl", r"munkatı", r"inkıta", r"tedlis", r"muallak", r"mürsel", r"hasen", r"zayıf"]),
        ("Hadis kaynakları", [r"buhari", r"müslim", r"müsned", r"sünen", r"cami", r"muvatta", r"ibnü'?s-salah", r"tedrib"]),
        ("Ravi ve cerh-ta'dil", [r"cerh", r"ta['’]dil", r"sika", r"adalet", r"zabt", r"vefayat"]),
        ("Konulu hadisler", [r"niyet", r"müslüman", r"hadis", r"sünnet"]),
    ],
    "Fıkıh": [
        ("Taharet", [r"abdest", r"gus", r"mest", r"necaset", r"temizlik", r"taharet"]),
        ("Namaz", [r"namaz", r"rekât", r"rekat", r"sehiv", r"itikâf", r"itikaf", r"mesbuk", r"lahik", r"muktedi"]),
        ("Oruç", [r"oruç", r"oruc", r"imsak", r"ramazan", r"kefaret orucu"]),
        ("Zekât", [r"zekât", r"zekat", r"nisab", r"mülkiyet", r"toprak mahsul"]),
        ("Hac ve umre", [r"\bhac\b", r"umre", r"ihram", r"tavaf", r"sa'y", r"müzdelife", r"mina", r"arafat"]),
        ("Kurban", [r"kurban", r"büyükbaş", r"büyükbas", r"küçükbaş", r"kucukbas"]),
        ("Aile hukuku", [r"nikâh", r"nikah", r"mehir", r"boşan", r"talak", r"iddet", r"hidane"]),
        ("Miras", [r"miras", r"tereke", r"vasiyet", r"muris", r"asabe"]),
        ("Muamelat", [r"alışveriş", r"alisveris", r"satış", r"satis", r"rehin", r"karz", r"şirket", r"sirket", r"muhayee", r"mudarebe", r"murabaha"]),
        ("Yemin, adak, kefaret", [r"yemin", r"adak", r"kefaret"]),
    ],
    "Fıkıh Usulü": [
        ("Kıyas", [r"kıyas", r"kiyas", r"illet", r"hikmet"]),
        ("İcma", [r"icma", r"sükûti", r"sükuti", r"sarih icma"]),
        ("İstishab ve istihsan", [r"istishab", r"istihsan"]),
        ("Makasıd", [r"makasıd", r"makasid", r"şeria", r"seria", r"zaruret", r"haciyat", r"tahsiniyat"]),
        ("Lafızlar ve delalet", [r"lafız", r"lafiz", r"hafi", r"müşkil", r"mücmel", r"müteşabih", r"vacib", r"mukayyed"]),
        ("Usul metotları", [r"fukaha", r"mütekellim", r"metodu", r"tümevar", r"meseleci"]),
    ],
    "Kelam / Akaid": [
        ("İman", [r"\biman\b", r"mürcie", r"mürtekib", r"büyük günah", r"murtekip"]),
        ("Kader", [r"kader", r"kaza", r"istitaat", r"cebr", r"cebriy", r"irade", r"tekvin"]),
        ("Tevhid ve sıfatlar", [r"tevhid", r"sıfat", r"sifat", r"vahdaniyet", r"uluhiyet", r"rü'yet", r"ruyet"]),
        ("Kelam ekolleri", [r"mutezile", r"eşari", r"eş'ar", r"maturid", r"cehmi", r"mürcie"]),
        ("Kelam yöntemi", [r"cevher", r"araz", r"kozmoloji", r"burhan", r"gazali", r"cüveyni", r"nazzam", r"kümun", r"zuhur"]),
    ],
    "Siyer": [
        ("Mekke dönemi", [r"mekke", r"darünnedve", r"darunnedve", r"boykot", r"taif"]),
        ("Medine dönemi", [r"medine", r"vesika", r"vesikası", r"vesikasi", r"suffe"]),
        ("Gazve ve seriyyeler", [r"gazve", r"seriyye", r"uhud", r"huneyn", r"hayber", r"hendek", r"mute", r"zatüsselasil"]),
        ("Hicret ve Hudeybiye", [r"hicret", r"hudeybiye"]),
        ("Veda dönemi", [r"veda hutbesi", r"veda"]),
    ],
    "İslam Tarihi": [
        ("Dört halife", [r"ebubekir", r"ömer", r"osman", r"ali", r"hulefa", r"raşidin", r"rasidin"]),
        ("Emeviler", [r"emevi", r"mervan", r"süfyani", r"sufyani"]),
        ("Abbasiler", [r"abbasi", r"memun", r"mihne"]),
        ("Türk-İslam devletleri", [r"toluno", r"selçuk", r"osmanlı", r"memlük", r"memluk"]),
    ],
    "İslam Mezhepleri ve Akımları": [
        ("Şia ve kolları", [r"şia", r"si[aâ]", r"imami", r"zeyd", r"ismail", r"nusayri"]),
        ("Haricilik", [r"harici", r"ezarika", r"ibazi"]),
        ("Modern akımlar", [r"bahai", r"kadıyan", r"kadiyan", r"vehhabi"]),
    ],
    "Mezhepler Tarihi": [
        ("Şia ve kolları", [r"şia", r"si[aâ]", r"imami", r"zeyd", r"ismail", r"nusayri"]),
        ("Haricilik", [r"harici", r"ezarika", r"ibazi"]),
        ("Modern akımlar", [r"bahai", r"kadıyan", r"kadiyan", r"vehhabi", r"dürzi", r"durzi"]),
    ],
    "Dinler Tarihi": [
        ("Hristiyanlık", [r"hristiyan", r"incil", r"teslis", r"vaftiz", r"evharist", r"misyoner"]),
        ("Yahudilik", [r"yahudi", r"tevrat", r"roş", r"şofar", r"şabat"]),
        ("Hint dinleri", [r"hindu", r"vişnu", r"visnu", r"karma", r"nirvana", r"avatara", r"buda"]),
        ("Diğer dinler", [r"mecusi", r"şinto", r"sabi", r"manihe", r"tao"]),
    ],
    "Din Hizmetleri ve Hitabet": [
        ("Hutbe ve vaaz", [r"hutbe", r"vaaz", r"hitabet"]),
        ("İrşat ve yaygın din hizmeti", [r"irşat", r"irsat", r"yaygın din hizmet", r"diyanet"]),
    ],
}


def format_subject_label(subject: str) -> str:
    subject = str(subject or "").replace("_", " ").strip()
    replacements = {
        "Onlisans": "Önlisans",
        "Ortaogretim": "Ortaöğretim",
        "ogretim": "öğretim",
        "DHBT Ortak": "DHBT Ortak (1-20)",
    }
    for source, target in replacements.items():
        subject = subject.replace(source, target)
    return subject


def get_exam_family(subject: str) -> str:
    subject = format_subject_label(subject)
    if subject.startswith("DHBT"):
        return "DHBT"
    return EXAM_FAMILY_LABELS.get(subject, subject)


def extract_subtopics(question_text: str, topic: str) -> List[str]:
    text = " ".join((question_text or "").split()).casefold()
    matched = []
    for label, patterns in SUBTOPIC_KEYWORDS.get(topic, []):
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            matched.append(label)
    return matched or ["Genel / Diğer"]


def sort_topics_for_priority(exam_family: str, topic_counts: Dict[str, int]) -> List[Tuple[str, int]]:
    return sort_topics_for_exam_family(exam_family, topic_counts)


def has_dhbt_common_file(year: int) -> bool:
    return (EXAM_DIR / f"{year}_DHBT_Ortak_Sorulari.txt").exists()


def should_skip_dhbt_common_question(year: int, subject: str, soru_no: int) -> bool:
    if soru_no > 20:
        return False
    if subject not in {"DHBT Lisans", "DHBT Önlisans", "DHBT Ortaöğretim"}:
        return False
    return has_dhbt_common_file(year)

def format_subject_label(subject: str) -> str:
    return format_exam_subject_label(subject)


def has_dhbt_common_file(year: int) -> bool:
    return question_bank_has_dhbt_common_file(year, base_dir=EXAM_DIR)


def should_skip_dhbt_common_question(year: int, subject: str, soru_no: int) -> bool:
    return question_bank_should_skip_dhbt_common_question(year, subject, soru_no, base_dir=EXAM_DIR)


def get_file_mod_time(file_path):
    try:
        return Path(file_path).stat().st_mtime
    except:
        return 0

def get_last_check():
    try:
        if os.path.exists(LAST_CHECK_FILE):
            with open(LAST_CHECK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"files": {}, "last_run": ""}

def save_last_check(data):
    try:
        with open(LAST_CHECK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def check_new_files():
    """Yeni eklenen dosyaları kontrol eder"""
    last_check = get_last_check()
    current_files = {}
    new_files = []
    
    if EXAM_DIR.exists():
        for file_path in EXAM_DIR.iterdir():
            filename = file_path.name
            match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
            if match:
                mod_time = get_file_mod_time(file_path)
                current_files[filename] = mod_time
                
                if filename not in last_check.get("files", {}):
                    new_files.append(filename)
                elif last_check["files"].get(filename, 0) != mod_time:
                    new_files.append(f"{filename} (güncellendi)")
    
    last_check["files"] = current_files
    last_check["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_last_check(last_check)
    
    return new_files


def load_summary_topic_reports() -> List[Dict]:
    reports = []
    for filename in ("dkab_ozet.txt", "dkab_kodlamali_ozet.txt"):
        path = PYTHON_VERISI_DIR / filename
        if not path.exists():
            continue
        try:
            reports.append(parse_topic_text_file(path))
        except Exception as exc:
            reports.append(
                {
                    "path": str(path),
                    "main_sections": [],
                    "topic_blocks": [],
                    "mapped_topics": [],
                    "warnings": [f"{filename} ayrıştırılamadı: {exc}"],
                }
            )
    return reports


def build_topic_quality_report(questions: List[Dict]) -> Dict[str, object]:
    missing_topics = []
    alias_corrections = set()
    unknown_topic_values = Counter()
    subject_topic_counts = defaultdict(Counter)

    for question in questions:
        raw_values = question.get("raw_topic_values", [])
        if question.get("topic_missing") or not raw_values:
            missing_topics.append((question["yil"], question["ders"], question["soru_no"]))

        for raw_topic, normalized_topic in question.get("topic_alias_corrections", []):
            alias_corrections.add(f"{raw_topic} -> {normalized_topic}")

        for raw_topic in raw_values:
            normalized = normalize_topic_name(raw_topic)
            if raw_topic and not is_known_topic(normalized):
                unknown_topic_values[normalized] += 1

        normalized_topic = normalize_topic_name(question.get("konu", ""))
        if normalized_topic:
            subject_topic_counts[question["ders"]][normalized_topic] += 1

    rare_topic_usage = []
    for subject, counter in subject_topic_counts.items():
        for topic_name, count in counter.items():
            if count <= 1:
                rare_topic_usage.append((subject, topic_name, count))
    rare_topic_usage.sort(key=lambda item: (item[0], item[1]))

    summary_reports = load_summary_topic_reports()
    summary_topics = set()
    summary_warnings = []
    for report in summary_reports:
        summary_topics.update(report.get("mapped_topics", []))
        summary_warnings.extend(report.get("warnings", []))

    question_topics = sorted(
        {
            normalize_topic_name(question.get("konu", ""))
            for question in questions
            if is_known_topic(question.get("konu", ""))
        }
    )
    summary_topics = sorted(topic for topic in summary_topics if topic)

    return {
        "missing_topics": missing_topics,
        "alias_corrections": sorted(alias_corrections),
        "unknown_topic_values": unknown_topic_values.most_common(),
        "rare_topic_usage": rare_topic_usage,
        "question_topics_without_summary": sorted(set(question_topics) - set(summary_topics)),
        "summary_topics_without_questions": sorted(set(summary_topics) - set(question_topics)),
        "summary_warnings": sorted(set(summary_warnings)),
        "summary_files": [Path(report.get("path", "")).name for report in summary_reports if report.get("path")],
    }


def append_topic_quality_report(text: List[str], quality_report: Dict[str, object]) -> None:
    text.append("KONU KALİTE RAPORU")
    text.append("-" * 70)

    missing_topics = quality_report["missing_topics"]
    if missing_topics:
        text.append("Boş veya eksik KONU etiketleri:")
        for yil, ders, soru_no in missing_topics[:20]:
            text.append(f"  - {yil} {ders} Soru {soru_no}")
    else:
        text.append("Boş KONU etiketi bulunmadı.")

    alias_corrections = quality_report["alias_corrections"]
    if alias_corrections:
        text.append("")
        text.append("Alias ile düzeltilen konu adları:")
        for row in alias_corrections[:20]:
            text.append(f"  - {row}")

    unknown_topic_values = quality_report["unknown_topic_values"]
    if unknown_topic_values:
        text.append("")
        text.append("Kanonik liste dışında kalan konu adları:")
        for topic_name, count in unknown_topic_values[:20]:
            text.append(f"  - {topic_name}: {count}")

    rare_topic_usage = quality_report["rare_topic_usage"]
    if rare_topic_usage:
        text.append("")
        text.append("Ders içinde nadir görülen konu kullanımları:")
        for subject, topic_name, count in rare_topic_usage[:20]:
            text.append(f"  - {subject} | {topic_name}: {count}")

    question_topics_without_summary = quality_report["question_topics_without_summary"]
    text.append("")
    text.append("Soru havuzunda olup özet metninde eşleşmeyen konular:")
    if question_topics_without_summary:
        for topic_name in question_topics_without_summary:
            text.append(f"  - {topic_name}")
    else:
        text.append("  - Tüm kanonik soru konuları özet tarafında eşleşiyor.")

    summary_topics_without_questions = quality_report["summary_topics_without_questions"]
    text.append("")
    text.append("Özet tarafında olup soru havuzunda görünmeyen konu eşleşmeleri:")
    if summary_topics_without_questions:
        for topic_name in summary_topics_without_questions:
            text.append(f"  - {topic_name}")
    else:
        text.append("  - Özet tarafındaki eşleşmeler soru havuzuyla uyumlu.")

    summary_warnings = quality_report["summary_warnings"]
    if summary_warnings:
        text.append("")
        text.append("Özet başlığı uyarıları:")
        for warning in summary_warnings[:20]:
            text.append(f"  - {warning}")

    text.append("-" * 70)
    text.append("")

def parse_questions_from_file(file_path: str, year: int, subject: str = "DKAB") -> List[Dict]:
    """Dosyadan soruları parse eder"""
    questions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = content.replace('---SONRAKİ SORU---', '---SONRAKI SORU---')
        content = content.replace('---SONRAKÄ° SORU---', '---SONRAKI SORU---')
        soru_blocks = content.split('---SONRAKI SORU---')
        
        for block in soru_blocks:
            if 'Soru ' in block and ('Doğru Cevap:' in block or 'Dogru Cevap:' in block or 'DoÄŸru Cevap:' in block):
                question = parse_single_question(block, year, subject)
                if question:
                    questions.append(question)
                    
    except Exception as e:
        print(f"Parse hatası {year}: {e}")
        
    return questions

def parse_single_question(text: str, year: int, subject: str = "DKAB") -> Dict:
    """Tek soruyu parse eder"""
    try:
        lines = text.strip().split('\n')
        
        soru_no = None
        soru_metni = []
        topic_candidates = []
        raw_topic_values = []
        alias_corrections = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Soru ') and ':' in line:
                soru_no_str = line.split()[1].replace(':', '')
                try:
                    soru_no = int(soru_no_str)
                except ValueError:
                    soru_no = None
            elif line.startswith('KONU:'):
                raw_topic = line.split(':', 1)[1].strip()
                raw_topic_values.append(raw_topic)
                normalized_topic = normalize_topic_name(raw_topic)
                if raw_topic and normalized_topic and raw_topic != normalized_topic:
                    alias_corrections.append((raw_topic, normalized_topic))
                if normalized_topic:
                    topic_candidates.append(normalized_topic)
            elif soru_no and not any(line.startswith(x) for x in ['A)', 'B)', 'C)', 'D)', 'E)', 'Doğru', 'Dogru', 'Açıklama', 'Aciklama', '[RESIM', 'Görsel', 'Gorsel']):
                soru_metni.append(line)

        konu = ""
        for candidate in topic_candidates:
            if is_known_topic(candidate):
                konu = normalize_topic_name(candidate)
                break
        if not konu and topic_candidates:
            konu = topic_candidates[-1]

        if soru_no and not should_skip_dhbt_common_question(year, subject, soru_no):
            soru_metni_birlesik = "\n".join(soru_metni).strip()
            konu_adi = konu if konu else "Diğer"
            return {
                "yil": year,
                "ders": subject,
                "sinav_aile": get_exam_family(subject),
                "konu": konu_adi,
                "topic_missing": not any(item.strip() for item in raw_topic_values),
                "topic_known": is_known_topic(konu_adi),
                "raw_topic_values": raw_topic_values,
                "topic_alias_corrections": alias_corrections,
                "soru_no": soru_no,
                "soru_metni": soru_metni_birlesik,
                "alt_basliklar": extract_subtopics(soru_metni_birlesik, konu_adi)
            }
    except:
        pass
    return None

def analyze_all_exams():
    """Tüm sınavları analiz eder"""
    all_questions = []
    years_data = defaultdict(lambda: defaultdict(int))
    konu_data = defaultdict(lambda: defaultdict(int))
    
    if EXAM_DIR.exists():
        for file_path in EXAM_DIR.iterdir():
            filename = file_path.name
            match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
            if match:
                year = int(match.group(1))
                subject = format_subject_label(match.group(2))
                questions = parse_questions_from_file(file_path, year, subject)
                all_questions.extend(questions)
                
                for q in questions:
                    years_data[q['yil']][q['ders']] += 1
                    konu_data[q['konu']][q['ders']] += 1
    
    return all_questions, years_data, konu_data

def parse_questions_from_file(file_path: str, year: int, subject: str = "DKAB") -> List[Dict]:
    """Dosyadan soruları parse eder."""
    try:
        questions = parse_questions_from_exam_file(
            Path(file_path),
            year,
            subject,
            base_dir=EXAM_DIR,
            default_topic="Diğer",
        )
    except Exception as exc:
        print(f"Parse hatası {year}: {exc}")
        return []

    for question in questions:
        konu_adi = normalize_topic_name(question.get("konu", "")) or "Diğer"
        question["sinav_aile"] = get_exam_family(subject)
        question["konu"] = konu_adi
        question["topic_known"] = is_known_topic(konu_adi)
        question["alt_basliklar"] = extract_subtopics(question.get("soru_metni", ""), konu_adi)
    return questions


def parse_single_question(text: str, year: int, subject: str = "DKAB") -> Dict:
    """Tek soruyu parse eder."""
    question = parse_single_question_block(
        text,
        year,
        subject,
        base_dir=EXAM_DIR,
        default_topic="Diğer",
    )
    if not question:
        return None

    konu_adi = normalize_topic_name(question.get("konu", "")) or "Diğer"
    question["sinav_aile"] = get_exam_family(subject)
    question["konu"] = konu_adi
    question["topic_known"] = is_known_topic(konu_adi)
    question["alt_basliklar"] = extract_subtopics(question.get("soru_metni", ""), konu_adi)
    return question


def analyze_all_exams():
    """Tüm sınavları analiz eder."""
    all_questions, _, _ = load_question_bank(base_dir=EXAM_DIR, default_topic="Diğer")
    years_data = defaultdict(lambda: defaultdict(int))
    konu_data = defaultdict(lambda: defaultdict(int))

    for question in all_questions:
        konu_adi = normalize_topic_name(question.get("konu", "")) or "Diğer"
        question["sinav_aile"] = get_exam_family(question.get("ders", ""))
        question["konu"] = konu_adi
        question["topic_known"] = is_known_topic(konu_adi)
        question["alt_basliklar"] = extract_subtopics(question.get("soru_metni", ""), konu_adi)
        years_data[question["yil"]][question["ders"]] += 1
        konu_data[konu_adi][question["ders"]] += 1

    return all_questions, years_data, konu_data


def generate_analysis_text():
    """Analiz metnini oluşturur"""
    questions, years_data, konu_data = analyze_all_exams()
    new_files = check_new_files()
    quality_report = build_topic_quality_report(questions)
    
    total = len(questions)
    all_subjects = sorted({subject for year_map in years_data.values() for subject in year_map.keys()})
    subject_totals = {
        subject: sum(year_map.get(subject, 0) for year_map in years_data.values())
        for subject in all_subjects
    }
    
    text = []
    text.append("=" * 70)
    text.append("DKAB ÖABT SORU ANALİZ RAPORU")
    text.append(f"Oluşturulma: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    text.append("=" * 70)
    
    if new_files:
        text.append("")
        text.append("🔔 YENİ EKLENEN DOSYALAR:")
        for f in new_files:
            text.append(f"   • {f}")
        text.append("")
    
    text.append("")
    text.append("📊 GENEL İSTATİSTİKLER")
    text.append("-" * 50)
    text.append(f"Toplam Soru Sayısı: {total}")
    for subject in all_subjects:
        text.append(f"  - {subject}: {subject_totals[subject]} soru")
    text.append("")
    
    text.append("📅 YILLARA GÖRE DAĞILIM")
    text.append("-" * 50)
    header = f"{'Yıl':<8}" + "".join(f" {subject:<18}" for subject in all_subjects) + f" {'Toplam':<10}"
    text.append(header)
    text.append("-" * 50)
    
    sorted_years = sorted(years_data.keys(), reverse=True)
    for year in sorted_years:
        row_counts = [years_data[year].get(subject, 0) for subject in all_subjects]
        row = f"{year:<8}" + "".join(f" {count:<18}" for count in row_counts) + f" {sum(row_counts):<10}"
        text.append(row)
    
    text.append("-" * 50)
    text.append("")
    
    text.append("📚 KONULARA GÖRE DAĞILIM (GENEL)")
    text.append("-" * 50)
    konu_header = f"{'Konu':<35}" + "".join(f" {subject:<12}" for subject in all_subjects) + f" {'Toplam':<8}"
    text.append(konu_header)
    text.append("-" * 50)
    
    konu_totals = {}
    for konu in konu_data:
        konu_totals[konu] = sum(konu_data[konu].get(subject, 0) for subject in all_subjects)
    
    sorted_konular = sorted(konu_totals.items(), key=lambda x: x[1], reverse=True)
    
    for konu, total_konu in sorted_konular:
        row = f"{konu:<35}" + "".join(
            f" {konu_data[konu].get(subject, 0):<12}" for subject in all_subjects
        ) + f" {total_konu:<8}"
        text.append(row)
    
    text.append("-" * 50)
    text.append("")
    
    # Bilinmeyen konu soruları
    unknown_questions = [
        (q['yil'], q['ders'], q['soru_no'])
        for q in questions
        if q.get("topic_missing") or q.get('konu') in ['BİLİNMEYEN KONU', '', None] or not q.get('konu')
    ]
    if unknown_questions:
        text.append("⚠️ BİLİNMEYEN KONU SORULARI")
        text.append("-" * 50)
        text.append("Bu soruların KONU etiketi bulunamadı:")
        for yil, ders, no in unknown_questions:
            text.append(f"  • {yil} {ders} - Soru {no}")
        text.append("-" * 50)
        text.append("")

    append_topic_quality_report(text, quality_report)
    
    text.append("📋 YIL × DERS × KONU DAĞILIMI")
    text.append("-" * 70)
    
    yil_ders_konu = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for q in questions:
        if q.get('konu') and q.get('konu') not in ['BİLİNMEYEN KONU', '']:
            yil_ders_konu[q['yil']][q['ders']][q['konu']] += 1
    
    sorted_yil_ders_konu_years = sorted(yil_ders_konu.keys(), reverse=True)
    all_ders = sorted(set(d for y in sorted_yil_ders_konu_years for d in yil_ders_konu[y].keys()))
    all_konular = sorted(set(k for y in sorted_yil_ders_konu_years for d in all_ders for k in yil_ders_konu[y][d].keys()))
    
    for year in sorted_yil_ders_konu_years:
        text.append(f"\n{year}:")
        for ders in all_ders:
            konular_str = ", ".join([f"{k}: {yil_ders_konu[year][ders].get(k, 0)}" for k in all_konular])
            text.append(f"  {ders}: {konular_str}")
    
    text.append("")
    text.append("=" * 70)
    text.append("")
    
    for subject in all_subjects:
        text.append(f"📋 YIL × KONU MATRİSİ ({subject})")
        text.append("-" * 70)

        subject_years = sorted(
            set(y for y in years_data.keys() if years_data[y].get(subject, 0) > 0),
            reverse=True,
        )
        if subject_years:
            header = f"{'Konu':<30}"
            for year in subject_years:
                header += f" {year:<8}"
            text.append(header)
            text.append("-" * 70)

            subject_topics = [
                konu_name
                for konu_name, _ in sorted_konular
                if konu_data[konu_name].get(subject, 0) > 0
            ]

            for konu_name in subject_topics:
                row = f"{konu_name[:28]:<30}"
                for year in subject_years:
                    count = 0
                    for q in questions:
                        if q['yil'] == year and q['konu'] == konu_name and q['ders'] == subject:
                            count += 1
                    row += f" {count:<8}"
                text.append(row)
        else:
            text.append(f"{subject} verisi bulunamadı.")

        text.append("-" * 70)
        text.append("")
    
    exam_family_topic_data = defaultdict(lambda: defaultdict(int))
    exam_family_subtopic_data = defaultdict(lambda: defaultdict(int))

    for q in questions:
        exam_family = q.get("sinav_aile") or get_exam_family(q.get("ders", ""))
        topic_name = q.get("konu") or "Diger"
        exam_family_topic_data[exam_family][topic_name] += 1
        for subtopic in q.get("alt_basliklar", []):
            exam_family_subtopic_data[exam_family][f"{topic_name} > {subtopic}"] += 1

    text.append("SINAV BAZLI ONCELIK VE ALT BASLIK RAPORU")
    text.append("-" * 70)

    for exam_family in sorted(exam_family_topic_data.keys()):
        text.append(f"\n{exam_family}:")

        sorted_main_topics = sort_topics_for_priority(exam_family, exam_family_topic_data[exam_family])
        if sorted_main_topics:
            text.append("  En yogun ana basliklar:")
            for topic_name, count in sorted_main_topics[:8]:
                text.append(f"    - {topic_name}: {count}")

        sorted_subtopics = sorted(
            exam_family_subtopic_data[exam_family].items(),
            key=lambda item: (-item[1], item[0])
        )
        if sorted_subtopics:
            text.append("  En sik donen alt basliklar:")
            for subtopic_name, count in sorted_subtopics[:10]:
                text.append(f"    - {subtopic_name}: {count}")

        priority_topics = [topic_name for topic_name, _ in sorted_main_topics[:6]]
        if priority_topics:
            text.append("  Onerilen calisma sirasi:")
            text.append(f"    {' -> '.join(priority_topics)}")

    text.append("-" * 70)
    text.append("")

    text.append("=" * 70)
    text.append("Analiz tamamlandi.")
    text.append("=" * 70)

    return "\n".join(text), new_files

def save_analysis():
    """Analiz sonucunu dosyaya kaydeder"""
    text, new_files = generate_analysis_text()
    
    with open(ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        f.write(text)
    
    data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "new_files": new_files,
        "total_questions": len([q for q in analyze_all_exams()[0]])
    }
    with open(ANALYSIS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return text, new_files

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("DKAB Analiz araci calisiyor...\n")
    result, new_files = save_analysis()
    print(result)
    
    if new_files:
        print("\n[YENI DOSYALAR TESPIT EDILDI]")
        for f in new_files:
            print(f"   - {f}")
