#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

try:
    from topic_catalog import map_summary_heading_to_topics, match_summary_main_section
except ImportError:
    from Python_Verisi.topic_catalog import map_summary_heading_to_topics, match_summary_main_section


ARABIC_LETTER_NAMES = {
    "ا": "elif",
    "أ": "hemze",
    "إ": "hemze",
    "آ": "elif",
    "ٱ": "elif",
    "ب": "be",
    "ت": "te",
    "ث": "se",
    "ج": "cim",
    "ح": "ha",
    "خ": "hı",
    "د": "dal",
    "ذ": "zel",
    "ر": "ra",
    "ز": "ze",
    "س": "sin",
    "ش": "şın",
    "ص": "sad",
    "ض": "dad",
    "ط": "tı",
    "ظ": "zı",
    "ع": "ayn",
    "غ": "gayn",
    "ف": "fe",
    "ق": "kaf",
    "ك": "kef",
    "ل": "lam",
    "م": "mim",
    "ن": "nun",
    "ه": "he",
    "ة": "te merbuta",
    "و": "vav",
    "ؤ": "hemzeli vav",
    "ي": "ye",
    "ى": "ye",
    "ئ": "hemzeli ye",
    "ء": "hemze",
}

ARABIC_MARK_NAMES = {
    "ً": "tenvin üstün",
    "ٍ": "tenvin esre",
    "ٌ": "tenvin ötre",
    "َ": "üstün",
    "ِ": "esre",
    "ُ": "ötre",
    "ْ": "cezim",
    "ّ": "şedde",
}

TECVID_TERM_REPLACEMENTS = {
    "MEDD-İ": "meddi",
    "MEDD-I": "meddi",
    "VAKF-I LAZIM": "vakfı lazım",
    "VAKF-İ LAZIM": "vakfı lazım",
    "VAKF-I MUTLAK": "vakfı mutlak",
    "VAKF-İ MUTLAK": "vakfı mutlak",
    "VAKF-I": "vakfı",
    "VAKF-İ": "vakfı",
    "İDĞAM-I": "idğamı",
    "IDĞAM-I": "idğamı",
    "İDĞAM-İ": "idğamı",
    "BİLA GUNNE": "bila gunne",
    "MEAL GUNNE": "meal gunne",
    "SAKİN": "sakin",
    "TENVİN": "tenvin",
    "İHFA": "ihfa",
    "İZHAR": "izhar",
    "İKLAB": "iklab",
    "LİN": "lin",
}


def _roman_to_int(value: str) -> int | None:
    roman_values = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
    }
    text = str(value or "").upper().strip()
    if not text or any(char not in roman_values for char in text):
        return None

    total = 0
    previous_value = 0
    repeat_count = 0
    previous_char = ""
    for char in reversed(text):
        current_value = roman_values[char]
        if char == previous_char:
            repeat_count += 1
            if char in {"V", "L", "D"} or repeat_count >= 3:
                return None
        else:
            repeat_count = 0
        if current_value < previous_value:
            if char not in {"I", "X", "C"}:
                return None
            total -= current_value
        else:
            total += current_value
            previous_value = current_value
        previous_char = char
    return total if total > 0 else None


def _replace_roman_numerals_for_tts(text: str) -> str:
    pattern = re.compile(
        r"(?<![A-Za-zÇĞİÖŞÜçğıöşü])"
        r"(M{0,3}(?:CM|CD|D?C{0,3})"
        r"(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{1,3}|I))"
        r"(\.?)"
        r"(?![A-Za-zÇĞİÖŞÜçğıöşü])"
    )

    def replace(match: re.Match[str]) -> str:
        roman = match.group(1)
        suffix = match.group(2) or ""
        numeric_value = _roman_to_int(roman)
        if numeric_value is None:
            return match.group(0)
        return f"{numeric_value}{suffix}"

    return pattern.sub(replace, str(text or ""))


def _count_question_references(text: str) -> int:
    match = re.search(r"\(çıkmış sorular\s*:\s*(.*?)\)", text, flags=re.IGNORECASE)
    if not match:
        return 0
    return len([item for item in match.group(1).split(",") if item.strip()])


def _turkish_upper(text: str) -> str:
    return text.replace("i", "İ").replace("ı", "I").upper()


def _spoken_join_i_suffix(match: re.Match[str]) -> str:
    stem = match.group(1).strip().lower()
    last_vowel = ""
    for char in reversed(stem):
        if char in "aeıioöuü":
            last_vowel = char
            break
    suffix = "i" if last_vowel in {"e", "i", "ö", "ü"} else "ı"
    return stem + suffix


def _replace_tecvid_terms(text: str) -> str:
    value = str(text or "")
    value = value.replace("\uf077", " ")
    value = value.replace("“", " ")
    value = value.replace("”", " ")
    for source, target in TECVID_TERM_REPLACEMENTS.items():
        value = re.sub(rf"\b{re.escape(source)}\b", target, value, flags=re.IGNORECASE)
    value = re.sub(r"\b([A-Za-zÇĞİÖŞÜçğıöşü]+)-[Iİıi]\b", _spoken_join_i_suffix, value)
    return value


