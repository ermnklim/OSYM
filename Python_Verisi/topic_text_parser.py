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


def _count_question_references(text: str) -> int:
    match = re.search(r"\(çıkmış sorular\s*:\s*(.*?)\)", text, flags=re.IGNORECASE)
    if not match:
        return 0
    return len([item for item in match.group(1).split(",") if item.strip()])


def _turkish_upper(text: str) -> str:
    return text.replace("i", "İ").replace("ı", "I").upper()


def normalize_sentence_for_tts(text: str) -> str:
    value = str(text or "")

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
        if result and result[-1] in "aiıuü":
            return result + "ncı"
        return result + "inci"

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
    for pattern, repl in replacements.items():
        value = re.sub(pattern, repl, value)
    return value


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
