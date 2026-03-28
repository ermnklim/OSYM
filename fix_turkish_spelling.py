#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import win32com.client as win32


BASE_DIR = Path(__file__).resolve().parent / "Worde_Yapistir"
TOKEN_RE = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû]+(?:['-][A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû]+)*")
TURKISH_CHARS = "çğıöşüÇĞİÖŞÜ"
TURKISH_UPPER_MAP = str.maketrans({"i": "İ", "ı": "I"})
TURKISH_LOWER_MAP = str.maketrans({"I": "ı", "İ": "i"})
MANUAL_TOKEN_MAP = {
    "oabt": "öabt",
    "ihl": "ihl",
    "ayni": "aynı",
    "sahsi": "şahsi",
    "seklinde": "şeklinde",
    "kotu": "kötü",
    "tur": "tür",
    "gerceklesen": "gerçekleşen",
    "gerceklesmesi": "gerçekleşmesi",
    "gerceklesenin": "gerçekleşenin",
    "gerceklestigi": "gerçekleştiği",
    "gerceklesmistir": "gerçekleşmiştir",
    "gerceklestirmeyi": "gerçekleştirmeyi",
    "gerceklestirmeye": "gerçekleştirmeye",
    "gerceklesebilecegini": "gerçekleşebileceğini",
    "gerceklesme": "gerçekleşme",
    "gerceklestirmis": "gerçekleştirmiş",
    "gerceklestigini": "gerçekleştiğini",
    "gerceklestirebilecegi": "gerçekleştirebileceği",
    "gerceklestirecek": "gerçekleştirecek",
    "gerceklesmesini": "gerçekleşmesini",
    "gerceklestirilen": "gerçekleştirilen",
    "gerceklesir": "gerçekleşir",
    "gerceklestirilmis": "gerçekleştirilmiş",
    "gerceklestirmesi": "gerçekleştirmesi",
    "gerceklestirilir": "gerçekleştirilir",
    "gerceklestirecegi": "gerçekleştireceği",
    "karsi": "karşı",
    "karsiya": "karşıya",
    "karsisinda": "karşısında",
}
MANUAL_TEXT_REPLACEMENTS = {
    "Kur'an-i": "Kur'an-ı",
    "Kur'an'i": "Kur'an'ı",
    "Kur'anin": "Kur'an'ın",
    "Kur'anin'": "Kur'an'ın",
}
SKIP_TOKENS = {
    "dkab",
    "dhbt",
    "mbsts",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "txt",
    "nun",
}


@dataclass
class ReplacementResult:
    token_cache: Dict[str, str]
    file_change_counts: Dict[str, int]
    token_change_counts: Counter


def turkish_upper(value: str) -> str:
    return value.translate(TURKISH_UPPER_MAP).upper()


def turkish_lower(value: str) -> str:
    return value.translate(TURKISH_LOWER_MAP).lower()


def turkish_title(value: str) -> str:
    if not value:
        return value
    lowered = turkish_lower(value)
    return turkish_upper(lowered[:1]) + lowered[1:]


def fold_text(value: str) -> str:
    translation = str.maketrans("çğıöşüÇĞİÖŞÜÂâÎîÛû", "cgiosuCGIOSUAaIiUu")
    folded = value.translate(translation)
    folded = unicodedata.normalize("NFKD", folded)
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    folded = folded.replace("’", "'").replace("`", "'")
    folded = folded.replace("-", "").replace("'", "")
    return folded.lower()


def turkish_char_score(value: str) -> int:
    return sum(ch in TURKISH_CHARS for ch in value)


def preserve_case(original: str, replacement: str) -> str:
    if not replacement:
        return original
    if original.isupper():
        return turkish_upper(replacement)
    if original.islower():
        return turkish_lower(replacement)
    if original[:1].isupper() and original[1:].islower():
        return turkish_title(replacement)
    return replacement


def should_skip_token(token: str) -> bool:
    lowered = turkish_lower(token)
    if lowered in SKIP_TOKENS:
        return True
    if len(token) < 2:
        return True
    if re.fullmatch(r"[IVXLCDM]+", token):
        return True
    if "-" in token:
        return True
    if any(ch in "ÂâÎîÛû" for ch in token):
        return True
    if any(ch in TURKISH_CHARS for ch in token):
        return True
    if token.count("'") > 1:
        return True
    if not any(ch.lower() in "aeiou" for ch in token):
        return True
    return False


def iter_target_files(base_dir: Path, max_year: int) -> Iterable[Path]:
    files = []
    for path in base_dir.glob("*_Sorulari.txt"):
        match = re.match(r"(\d{4})_", path.name)
        if not match:
            continue
        year = int(match.group(1))
        if year <= max_year:
            files.append((year, path.name, path))
    for _, _, path in sorted(files, key=lambda item: (-item[0], item[1])):
        yield path


class WordSpellHelper:
    def __init__(self) -> None:
        self.app = win32.Dispatch("Word.Application")
        self.app.Visible = False
        self.doc = self.app.Documents.Add()
        self.doc.Content.LanguageID = 1055

    def close(self) -> None:
        try:
            self.doc.Close(False)
        finally:
            self.app.Quit()

    def check_spelling(self, word: str) -> bool:
        return bool(self.app.CheckSpelling(word))

    def get_suggestions(self, word: str) -> List[str]:
        suggestions = self.app.GetSpellingSuggestions(word)
        return [suggestions.Item(index).Name for index in range(1, suggestions.Count + 1)]


def choose_replacement(helper: WordSpellHelper, token: str, cache: Dict[str, str]) -> str:
    if token in cache:
        return cache[token]

    if should_skip_token(token):
        cache[token] = token
        return token

    lookup_token = token.lower() if token.isupper() else token
    lowered_lookup = turkish_lower(lookup_token)

    if lowered_lookup in MANUAL_TOKEN_MAP:
        replacement = preserve_case(token, MANUAL_TOKEN_MAP[lowered_lookup])
        cache[token] = replacement
        return replacement

    if helper.check_spelling(lookup_token):
        replacement = preserve_case(token, lookup_token)
        cache[token] = replacement
        return replacement

    lookup_fold = fold_text(lookup_token)
    matching_suggestions: List[str] = []
    for suggestion in helper.get_suggestions(lookup_token):
        if fold_text(suggestion) != lookup_fold:
            continue
        if "'" in token and "'" not in suggestion:
            continue
        matching_suggestions.append(suggestion)

    if not matching_suggestions:
        cache[token] = token
        return token

    best_suggestion = matching_suggestions[0]
    replacement = preserve_case(token, best_suggestion)
    cache[token] = replacement
    return replacement


def replace_tokens(text: str, helper: WordSpellHelper, cache: Dict[str, str]) -> tuple[str, Counter]:
    changes = Counter()

    def _replace(match: re.Match[str]) -> str:
        original = match.group(0)
        updated = choose_replacement(helper, original, cache)
        if updated != original:
            changes[(original, updated)] += 1
        return updated

    updated_text = TOKEN_RE.sub(_replace, text)
    for source, target in MANUAL_TEXT_REPLACEMENTS.items():
        if source in updated_text:
            count = updated_text.count(source)
            updated_text = updated_text.replace(source, target)
            changes[(source, target)] += count
    updated_text = fix_question_particles(updated_text, changes)
    return updated_text, changes


def _last_vowel(word: str) -> str:
    vowels = "aeıioöuüAEIİOÖUÜ"
    for ch in reversed(word):
        if ch in vowels:
            return ch
    return ""


def _question_particle_for(word: str) -> str:
    last_vowel = _last_vowel(word)
    if last_vowel in "eEiİ":
        return "mi"
    if last_vowel in "aAıI":
        return "mı"
    if last_vowel in "oOuU":
        return "mu"
    if last_vowel in "öÖüÜ":
        return "mü"
    return "mi"


def fix_question_particles(text: str, changes: Counter) -> str:
    pattern = re.compile(r"(\b[A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû']+\b)(\s+)(mi)(?=(?:[?.!,;:)\]\"'»”]|$))")

    def _replace(match: re.Match[str]) -> str:
        word = match.group(1)
        spacing = match.group(2)
        original = match.group(3)
        replacement = _question_particle_for(word)
        if replacement != original:
            changes[(original, replacement)] += 1
        return f"{word}{spacing}{replacement}"

    return pattern.sub(_replace, text)


def process_files(base_dir: Path, max_year: int, dry_run: bool = False) -> ReplacementResult:
    helper = WordSpellHelper()
    file_change_counts: Dict[str, int] = {}
    token_change_counts: Counter = Counter()
    token_cache: Dict[str, str] = {}
    try:
        for path in iter_target_files(base_dir, max_year):
            text = path.read_text(encoding="utf-8")
            updated_text, changes = replace_tokens(text, helper, token_cache)
            if updated_text != text:
                file_change_counts[path.name] = sum(changes.values())
                token_change_counts.update(changes)
                if not dry_run:
                    path.write_text(updated_text, encoding="utf-8")
    finally:
        helper.close()
    return ReplacementResult(
        token_cache=token_cache,
        file_change_counts=file_change_counts,
        token_change_counts=token_change_counts,
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Word imla önerileriyle sınav metinlerindeki Türkçe karakterleri düzeltir.")
    parser.add_argument("--max-year", type=int, default=2025, help="Bu yıl ve öncesindeki dosyaları işler.")
    parser.add_argument("--base-dir", type=Path, default=BASE_DIR, help="İşlenecek klasör.")
    parser.add_argument("--dry-run", action="store_true", help="Dosyalara yazmadan sadece özet rapor üretir.")
    parser.add_argument("--top", type=int, default=40, help="Raporda gösterilecek en sık dönüşüm sayısı.")
    args = parser.parse_args()

    result = process_files(args.base_dir, args.max_year, dry_run=args.dry_run)
    print(f"İşlenen klasör: {args.base_dir}")
    print(f"Değişen dosya sayısı: {len(result.file_change_counts)}")
    if result.file_change_counts:
        for name, count in sorted(result.file_change_counts.items(), key=lambda item: (-int(item[0][:4]), item[0])):
            print(f"{name}: {count} değişiklik")

    print("")
    print("En sık dönüşümler:")
    for (source, target), count in result.token_change_counts.most_common(args.top):
        print(f"{count}x {source} -> {target}")


if __name__ == "__main__":
    main()
