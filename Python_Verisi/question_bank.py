#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

try:
    from project_paths import WORDE_DIR
    from topic_catalog import is_known_topic, normalize_topic_name
except ImportError:
    from Python_Verisi.project_paths import WORDE_DIR
    from Python_Verisi.topic_catalog import is_known_topic, normalize_topic_name


QUESTION_SEPARATOR = "---SONRAKI SORU---"
QUESTION_SEPARATOR_VARIANTS = (
    "---SONRAKİ SORU---",
    "---SONRAKÃ„Â° SORU---",
    "---SONRAKÃƒâ€Ã‚Â° SORU---",
    "---SONRAK? SORU---",
    "---SONRAK?? SORU---",
)
ANSWER_PREFIXES = (
    "Doğru Cevap:",
    "Dogru Cevap:",
    "DoÄŸru Cevap:",
    "DoÃ„Å¸ru Cevap:",
    "Do?ru Cevap:",
    "Do??ru Cevap:",
)
EXPLANATION_PREFIXES = (
    "Açıklama:",
    "Aciklama:",
    "AÃ§Ä±klama:",
    "AÃƒÂ§Ã„Â±klama:",
    "A??klama:",
    "A????klama:",
)
VISUAL_PREFIXES = (
    "Görsel",
    "Gorsel",
    "GÃ¶rsel",
    "GÃƒÂ¶rsel",
    "G?rsel",
    "G??rsel",
    "Dosya:",
    "Konum:",
)
SKIPPED_LINE_PREFIXES = (
    "DERS:",
    "YIL:",
    "[RESIM:",
) + ANSWER_PREFIXES + EXPLANATION_PREFIXES + VISUAL_PREFIXES


def format_subject_label(subject: str) -> str:
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


def normalize_question_content(content: str) -> str:
    normalized = str(content or "")
    for variant in QUESTION_SEPARATOR_VARIANTS:
        normalized = normalized.replace(variant, QUESTION_SEPARATOR)
    return normalized


def iter_exam_files(base_dir: Path = WORDE_DIR) -> Iterable[Tuple[Path, int, str]]:
    if not base_dir.exists():
        return
    for file_path in sorted(base_dir.glob("*_Sorulari.txt")):
        match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", file_path.name)
        if not match:
            continue
        year = int(match.group(1))
        subject = format_subject_label(match.group(2))
        yield file_path, year, subject


def has_dhbt_common_file(year: int, base_dir: Path = WORDE_DIR) -> bool:
    return (base_dir / f"{year}_DHBT_Ortak_Sorulari.txt").exists()


def should_skip_dhbt_common_question(
    year: int,
    subject: str,
    soru_no: int,
    base_dir: Path = WORDE_DIR,
) -> bool:
    if soru_no > 20:
        return False
    if subject not in {"DHBT Lisans", "DHBT Önlisans", "DHBT Ortaöğretim"}:
        return False
    return has_dhbt_common_file(year, base_dir=base_dir)


def _resolve_default_topic(default_topic: object, subject: str) -> str:
    if callable(default_topic):
        return str(default_topic(subject) or "")
    if default_topic is None:
        return subject
    return str(default_topic or "")


def _resolve_visual_path(
    raw_value: str,
    year: int,
    visual_resolver: Optional[Callable[[str, int], str]] = None,
) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return value
    if visual_resolver is not None:
        return str(visual_resolver(value, year))
    return value


def _extract_visual_file_name(line: str) -> str:
    prefixes = (
        "Görsel dosyası:",
        "Gorsel dosyasi:",
        "GÃ¶rsel dosyasÄ±:",
        "GÃƒÂ¶rsel dosyasÃ„Â±:",
        "G?rsel dosyas?:",
        "G??rsel dosyas??:",
        "Görsel dosya adı:",
        "Gorsel dosya adi:",
        "GÃ¶rsel dosya adÄ±:",
        "Dosya:",
    )
    for prefix in prefixes:
        if prefix in line:
            return line.split(prefix, 1)[1].strip()
    return ""


