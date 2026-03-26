#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from typing import Dict, List

from Python_Verisi.project_paths import WORDE_DIR
from Python_Verisi.question_bank import load_question_bank
from Python_Verisi.similarity_analyzer import build_similarity_report, filter_questions
from Python_Verisi.topic_catalog import normalize_topic_name

BASE_PATH = WORDE_DIR


def parse_questions() -> List[Dict]:
    questions, _, _ = load_question_bank(base_dir=BASE_PATH, default_topic="")
    for question in questions:
        question["konu"] = normalize_topic_name(question.get("konu", ""))
    return questions


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def main() -> None:
    parser = argparse.ArgumentParser(description="Benzer soru ve konu egilimi analizi")
    parser.add_argument("--yil", help="Belirli bir yil filtrele")
    parser.add_argument("--ders", help="Belirli bir ders filtrele. Ornek: DKAB, IHL, DHBT Lisans")
    parser.add_argument("--konu", help="Belirli bir konu filtrele")
    parser.add_argument("--semantic", action="store_true", help="Vektor tabanli semantik benzerlik guclendirmesini ac")
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
    report = build_similarity_report(
        scope_questions,
        history_questions=history_questions,
        use_semantic=args.semantic,
    )

    print("Benzer Soru ve Cikis Egilimi Analizi")
    print("====================================")
    print(f"Filtrelenen soru: {report['scope_total']}")
    print(f"Tahmin havuzu: {report['history_total']}")
    print(f"Yil filtresi: {args.yil or 'Tum yillar'}")
    print(f"Ders filtresi: {args.ders or 'Tum dersler'}")
    print(f"Konu filtresi: {args.konu or 'Tum konular'}")
    print(f"Aday tarama: {report.get('candidate_pair_count', 0)} cift")
    print(f"Semantik arka uc: {report.get('semantic_backend', 'kapali')}")

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
            semantic_note = ""
            if pair.get("semantic_score") is not None:
                semantic_note = f" | semantik %{int(pair['semantic_score'] * 100)}"
            print(
                f"- %{int(pair['score'] * 100)}{semantic_note} | "
                f"{q1['yil']} {q1['ders']} Soru {q1['soru_no']} ({q1['konu']}) <-> "
                f"{q2['yil']} {q2['ders']} Soru {q2['soru_no']} ({q2['konu']})"
            )
            print(f"  Tipler: {q1['question_type']} / {q2['question_type']}")
            print(f"  Ortak izler: {overlap}")
            print(f"  A: {(q1['soru_metni'] or '')[:110]}...")
            print(f"  B: {(q2['soru_metni'] or '')[:110]}...")


if __name__ == "__main__":
    main()
