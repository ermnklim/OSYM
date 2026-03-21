#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
from typing import Dict, List

from Python_Verisi.similarity_analyzer import build_similarity_report, filter_questions


BASE_PATH = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir"


def format_subject_label(subject: str) -> str:
    subject = str(subject or "").replace("_", " ").strip()
    replacements = {
        "Onlisans": "Önlisans",
        "Ortaogretim": "Ortaöğretim",
        "ogretim": "öğretim",
    }
    for source, target in replacements.items():
        subject = subject.replace(source, target)
    return subject


def parse_questions() -> List[Dict]:
    questions: List[Dict] = []

    for filename in sorted(os.listdir(BASE_PATH)):
        match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
        if not match:
            continue

        year = int(match.group(1))
        subject = format_subject_label(match.group(2))
        file_path = os.path.join(BASE_PATH, filename)

        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()

        content = content.replace("---SONRAKİ SORU---", "---SONRAKI SORU---")
        content = content.replace("---SONRAKÄ° SORU---", "---SONRAKI SORU---")
        content = content.replace("---SONRAKÃ„Â° SORU---", "---SONRAKI SORU---")

        for block in content.split("---SONRAKI SORU---"):
            if "Soru " not in block:
                continue

            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue

            soru_no = "?"
            topic = ""
            question_lines = []
            options = {}

            for line in lines:
                if line.startswith("Soru ") and ":" in line:
                    match_no = re.search(r"Soru\s+(\d+)", line)
                    if match_no:
                        soru_no = int(match_no.group(1))
                elif line.startswith("KONU:"):
                    topic = line.split(":", 1)[1].strip()
                elif re.match(r"^[ABCDE]\)", line):
                    options[line[0]] = line[2:].strip()
                elif line.startswith(("DERS:", "YIL:", "Dogru Cevap:", "Doğru Cevap:", "Aciklama:", "Açıklama:", "Gorsel", "Görsel", "Dosya:", "Konum:", "[RESIM:")):
                    continue
                else:
                    question_lines.append(line)

            if question_lines and soru_no != "?" and len(options) >= 2:
                questions.append(
                    {
                        "yil": year,
                        "ders": subject,
                        "konu": topic,
                        "soru_no": soru_no,
                        "soru_metni": " ".join(question_lines),
                        "siklar": options,
                    }
                )

    return questions


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def main() -> None:
    parser = argparse.ArgumentParser(description="Benzer soru ve konu egilimi analizi")
    parser.add_argument("--yil", help="Belirli bir yil filtrele")
    parser.add_argument("--ders", help="Belirli bir ders filtrele. Ornek: DKAB, IHL, DHBT Lisans")
    parser.add_argument("--konu", help="Belirli bir konu filtrele")
    args = parser.parse_args()

    all_questions = parse_questions()
    scope_questions = filter_questions(
        all_questions,
        year=args.yil,
        subject=args.ders,
        topic=args.konu,
    )
    history_questions = filter_questions(
        all_questions,
        year=None,
        subject=args.ders,
        topic=args.konu,
    )
    report = build_similarity_report(scope_questions, history_questions=history_questions)

    print("Benzer Soru ve Cikis Egilimi Analizi")
    print("====================================")
    print(f"Filtrelenen soru: {report['scope_total']}")
    print(f"Tahmin havuzu: {report['history_total']}")
    print(f"Yil filtresi: {args.yil or 'Tum yillar'}")
    print(f"Ders filtresi: {args.ders or 'Tum dersler'}")
    print(f"Konu filtresi: {args.konu or 'Tum konular'}")

    if not scope_questions:
        print("\nBu filtrede soru bulunamadi.")
        return

    print_section("One Cikan Soru Tipleri")
    for row in report["question_types"][:8]:
        print(f"- {row['question_type']}: {row['count']}")

    print_section("Kapsamdaki Konular")
    for row in report["topic_counts"][:8]:
        print(f"- {row['topic']}: {row['count']}")

    print_section("Konu ve Alt Konu Ipuclari")
    for item in report["subtopics_by_topic"][:8]:
        phrases = ", ".join(item["phrases"]) if item["phrases"] else "Belirgin alt konu bulunamadi"
        print(f"- {item['topic']}: {phrases}")

    print_section("Tekrarlayan OSYM Kaliplari")
    if not report["clusters"]:
        print("- Belirgin tekrar eden kalip bulunamadi.")
    else:
        for cluster in report["clusters"][:8]:
            years_text = ", ".join(str(year) for year in cluster["years"]) if cluster["years"] else "?"
            phrase_text = ", ".join(cluster["phrases"]) if cluster["phrases"] else "Alt konu ipucu yok"
            print(
                f"- {cluster['topic'] or 'Konu yok'} | {cluster['question_type']} | "
                f"{cluster['size']} soru | yillar: {years_text} | alt konu: {phrase_text}"
            )

    print_section("Cikmasi Muhtemel Konular")
    if not args.konu:
        for row in report["likely_topics"][:8]:
            years_text = ", ".join(str(year) for year in row["years"][-5:]) if row["years"] else "?"
            print(
                f"- {row['topic']} | skor {row['score']:.1f} | tekrar {row['count']} | "
                f"son yillar {row['recent_count']} | yillar: {years_text}"
            )

    print_section("Cikmasi Muhtemel Alt Konular")
    if not report["likely_subtopics"]:
        print("- Belirgin alt konu sinyali bulunamadi.")
    else:
        for row in report["likely_subtopics"][:8]:
            years_text = ", ".join(str(year) for year in row["years"][-4:]) if row["years"] else "?"
            print(
                f"- {row['subtopic']} | skor {row['score']:.1f} | tekrar {row['count']} | yillar: {years_text}"
            )

    print_section("Guclu Benzer Soru Eslesmeleri")
    if not report["similar_pairs"]:
        print("- Guclu eslesme bulunamadi.")
    else:
        for pair in report["similar_pairs"][:12]:
            q1 = pair["q1"]
            q2 = pair["q2"]
            overlap = ", ".join(pair["overlap_terms"]) if pair["overlap_terms"] else "Belirgin ortak iz yok"
            print(
                f"- %{int(pair['score'] * 100)} | "
                f"{q1['yil']} {q1['ders']} Soru {q1['soru_no']} ({q1['konu']}) <-> "
                f"{q2['yil']} {q2['ders']} Soru {q2['soru_no']} ({q2['konu']})"
            )
            print(f"  Tipler: {q1['question_type']} / {q2['question_type']}")
            print(f"  Ortak izler: {overlap}")
            print(f"  A: {(q1['soru_metni'] or '')[:110]}...")
            print(f"  B: {(q2['soru_metni'] or '')[:110]}...")


if __name__ == "__main__":
    main()
