#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


CANONICAL_TOPICS: List[str] = [
    "Kur'an-ı Kerim ve Tecvid",
    "Tefsir",
    "Hadis",
    "Fıkıh",
    "Fıkıh Usulü",
    "Kelam / Akaid",
    "İslam Mezhepleri ve Akımları",
    "İslam Tarihi",
    "Siyer",
    "İslam Kültür ve Medeniyeti",
    "İslam Felsefesi",
    "Din Felsefesi",
    "Din Sosyolojisi",
    "Din Psikolojisi",
    "Din Eğitimi",
    "Dinler Tarihi",
    "İslam Ahlakı ve Tasavvuf",
    "Mezhepler Tarihi",
    "Din Hizmetleri ve Hitabet",
]

TOPIC_ALIASES: Dict[str, str] = {
    "Akaid / Kelam": "Kelam / Akaid",
    "Kur’an-ı Kerim ve Tecvid": "Kur'an-ı Kerim ve Tecvid",
    "Kur'an-i Kerim ve Tecvid": "Kur'an-ı Kerim ve Tecvid",
    "Kurani Kerim ve Tecvid": "Kur'an-ı Kerim ve Tecvid",
    "İslam Tarihi / Siyer": "İslam Tarihi",
    "Islam Tarihi / Siyer": "İslam Tarihi",
    "Islam Tarihi": "İslam Tarihi",
    "İslam Ahlaki ve Tasavvuf": "İslam Ahlakı ve Tasavvuf",
    "Islam Ahlaki ve Tasavvuf": "İslam Ahlakı ve Tasavvuf",
    "?slam Ahlak? ve Tasavvuf": "İslam Ahlakı ve Tasavvuf",
    "Akaid Kelam": "Kelam / Akaid",
    "Mezhepler tarihi": "Mezhepler Tarihi",
    "İslam Mezhepleri Tarihi": "Mezhepler Tarihi",
    "Islam Mezhepleri Tarihi": "Mezhepler Tarihi",
}

SUMMARY_MAIN_SECTIONS: List[str] = [
    "Kur'an-ı Kerim ve Tecvid",
    "Tefsir",
    "Hadis",
    "İslam İbadet Esasları",
    "İslam Hukuku",
    "Fıkıh Usulü",
    "Kelam / Akaid",
    "İnanç Esasları",
    "İslam Mezhepler Tarihi",
    "İslam Kültür ve Medeniyeti",
    "İslam Mezhepleri ve Akımları",
    "İslam Tarihi",
    "Siyer",
    "İslam Felsefesi",
    "Din Felsefesi",
    "Din Sosyolojisi",
    "Din Psikolojisi",
    "Din Eğitimi",
    "Dinler Tarihi",
    "İslam Ahlakı ve Tasavvuf",
    "Mezhepler Tarihi",
    "Din Hizmetleri ve Hitabet",
]

SUMMARY_MAIN_SECTION_ALIASES: Dict[str, str] = {
    "İbadet": "İslam İbadet Esasları",
    "İslam İbadet Esasları": "İslam İbadet Esasları",
    "İslam Hukuku": "İslam Hukuku",
    "İnanç Esasları": "İnanç Esasları",
    "İslam Mezhepler Tarihi": "İslam Mezhepler Tarihi",
    "Kur'an-i Kerim ve Tecvid": "Kur'an-ı Kerim ve Tecvid",
}