def _replace_arabic_symbols_for_tts(text: str) -> str:
    value = str(text or "")
    value = value.replace("", " ")
    value = value.replace("◌ً", " tenvin üstün ")
    value = value.replace("◌ٍ", " tenvin esre ")
    value = value.replace("◌ٌ", " tenvin ötre ")

    value = re.sub(r"[“”\"'`]\s*([ءاأإآٱبتثجحخدذرزسشصضطظعغفقكلمنهوىيؤئةئ])\s*[“”\"'`]", r" , \1 , ", value)

    def replace_sukun_pair(match: re.Match[str]) -> str:
        letter = match.group(1)
        return f" cezimli {ARABIC_LETTER_NAMES.get(letter, letter)} "

    value = re.sub(r"([ءاأإآٱبتثجحخدذرزسشصضطظعغفقكلمنهوىيؤئةئ])\s*ْ", replace_sukun_pair, value)

    def replace_letter(match: re.Match[str]) -> str:
        char = match.group(0)
        if char in ARABIC_MARK_NAMES:
            return f" {ARABIC_MARK_NAMES[char]} "
        return f" {ARABIC_LETTER_NAMES.get(char, char)} "

    value = re.sub(r"[ءاأإآٱبتثجحخدذرزسشصضطظعغفقكلمنهوىيؤئةئًٌٍَُِّْ]", replace_letter, value)
    value = value.replace("|", ", ")
    value = value.replace("/", ", ")
    value = value.replace("–", ", ")
    value = value.replace("—", ", ")
    value = value.replace("(", " ")
    value = value.replace(")", " ")
    value = value.replace("“", " ")
    value = value.replace("”", " ")
    value = value.replace('"', " ")
    return re.sub(r"\s+", " ", value).strip()


