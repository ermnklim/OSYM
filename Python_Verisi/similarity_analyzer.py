#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional

try:
    import numpy as np
except ImportError:
    np = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    TfidfVectorizer = None


STOPWORDS = {
    "acaba",
    "ait",
    "ama",
    "ancak",
    "araciligiyla",
    "arasinda",
    "artik",
    "asagidaki",
    "asagidakilerden",
    "ayni",
    "bana",
    "bazi",
    "bazilari",
    "belirtilen",
    "ben",
    "beni",
    "benim",
    "beraber",
    "bile",
    "bir",
    "biraz",
    "birbiri",
    "birden",
    "birlikte",
    "biri",
    "birisi",
    "birsey",
    "biz",
    "bize",
    "bizi",
    "bizim",
    "buna",
    "bunda",
    "bundan",
    "bunlar",
    "bunlardan",
    "bunlari",
    "bunun",
    "burada",
    "butun",
    "bu",
    "cevap",
    "cunku",
    "cok",
    "cunku",
    "da",
    "daha",
    "dahi",
    "de",
    "defa",
    "degildir",
    "dolayi",
    "dolayisiyla",
    "dogru",
    "eger",
    "en",
    "esas",
    "etti",
    "ettigi",
    "ettiği",
    "gibi",
    "gore",
    "gosterir",
    "gorece",
    "hangi",
    "hangi",
    "hangileridir",
    "hangilerinden",
    "hangisi",
    "hangisidir",
    "hani",
    "hatta",
    "hem",
    "hepsi",
    "her",
    "herhangi",
    "hic",
    "hicbir",
    "i",
    "ii",
    "iii",
    "icin",
    "ile",
    "ilgili",
    "ise",
    "isim",
    "itibariyla",
    "kadar",
    "karsi",
    "karşı",
    "kendisi",
    "kendisine",
    "kendisini",
    "kez",
    "ki",
    "kim",
    "kime",
    "kimi",
    "kimin",
    "mu",
    "midir",
    "midir",
    "mudur",
    "muhtemelen",
    "na",
    "nasil",
    "neden",
    "nedeniyle",
    "ne",
    "nerede",
    "nereye",
    "nicin",
    "nin",
    "o",
    "olan",
    "olarak",
    "oldugu",
    "olduğu",
    "olup",
    "olur",
    "olmayan",
    "olmaktadir",
    "olmaz",
    "ona",
    "ondan",
    "onlar",
    "onlara",
    "onlardan",
    "onlari",
    "onu",
    "onun",
    "orada",
    "ortaya",
    "oysa",
    "pek",
    "rağmen",
    "rağmen",
    "sadece",
    "seklinde",
    "sekilde",
    "sonra",
    "sureyle",
    "tarafindan",
    "tarz",
    "tam",
    "tamam",
    "tanim",
    "tanimi",
    "uzere",
    "uzerinde",
    "ve",
    "veya",
    "vardir",
    "vardır",
    "yer",
    "yerine",
    "yerini",
    "yerler",
    "yine",
    "yonelik",
    "yonuyle",
    "yukarida",
    "yukaridaki",
}

GENERIC_PHRASES = {
    "asagidakilerden hangisi",
    "hangisi asagidakilerden",
    "yukaridaki parca gore",
    "bu parcaya gore",
    "bu soruya gore",
}

GENERIC_KEY_TERMS = {
    "bilgi",
    "cevap",
    "ders",
    "dini",
    "durum",
    "gore",
    "göre",
    "hangisi",
    "ilgili",
    "islam",
    "konu",
    "metin",
    "ornek",
    "örnek",
    "soru",
    "soruda",
    "verilen",
    "yukaridaki",
}

QUESTION_TYPE_PATTERNS = [
    ("Olumsuz eleme", [r"hangisi.*değildir", r"hangisi.*degildir", r"yer almaz", r"söylenemez", r"soylenemez", r"yanlıştır", r"yanlistir"]),
    ("Eslestirme", [r"birlikte verilmiştir", r"birlikte verilmiştir", r"eşleştirm", r"eslestirm", r"hangi ikili", r"hangi kavram ikilisi"]),
    ("Paragraf yorum", [r"bu parçaya göre", r"parçaya göre", r"parcaya gore", r"metne göre", r"metne gore"]),
    ("Coklu onermeler", [r"yukarıdakilerden hangileri", r"yukaridakilerden hangileri", r"numaralanmış", r"numaralandırılmış", r"i, ii", r"i ii iii"]),
    ("Siralama", [r"sıralama", r"siralama", r"kronolojik", r"sirasiyla", r"önce", r"sonra"]),
    ("Kavram / terim", [r"hangi kavram", r"hangi terim", r"adlandırılır", r"adlandirilir", r"isimlendirilir", r"isimlendirilmiştir"]),
    ("Vaka / uygulama", [r"öğretmen", r"ogrenci", r"öğrenci", r"bir din görevlisi", r"bir kisi", r"örnek", r"ornek", r"durum", r"olay"]),
]