SUMMARY_SECTION_TOPIC_MAP: Dict[str, Tuple[str, ...]] = {
    "Kur'an-ı Kerim ve Tecvid": ("Kur'an-ı Kerim ve Tecvid",),
    "Tefsir": ("Tefsir",),
    "Hadis": ("Hadis",),
    "İslam İbadet Esasları": ("Fıkıh",),
    "İslam Hukuku": ("Fıkıh",),
    "Fıkıh Usulü": ("Fıkıh Usulü",),
    "Kelam / Akaid": ("Kelam / Akaid",),
    "İnanç Esasları": ("Kelam / Akaid",),
    "İslam Mezhepler Tarihi": ("İslam Mezhepleri ve Akımları", "Mezhepler Tarihi"),
    "İslam Kültür ve Medeniyeti": ("İslam Kültür ve Medeniyeti",),
    "İslam Mezhepleri ve Akımları": ("İslam Mezhepleri ve Akımları",),
    "İslam Tarihi": ("İslam Tarihi",),
    "Siyer": ("Siyer",),
    "İslam Felsefesi": ("İslam Felsefesi",),
    "Din Felsefesi": ("Din Felsefesi",),
    "Din Sosyolojisi": ("Din Sosyolojisi",),
    "Din Psikolojisi": ("Din Psikolojisi",),
    "Din Eğitimi": ("Din Eğitimi",),
    "Dinler Tarihi": ("Dinler Tarihi",),
    "İslam Ahlakı ve Tasavvuf": ("İslam Ahlakı ve Tasavvuf",),
    "Mezhepler Tarihi": ("Mezhepler Tarihi",),
    "Din Hizmetleri ve Hitabet": ("Din Hizmetleri ve Hitabet",),
}

PRIORITY_HINTS: Dict[str, List[str]] = {
    "DHBT": [
        "Fıkıh",
        "Siyer",
        "Kelam / Akaid",
        "Kur'an-ı Kerim ve Tecvid",
        "İslam Ahlakı ve Tasavvuf",
        "Tefsir",
        "Hadis",
        "Dinler Tarihi",
        "Mezhepler Tarihi",
        "Din Hizmetleri ve Hitabet",
    ],
    "MBSTS": [
        "Fıkıh",
        "Kur'an-ı Kerim ve Tecvid",
        "Tefsir",
        "Hadis",
        "Kelam / Akaid",
        "Fıkıh Usulü",
        "Siyer",
        "İslam Tarihi",
        "Dinler Tarihi",
        "İslam Mezhepleri ve Akımları",
        "Din Hizmetleri ve Hitabet",
    ],
    "ÖABT DKAB": [
        "Fıkıh",
        "Tefsir",
        "Hadis",
        "Kelam / Akaid",
        "Din Eğitimi",
        "Siyer",
        "İslam Tarihi",
        "İslam Kültür ve Medeniyeti",
        "Dinler Tarihi",
        "Din Sosyolojisi",
        "Din Psikolojisi",
        "Din Felsefesi",
        "İslam Felsefesi",
    ],
    "ÖABT İHL": [
        "Kur'an-ı Kerim ve Tecvid",
        "Fıkıh",
        "Tefsir",
        "Hadis",
        "Kelam / Akaid",
        "Siyer",
        "İslam Tarihi",
        "İslam Ahlakı ve Tasavvuf",
        "İslam Mezhepleri ve Akımları",
        "Mezhepler Tarihi",
        "Dinler Tarihi",
        "Din Eğitimi",
    ],
}

_COMMON_MOJIBAKE_REPLACEMENTS = {
    "Ã–": "Ö",
    "Ã¶": "ö",
    "Ãœ": "Ü",
    "Ã¼": "ü",
    "Ä°": "İ",
    "Ä±": "ı",
    "Äž": "Ğ",
    "ÄŸ": "ğ",
    "Åž": "Ş",
    "ÅŸ": "ş",
    "Ã‡": "Ç",
    "Ã§": "ç",
    "â€™": "'",
    "â€œ": '"',
    "â€": '"',
}

_TURKISH_ASCII_MAP = str.maketrans(
    {
        "ı": "i",
        "İ": "I",
        "ş": "s",
        "Ş": "S",
        "ğ": "g",
        "Ğ": "G",
        "ü": "u",
        "Ü": "U",
        "ö": "o",
        "Ö": "O",
        "ç": "c",
        "Ç": "C",
    }
)


