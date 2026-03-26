#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

try:
    from analiz_araci import analyze_all_exams
    from project_paths import TEMIZ_METIN_DIR, ensure_directory
    from topic_catalog import normalize_topic_name, sanitize_topic_for_filename
except ImportError:
    from Python_Verisi.analiz_araci import analyze_all_exams
    from Python_Verisi.project_paths import TEMIZ_METIN_DIR, ensure_directory
    from Python_Verisi.topic_catalog import normalize_topic_name, sanitize_topic_for_filename


def filter_export_questions(
    questions: List[Dict],
    *,
    year: str | None = None,
    subject: str | None = None,
    topic: str | None = None,
) -> List[Dict]:
    normalized_topic = normalize_topic_name(topic or "")
    filtered = []
    for question in questions:
        if year and str(question.get("yil")) != str(year):
            continue
        if subject and question.get("ders") != subject:
            continue
        if normalized_topic and normalize_topic_name(question.get("konu", "")) != normalized_topic:
            continue
        filtered.append(question)
    return filtered


def write_grouped_exports(questions: List[Dict], output_dir: Path) -> List[Path]:
    grouped: Dict[tuple, List[Dict]] = {}
    for question in sorted(
        questions,
        key=lambda item: (str(item.get("ders", "")), int(item.get("yil", 0)), str(item.get("konu", "")), int(item.get("soru_no", 0))),
    ):
        normalized_topic = normalize_topic_name(question.get("konu", "")) or "Diğer"
        key = (question.get("ders", "Bilinmeyen"), question.get("yil", "Bilinmeyen"), normalized_topic)
        grouped.setdefault(key, []).append(question)

    written_paths: List[Path] = []
    for (subject, year, topic), items in grouped.items():
        target_dir = ensure_directory(output_dir / str(subject) / str(year))
        target_path = target_dir / f"{sanitize_topic_for_filename(topic)}.txt"
        lines = [
            f"Ders: {subject}",
            f"Yıl: {year}",
            f"Konu: {topic}",
            f"Toplam Soru: {len(items)}",
            "",
        ]
        for item in items:
            lines.append(f"Soru {item['soru_no']}:")
            lines.append((item.get("soru_metni") or "").strip())
            lines.append("")
        target_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        written_paths.append(target_path)
    return written_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Soruları yıl ve konuya göre temiz metin dosyaları olarak dışa aktarır.")
    parser.add_argument("--year", help="Yıl filtresi. Örnek: 2024")
    parser.add_argument("--subject", help="Ders filtresi. Örnek: DKAB")
    parser.add_argument("--topic", help="Konu filtresi. Örnek: Fıkıh")
    parser.add_argument("--output-dir", help="Varsayılan çıktı klasörünü değiştirir.")
    args = parser.parse_args()

    questions, _, _ = analyze_all_exams()
    filtered = filter_export_questions(
        questions,
        year=args.year,
        subject=args.subject,
        topic=args.topic,
    )
    output_dir = Path(args.output_dir) if args.output_dir else TEMIZ_METIN_DIR
    ensure_directory(output_dir)
    written_paths = write_grouped_exports(filtered, output_dir)

    print("Temiz metin dışa aktarma tamamlandı.")
    print(f"Filtrelenen soru sayısı: {len(filtered)}")
    print(f"Oluşturulan dosya sayısı: {len(written_paths)}")
    print(f"Çıktı klasörü: {output_dir}")


if __name__ == "__main__":
    main()