SEMANTIC_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_SEMANTIC_MODEL_CACHE = None
_SEMANTIC_MODEL_ERROR = None


def _pick(question: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in question and question[key] not in (None, ""):
            return question[key]
    return None


def normalize_text(value: str) -> str:
    value = str(value or "").lower()
    value = unicodedata.normalize("NFKC", value).replace("\u0307", "")
    value = (
        value.replace("’", "'")
        .replace("`", "'")
        .replace("“", '"')
        .replace("”", '"')
    )
    value = re.sub(r"(?<=\w)'(?=\w)", "", value)
    value = value.replace("-", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def tokenize_text(value: str) -> List[str]:
    tokens = re.findall(r"[0-9a-zA-ZçğıöşüÇĞİÖŞÜâîûÂÎÛ]+", normalize_text(value), re.UNICODE)
    cleaned = []
    for token in tokens:
        token = token.lower()
        if token.isdigit():
            continue
        if len(token) < 3:
            continue
        if token in STOPWORDS:
            continue
        cleaned.append(token)
    return cleaned


def extract_phrases(tokens: List[str], top_n: int = 6) -> List[str]:
    if not tokens:
        return []

    phrase_counter: Counter[str] = Counter()
    for size in (2, 3):
        for index in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[index:index + size]).strip()
            if len(phrase) < 7:
                continue
            if phrase in GENERIC_PHRASES:
                continue
            phrase_counter[phrase] += 1

    return [phrase for phrase, _ in phrase_counter.most_common(top_n)]


def extract_key_terms(tokens: List[str], top_n: int = 6) -> List[str]:
    key_terms = []
    for token in tokens:
        if token in GENERIC_KEY_TERMS:
            continue
        if len(token) < 4:
            continue
        if token not in key_terms:
            key_terms.append(token)
        if len(key_terms) >= top_n:
            break
    return key_terms


def infer_question_type(text: str) -> str:
    normalized = normalize_text(text)
    for label, patterns in QUESTION_TYPE_PATTERNS:
        if any(re.search(pattern, normalized) for pattern in patterns):
            return label
    if "hangisi" in normalized:
        return "Dogrudan bilgi"
    return "Aciklama / yorum"


def normalize_question_record(question: Dict[str, Any]) -> Dict[str, Any]:
    yil = _pick(question, "yil", "y")
    ders = _pick(question, "ders", "d") or ""
    konu = _pick(question, "konu", "k") or ""
    soru_no = _pick(question, "soru_no", "no") or "?"
    soru_metni = _pick(question, "soru_metni", "raw", "text") or ""
    siklar = _pick(question, "siklar", "options") or {}

    if isinstance(siklar, dict):
        secenekler_text = " ".join(str(value) for value in siklar.values())
    else:
        secenekler_text = str(siklar or "")

    full_text = " ".join(part for part in [str(soru_metni), secenekler_text] if part).strip()
    tokens = tokenize_text(full_text)
    phrases = extract_phrases(tokens)
    key_terms = extract_key_terms(tokens)
    signature = set(tokens) | {f"bg:{phrase}" for phrase in phrases[:4]}
    question_type = infer_question_type(soru_metni or full_text)

    return {
        "yil": yil,
        "ders": str(ders),
        "konu": str(konu),
        "soru_no": soru_no,
        "soru_metni": str(soru_metni),
        "full_text": full_text,
        "tokens": tokens,
        "phrases": phrases,
        "key_terms": key_terms,
        "signature": signature,
        "question_type": question_type,
    }


def _candidate_keys(question: Dict[str, Any]) -> List[str]:
    keys = []
    keys.extend(f"p:{phrase}" for phrase in question.get("phrases", [])[:4])
    keys.extend(f"k:{term}" for term in question.get("key_terms", [])[:4])
    keys.extend(
        f"t:{token}"
        for token in question.get("tokens", [])
        if len(token) >= 5
    )
    deduped = []
    for key in keys:
        if key not in deduped:
            deduped.append(key)
        if len(deduped) >= 10:
            break
    return deduped


def _generate_candidate_pairs(
    questions: List[Dict[str, Any]],
    *,
    max_bucket_size: int = 80,
    max_fallback_group_size: int = 36,
) -> List[tuple]:
    if len(questions) < 2:
        return []

    pair_votes: Counter[tuple] = Counter()
    inverted_index: Dict[str, List[int]] = defaultdict(list)

    for idx, question in enumerate(questions):
        for key in _candidate_keys(question):
            prior_indexes = inverted_index[key]
            if len(prior_indexes) <= max_bucket_size:
                for previous_idx in prior_indexes:
                    pair_votes[(previous_idx, idx)] += 1
            prior_indexes.append(idx)

    # Kucuk ve ayni baglamdaki gruplar icin aday kapsamini koru.
    grouped: Dict[tuple, List[int]] = defaultdict(list)
    for idx, question in enumerate(questions):
        grouped[(question.get("ders"), question.get("konu"), question.get("question_type"))].append(idx)

    for indexes in grouped.values():
        if 2 <= len(indexes) <= max_fallback_group_size:
            for offset, left_idx in enumerate(indexes):
                for right_idx in indexes[offset + 1:]:
                    pair_votes[(left_idx, right_idx)] += 1

    return [pair for pair, _ in pair_votes.items()]


def _get_semantic_model():
    global _SEMANTIC_MODEL_CACHE, _SEMANTIC_MODEL_ERROR
    if _SEMANTIC_MODEL_CACHE is not None:
        return _SEMANTIC_MODEL_CACHE, None
    if _SEMANTIC_MODEL_ERROR is not None:
        return None, _SEMANTIC_MODEL_ERROR
    if SentenceTransformer is None:
        _SEMANTIC_MODEL_ERROR = "sentence-transformers kurulu degil"
        return None, _SEMANTIC_MODEL_ERROR

    try:
        _SEMANTIC_MODEL_CACHE = SentenceTransformer(SEMANTIC_MODEL_NAME)
        return _SEMANTIC_MODEL_CACHE, None
    except Exception as exc:
        _SEMANTIC_MODEL_ERROR = str(exc)
        return None, _SEMANTIC_MODEL_ERROR


def _build_semantic_index(questions: List[Dict[str, Any]], use_semantic: bool = False) -> Dict[str, Any]:
    if not use_semantic or not questions:
        return {"enabled": False, "backend": "kapali", "vectors": None}

    texts = [question.get("full_text") or question.get("soru_metni") or "" for question in questions]

    if np is not None:
        model, model_error = _get_semantic_model()
        if model is not None:
            try:
                vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
                return {
                    "enabled": True,
                    "backend": f"sentence-transformers:{SEMANTIC_MODEL_NAME}",
                    "vectors": vectors,
                }
            except Exception as exc:
                model_error = str(exc)

        if TfidfVectorizer is not None:
            try:
                vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
                matrix = vectorizer.fit_transform(texts)
                return {
                    "enabled": True,
                    "backend": f"tfidf-char-fallback ({model_error or 'semantic model unavailable'})",
                    "vectors": matrix,
                }
            except Exception as exc:
                return {"enabled": False, "backend": f"kapali ({exc})", "vectors": None}

        if model_error:
            return {"enabled": False, "backend": f"kapali ({model_error})", "vectors": None}

    return {"enabled": False, "backend": "kapali (numpy unavailable)", "vectors": None}


def _semantic_score(semantic_index: Dict[str, Any], left_idx: int, right_idx: int) -> Optional[float]:
    if not semantic_index.get("enabled"):
        return None

    vectors = semantic_index.get("vectors")
    if vectors is None:
        return None

    try:
        left = vectors[left_idx]
        right = vectors[right_idx]
        if np is not None and hasattr(left, "shape") and hasattr(right, "shape"):
            if hasattr(left, "toarray"):
                value = float(left.multiply(right).sum())
            else:
                value = float(np.dot(left, right))
            return max(0.0, min(value, 1.0))
    except Exception:
        return None
    return None


def filter_questions(
    questions: Iterable[Dict[str, Any]],
    year: Optional[Any] = None,
    subject: Optional[str] = None,
    topic: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filtered = []
    for question in questions:
        item = normalize_question_record(question)

        if year not in (None, "", "Tum yillar", "Tüm yıllar"):
            try:
                if int(item["yil"]) != int(year):
                    continue
            except Exception:
                continue

        if subject not in (None, "", "Tum dersler", "Tüm dersler"):
            if item["ders"] != subject:
                continue

        if topic not in (None, "", "Tum konular", "Tüm konular"):
            if item["konu"] != topic:
                continue

        filtered.append(item)
    return filtered


def _question_similarity(
    q1: Dict[str, Any],
    q2: Dict[str, Any],
    *,
    semantic_score: Optional[float] = None,
) -> float:
    if not q1["signature"] or not q2["signature"]:
        return 0.0

    if q1["ders"] != q2["ders"] and q1["konu"] != q2["konu"] and q1["question_type"] != q2["question_type"]:
        return 0.0

    inter = len(q1["signature"].intersection(q2["signature"]))
    union = len(q1["signature"].union(q2["signature"]))
    if not union:
        return 0.0

    score = inter / union
    if q1["konu"] and q1["konu"] == q2["konu"]:
        score += 0.05
    if q1["question_type"] == q2["question_type"]:
        score += 0.03
    if semantic_score is not None:
        score = score * 0.72 + semantic_score * 0.28
    return min(score, 0.99)


def _overlap_terms(q1: Dict[str, Any], q2: Dict[str, Any], limit: int = 5) -> List[str]:
    common_phrases = [phrase for phrase in q1["phrases"] if phrase in q2["phrases"]]
    common_key_terms = [term for term in q1.get("key_terms", []) if term in q2.get("key_terms", [])]
    common_tokens = sorted(
        token
        for token in q1["tokens"]
        if token in q2["tokens"] and len(token) > 3
    )

    result = []
    for phrase in common_phrases + common_key_terms + common_tokens:
        if phrase not in result:
            result.append(phrase)
        if len(result) >= limit:
            break
    return result


def find_similar_pairs(
    questions: List[Dict[str, Any]],
    threshold: float = 0.55,
    limit: int = 20,
    semantic_index: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    pairs: List[Dict[str, Any]] = []
    candidate_pairs = _generate_candidate_pairs(questions)
    if not candidate_pairs and len(questions) <= 80:
        candidate_pairs = [(i, j) for i in range(len(questions)) for j in range(i + 1, len(questions))]

    for i, j in candidate_pairs:
        semantic_score = _semantic_score(semantic_index or {}, i, j)
        score = _question_similarity(questions[i], questions[j], semantic_score=semantic_score)
        if score < threshold:
            continue
        pairs.append(
            {
                "score": score,
                "semantic_score": semantic_score,
                "q1": questions[i],
                "q2": questions[j],
                "overlap_terms": _overlap_terms(questions[i], questions[j]),
            }
        )

    pairs.sort(key=lambda item: item["score"], reverse=True)
    return pairs[:limit]


def build_similarity_clusters(
    questions: List[Dict[str, Any]],
    threshold: float = 0.57,
    limit: int = 8,
    semantic_index: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    if not questions:
        return []

    grouped: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for question in questions:
        grouped[(question["konu"], question["question_type"])].append(question)

    clusters = []
    for (topic, question_type), cluster_questions in grouped.items():
        if len(cluster_questions) < 2:
            continue

        phrase_counter: Counter[str] = Counter()
        years = sorted({q["yil"] for q in cluster_questions if q["yil"]})

        for question in cluster_questions:
            phrase_counter.update(set(question["phrases"][:3] + question.get("key_terms", [])[:3]))

        avg_similarity = 0.0
        pair_count = 0
        local_pairs = _generate_candidate_pairs(cluster_questions, max_fallback_group_size=20)
        if not local_pairs and len(cluster_questions) <= 24:
            local_pairs = [
                (i, j)
                for i in range(len(cluster_questions))
                for j in range(i + 1, len(cluster_questions))
            ]

        for i, j in local_pairs:
            score = _question_similarity(cluster_questions[i], cluster_questions[j])
            if score >= threshold:
                avg_similarity += score
                pair_count += 1

        clusters.append(
            {
                "size": len(cluster_questions),
                "topic": topic,
                "question_type": question_type,
                "years": years,
                "phrases": [phrase for phrase, _ in phrase_counter.most_common(4)],
                "avg_similarity": (avg_similarity / pair_count) if pair_count else 0.0,
                "sample_questions": cluster_questions[:3],
            }
        )

    clusters.sort(
        key=lambda item: (item["size"], item["avg_similarity"], len(item["years"])),
        reverse=True,
    )
    return clusters[:limit]


def summarize_topic_counts(questions: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    topic_counter = Counter(q["konu"] for q in questions if q["konu"])
    return [
        {"topic": topic, "count": count}
        for topic, count in topic_counter.most_common(limit)
    ]


def summarize_question_types(questions: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    type_counter = Counter(q["question_type"] for q in questions)
    return [
        {"question_type": question_type, "count": count}
        for question_type, count in type_counter.most_common(limit)
    ]


def summarize_subtopics_by_topic(
    questions: List[Dict[str, Any]],
    limit_topics: int = 5,
    phrases_per_topic: int = 4,
) -> List[Dict[str, Any]]:
    by_topic: Dict[str, Counter[str]] = defaultdict(Counter)
    for question in questions:
        if not question["konu"]:
            continue
        by_topic[question["konu"]].update(set(question["phrases"][:3] + question.get("key_terms", [])[:3]))

    topic_counts = Counter(q["konu"] for q in questions if q["konu"])
    result = []
    for topic, _ in topic_counts.most_common(limit_topics):
        result.append(
            {
                "topic": topic,
                "phrases": [phrase for phrase, _ in by_topic[topic].most_common(phrases_per_topic)],
            }
        )
    return result


def _scored_frequency_summary(
    phrase_rows: Dict[str, List[Dict[str, Any]]],
    recent_years: List[int],
    limit: int,
) -> List[Dict[str, Any]]:
    rows = []
    for label, items in phrase_rows.items():
        years = sorted({int(item["yil"]) for item in items if item.get("yil")})
        total = len(items)
        recent = sum(1 for item in items if item.get("yil") in recent_years)
        score = total * 1.5 + len(years) * 1.2 + recent * 2.0
        rows.append(
            {
                "label": label,
                "count": total,
                "years": years,
                "recent_count": recent,
                "score": round(score, 2),
            }
        )
    rows.sort(key=lambda row: (row["score"], row["count"], len(row["years"])), reverse=True)
    return rows[:limit]


def predict_topics(history_questions: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    if not history_questions:
        return []

    years = sorted({int(q["yil"]) for q in history_questions if q.get("yil")})
    recent_years = years[-3:] if years else []
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for question in history_questions:
        if question["konu"]:
            grouped[question["konu"]].append(question)

    rows = _scored_frequency_summary(grouped, recent_years, limit)
    for row in rows:
        row["topic"] = row.pop("label")
    return rows


def predict_subtopics(
    history_questions: List[Dict[str, Any]],
    selected_topic: Optional[str] = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    relevant = [
        question
        for question in history_questions
        if question["phrases"] and (not selected_topic or question["konu"] == selected_topic)
    ]
    if not relevant:
        return []

    years = sorted({int(q["yil"]) for q in relevant if q.get("yil")})
    recent_years = years[-3:] if years else []
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for question in relevant:
        for phrase in set(question["phrases"][:3] + question.get("key_terms", [])[:3]):
            grouped[phrase].append(question)

    grouped = {label: items for label, items in grouped.items() if len(items) >= 2}
    rows = _scored_frequency_summary(grouped, recent_years, limit)
    for row in rows:
        row["subtopic"] = row.pop("label")
    return rows


def build_similarity_report(
    scope_questions: List[Dict[str, Any]],
    history_questions: Optional[List[Dict[str, Any]]] = None,
    pair_threshold: float = 0.55,
    use_semantic: bool = False,
) -> Dict[str, Any]:
    normalized_scope = [normalize_question_record(question) for question in scope_questions]
    normalized_history = (
        [normalize_question_record(question) for question in history_questions]
        if history_questions is not None
        else normalized_scope
    )
    semantic_index = _build_semantic_index(normalized_scope, use_semantic=use_semantic)
    candidate_pairs = _generate_candidate_pairs(normalized_scope)

    selected_topic = ""
    if normalized_scope:
        unique_topics = {q["konu"] for q in normalized_scope if q["konu"]}
        if len(unique_topics) == 1:
            selected_topic = list(unique_topics)[0]

    return {
        "scope_total": len(normalized_scope),
        "history_total": len(normalized_history),
        "semantic_backend": semantic_index.get("backend", "kapali"),
        "candidate_pair_count": len(candidate_pairs),
        "question_types": summarize_question_types(normalized_scope),
        "topic_counts": summarize_topic_counts(normalized_scope),
        "subtopics_by_topic": summarize_subtopics_by_topic(normalized_scope),
        "clusters": build_similarity_clusters(normalized_scope, semantic_index=semantic_index),
        "similar_pairs": find_similar_pairs(normalized_scope, threshold=pair_threshold, semantic_index=semantic_index),
        "likely_topics": predict_topics(normalized_history),
        "likely_subtopics": predict_subtopics(normalized_history, selected_topic=selected_topic),
    }