def _replace_common_mojibake(value: str) -> str:
    cleaned = str(value or "")
    for source, target in _COMMON_MOJIBAKE_REPLACEMENTS.items():
        cleaned = cleaned.replace(source, target)
    return cleaned.strip()


def fold_text(value: str) -> str:
    cleaned = _replace_common_mojibake(value)
    cleaned = cleaned.translate(_TURKISH_ASCII_MAP)
    cleaned = unicodedata.normalize("NFKD", cleaned)
    cleaned = cleaned.encode("ascii", "ignore").decode("ascii")
    cleaned = cleaned.lower().replace("_", " ")
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


_CANONICAL_BY_FOLD = {fold_text(topic): topic for topic in CANONICAL_TOPICS}
_ALIASES_BY_FOLD = {fold_text(alias): target for alias, target in TOPIC_ALIASES.items()}
_SUMMARY_MAIN_BY_FOLD = {
    fold_text(name): name
    for name in SUMMARY_MAIN_SECTIONS
}
_SUMMARY_MAIN_BY_FOLD.update(
    {fold_text(alias): target for alias, target in SUMMARY_MAIN_SECTION_ALIASES.items()}
)


def clean_topic_text(topic: str) -> str:
    return _replace_common_mojibake(topic).strip()


def normalize_topic_name(topic: str) -> str:
    cleaned = clean_topic_text(topic)
    if not cleaned:
        return ""

    folded = fold_text(cleaned)
    if folded in _CANONICAL_BY_FOLD:
        return _CANONICAL_BY_FOLD[folded]
    if folded in _ALIASES_BY_FOLD:
        return _ALIASES_BY_FOLD[folded]
    return cleaned


def is_known_topic(topic: str) -> bool:
    return normalize_topic_name(topic) in CANONICAL_TOPICS


def topic_sort_key(exam_family: str, topic: str) -> Tuple[int, str]:
    order = {name: index for index, name in enumerate(PRIORITY_HINTS.get(exam_family, []))}
    normalized = normalize_topic_name(topic)
    return (order.get(normalized, len(order) + 999), normalized)


def sort_topics_for_exam_family(exam_family: str, topic_counts: Dict[str, int]) -> List[Tuple[str, int]]:
    return sorted(
        topic_counts.items(),
        key=lambda item: (-item[1],) + topic_sort_key(exam_family, item[0]),
    )


def sanitize_topic_for_filename(topic: str) -> str:
    normalized = normalize_topic_name(topic)
    folded = fold_text(normalized)
    safe = re.sub(r"\s+", "_", folded).strip("_")
    return safe or "konu"


def match_summary_main_section(line: str) -> str:
    folded = fold_text(line)
    if folded in _SUMMARY_MAIN_BY_FOLD:
        return _SUMMARY_MAIN_BY_FOLD[folded]

    for folded_section, section_name in _SUMMARY_MAIN_BY_FOLD.items():
        if folded.startswith(folded_section + " "):
            return section_name
    return ""


def map_summary_heading_to_topics(heading: str) -> Tuple[str, ...]:
    matched_main = match_summary_main_section(heading)
    if matched_main:
        return SUMMARY_SECTION_TOPIC_MAP.get(matched_main, ())

    normalized_topic = normalize_topic_name(heading)
    if normalized_topic in CANONICAL_TOPICS:
        return (normalized_topic,)
    return ()


def summarize_topic_inventory(topics: Iterable[str]) -> Dict[str, int]:
    counter = Counter()
    for topic in topics:
        normalized = normalize_topic_name(topic)
        if normalized:
            counter[normalized] += 1
    return dict(counter)


def canonical_topics() -> Sequence[str]:
    return tuple(CANONICAL_TOPICS)


def summary_main_sections() -> Sequence[str]:
    return tuple(SUMMARY_MAIN_SECTIONS)