def parse_single_question_block(
    text: str,
    year: int,
    subject: str = "DKAB",
    *,
    base_dir: Path = WORDE_DIR,
    default_topic: object = "",
    visual_resolver: Optional[Callable[[str, int], str]] = None,
) -> Optional[Dict]:
    try:
        lines = text.strip().splitlines()
        soru_no = None
        soru_metni: List[str] = []
        options: Dict[str, str] = {}
        dogru_cevap = None
        aciklama = ""
        gorsel_var = False
        gorsel_dosyalari: List[str] = []
        raw_topic_values: List[str] = []
        topic_candidates: List[str] = []
        alias_corrections: List[Tuple[str, str]] = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("Soru ") and ":" in line:
                match = re.search(r"Soru\s+(\d+)", line)
                if match:
                    try:
                        soru_no = int(match.group(1))
                    except ValueError:
                        soru_no = None
                continue

            if line.startswith("[RESIM:"):
                gorsel_var = True
                gorsel_dosyalari.append(_resolve_visual_path(line, year, visual_resolver))
                continue

            if line.startswith("KONU:"):
                raw_topic = line.split(":", 1)[1].strip()
                raw_topic_values.append(raw_topic)
                normalized_topic = normalize_topic_name(raw_topic)
                if raw_topic and normalized_topic and raw_topic != normalized_topic:
                    alias_corrections.append((raw_topic, normalized_topic))
                if normalized_topic:
                    topic_candidates.append(normalized_topic)
                continue

            if re.match(r"^[ABCDE]\)", line):
                options[line[0]] = line[2:].strip()
                continue

            if line.startswith(ANSWER_PREFIXES):
                dogru_cevap = line.split(":", 1)[1].strip()
                continue

            if line.startswith(EXPLANATION_PREFIXES):
                aciklama = line.split(":", 1)[1].strip()
                continue

            if (
                "Görsel Notu:" in line
                or "Gorsel Notu:" in line
                or "GÃ¶rsel Notu:" in line
                or "GÃƒÂ¶rsel Notu:" in line
                or "G?rsel Notu:" in line
                or "G??rsel Notu:" in line
                or "Görsel dosyası:" in line
                or "Gorsel dosyasi:" in line
                or "GÃ¶rsel dosyasÄ±:" in line
                or "GÃƒÂ¶rsel dosyasÃ„Â±:" in line
                or "G?rsel dosyas?:" in line
                or "G??rsel dosyas??:" in line
                or "Dosya:" in line
            ):
                gorsel_var = True
                dosya_adi = _extract_visual_file_name(line)
                if dosya_adi:
                    gorsel_dosyalari.append(_resolve_visual_path(dosya_adi, year, visual_resolver))
                continue

            if soru_no and not line.startswith(SKIPPED_LINE_PREFIXES):
                soru_metni.append(line)

        konu = ""
        for candidate in topic_candidates:
            if is_known_topic(candidate):
                konu = candidate
                break
        if not konu and topic_candidates:
            konu = topic_candidates[-1]

        if not konu:
            konu = _resolve_default_topic(default_topic, subject)

        if (
            soru_no
            and len(options) >= 2
            and dogru_cevap
            and not should_skip_dhbt_common_question(year, subject, soru_no, base_dir=base_dir)
        ):
            return {
                "yil": year,
                "ders": subject,
                "konu": konu,
                "soru_no": soru_no,
                "soru_metni": "\n".join(soru_metni).strip(),
                "siklar": options,
                "dogru_cevap": dogru_cevap,
                "aciklama": aciklama,
                "gorsel_var": gorsel_var,
                "gorsel_dosyalari": gorsel_dosyalari,
                "tablo_var": False,
                "tablo_dosyalari": [],
                "topic_missing": not any(item.strip() for item in raw_topic_values),
                "topic_known": is_known_topic(konu),
                "raw_topic_values": raw_topic_values,
                "topic_alias_corrections": alias_corrections,
            }
    except Exception:
        return None

    return None


def parse_questions_from_file(
    file_path: Path,
    year: int,
    subject: str = "DKAB",
    *,
    base_dir: Path = WORDE_DIR,
    default_topic: object = "",
    visual_resolver: Optional[Callable[[str, int], str]] = None,
) -> List[Dict]:
    questions: List[Dict] = []

    with open(file_path, "r", encoding="utf-8") as file:
        content = normalize_question_content(file.read())

    for block in content.split(QUESTION_SEPARATOR):
        if "Soru " not in block:
            continue
        if not any(marker in block for marker in ANSWER_PREFIXES):
            continue
        question = parse_single_question_block(
            block,
            year,
            subject,
            base_dir=base_dir,
            default_topic=default_topic,
            visual_resolver=visual_resolver,
        )
        if question:
            questions.append(question)
    return questions


def load_question_bank(
    *,
    base_dir: Path = WORDE_DIR,
    default_topic: object = "",
    visual_resolver: Optional[Callable[[str, int], str]] = None,
) -> Tuple[List[Dict], List[str], List[str]]:
    questions: List[Dict] = []
    years = set()
    subjects = set()

    for file_path, year, subject in iter_exam_files(base_dir):
        year_questions = parse_questions_from_file(
            file_path,
            year,
            subject,
            base_dir=base_dir,
            default_topic=default_topic,
            visual_resolver=visual_resolver,
        )
        questions.extend(year_questions)
        years.add(str(year))
        subjects.add(subject)

    return questions, sorted(years, reverse=True), sorted(subjects)