def normalize_sentence_for_tts(text: str) -> str:
    value = _replace_roman_numerals_for_tts(text)
    value = _replace_tecvid_terms(_replace_arabic_symbols_for_tts(value))
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

    def number_to_turkish(match: re.Match[str]) -> str:
        number_text = match.group(1)
        is_ordinal = match.group(2) == "."
        try:
            number = int(number_text)
        except Exception:
            return number_text

        units = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
        tens = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]

        if number == 0:
            result = "sıfır"
        else:
            pieces = []
            if number >= 1000:
                thousands = number // 1000
                if thousands > 1:
                    pieces.append(f"{units[thousands]} bin")
                else:
                    pieces.append("bin")
                number %= 1000
            if number >= 100:
                hundreds = number // 100
                if hundreds > 1:
                    pieces.append(f"{units[hundreds]} yüz")
                else:
                    pieces.append("yüz")
                number %= 100
            if number >= 10:
                pieces.append(tens[number // 10])
                number %= 10
            if number:
                pieces.append(units[number])
            result = " ".join(piece for piece in pieces if piece)

        if not is_ordinal:
            return result
        parts = [piece for piece in result.split() if piece]
        if not parts:
            return result
        parts[-1] = ordinal_map.get(parts[-1], parts[-1])
        return " ".join(parts)

    value = re.sub(r"(\d+)(\.)?", number_to_turkish, value)
    replacements = {
        r"\bVIII\.": "Sekizinci ",
        r"\bVII\.": "Yedinci ",
        r"\bVI\.": "Altıncı ",
        r"\bIV\.": "Dördüncü ",
        r"\bV\.": "Beşinci ",
        r"\bIII\.": "Üçüncü ",
        r"\bII\.": "İkinci ",
        r"\bI\.": "Birinci ",
        r"(?i)\bhz\.\s*": "Hazreti ",
        r"(?i)\bibn\b": "İbni",
        r"(?i)\bb\.\s*": "bin ",
    }
    replacements.update(
        {
            r"(?i)\bm\.\s*ö\.\s*": "milattan önce ",
            r"(?i)\bm\.\s*s\.\s*": "milattan sonra ",
            r"(?i)\bs\.a\.v\.\s*": "sallallahu aleyhi ve sellem ",
            r"(?i)\ba\.s\.\s*": "aleyhisselam ",
            r"(?i)\br\.a\.\s*": "radıyallahu anh ",
        }
    )
    for pattern, repl in replacements.items():
        value = re.sub(pattern, repl, value)
    value = re.sub(r"\b(vakf[ıi]\s+\w+)\s+([a-zçğıöşü]+)\b", r"\1, \2,", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(vakfı\s+lazım)\s+(mim)\b", r"\1, \2,", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(vakfı\s+mutlak)\s+(tı)\b", r"\1, \2,", value, flags=re.IGNORECASE)
    value = re.sub(r"vakfı\s+lazım\W+mim,", "vakfı lazım, mim,", value, flags=re.IGNORECASE)
    value = re.sub(r"vakfı\s+mutlak\W+tı,", "vakfı mutlak, tı,", value, flags=re.IGNORECASE)
    value = re.sub(r",\s*,+", ", ", value)
    value = re.sub(r"\s+\?\s+", " ", value)
    value = re.sub(r"\s+,", ",", value)
    value = value.replace(" - ", ", ")
    return re.sub(r"\s+", " ", value).strip()


def _is_probable_subtopic_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("•", "-", "*")):
        return False
    if re.match(r"^\d+[.)]", stripped):
        return False

    no_parens = re.sub(r"\(.*?\)", "", stripped).strip()
    if not no_parens:
        return False
    if match_summary_main_section(no_parens):
        return False

    if ":" in no_parens and len(no_parens) <= 70 and not re.search(r"[.!?]", no_parens):
        return True

    alpha_chars = [char for char in no_parens if char.isalpha()]
    if alpha_chars and all(char.isupper() for char in alpha_chars):
        return len(no_parens) <= 90
    return False


def _split_sentences(line: str) -> List[str]:
    raw_temp = line
    for abbr in ["HZ", "Hz", "hz", "S.A.V", "A.S", "R.A", "vs", "vb", "b", "B"]:
        raw_temp = re.sub(fr"\b{abbr}\.", f"{abbr}_DOT_", raw_temp, flags=re.IGNORECASE)
    for roman in ["VIII", "VII", "VI", "IV", "V", "III", "II", "I"]:
        raw_temp = re.sub(fr"\b{roman}\.\s+", f"{roman}_DOT_ ", raw_temp)

    sentences = []
    for raw_split in re.split(r"(?<=[.!?])\s+", raw_temp):
        raw_sentence = raw_split.replace("_DOT_", ".").strip()
        if raw_sentence:
            sentences.append(raw_sentence)
    return sentences or ([line.strip()] if line.strip() else [])


def parse_topic_text(content: str) -> Dict[str, object]:
    topic_blocks: List[Dict[str, object]] = []
    main_sections: List[Dict[str, object]] = []
    warnings: List[str] = []
    main_section_to_topics: Dict[str, List[str]] = defaultdict(list)
    main_section_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()

    current_main = "Diğer"
    current_topic = "Giriş / Genel"
    current_sentences: List[Dict[str, str]] = []
    current_start_line = 1

    def register_main_section(name: str, line_number: int) -> None:
        if not any(item["name"] == name for item in main_sections):
            main_sections.append(
                {
                    "name": name,
                    "line_number": line_number,
                    "mapped_topics": list(map_summary_heading_to_topics(name)),
                }
            )

    def save_current_block() -> None:
        nonlocal current_sentences
        if not current_sentences:
            return
        mapped_topics = list(map_summary_heading_to_topics(current_topic))
        block = {
            "topic": current_topic,
            "main_cat": current_main,
            "main_section": current_main,
            "sentences": current_sentences,
            "mapped_topics": mapped_topics,
            "start_line": current_start_line,
        }
        topic_blocks.append(block)
        if current_topic not in main_section_to_topics[current_main]:
            main_section_to_topics[current_main].append(current_topic)
        if not mapped_topics and current_topic not in {"Giriş / Genel", "Diğer"}:
            warnings.append(f"Eşleşmeyen özet başlığı: {current_topic}")
        current_sentences = []

    lines = content.splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        question_count = _count_question_references(line)
        matched_main = match_summary_main_section(line)
        if matched_main:
            save_current_block()
            current_main = matched_main
            current_topic = "Giriş / Genel"
            current_start_line = line_number
            current_sentences = [{"raw": line, "norm": normalize_sentence_for_tts(line)}]
            register_main_section(matched_main, line_number)
            main_section_counts[current_main] += question_count
            topic_counts[current_topic] += question_count
            continue

        if _is_probable_subtopic_header(line):
            save_current_block()
            current_topic = line.rstrip()
            current_start_line = line_number
            current_sentences = [{"raw": line, "norm": normalize_sentence_for_tts(line)}]
            main_section_counts[current_main] += question_count
            topic_counts[current_topic] += question_count
            continue

        main_section_counts[current_main] += question_count
        topic_counts[current_topic] += question_count
        for sentence in _split_sentences(line):
            current_sentences.append({"raw": sentence, "norm": normalize_sentence_for_tts(sentence)})

    save_current_block()

    flattened_sentences = []
    mapped_topics = set()
    for main_section in main_sections:
        mapped_topics.update(main_section.get("mapped_topics", []))
    for block in topic_blocks:
        flattened_sentences.extend(block["sentences"])
        mapped_topics.update(block["mapped_topics"])

    return {
        "main_sections": main_sections,
        "topic_blocks": topic_blocks,
        "sentences": flattened_sentences,
        "warnings": warnings,
        "mapped_topics": sorted(mapped_topics),
        "main_section_to_topics": dict(main_section_to_topics),
        "main_section_counts": dict(main_section_counts),
        "topic_counts": dict(topic_counts),
    }


def parse_topic_text_file(path: Path) -> Dict[str, object]:
    content = path.read_text(encoding="utf-8")
    parsed = parse_topic_text(content)
    parsed["content"] = content
    parsed["path"] = str(path)
    return parsed
