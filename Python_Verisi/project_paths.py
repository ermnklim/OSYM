#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
WORDE_DIR = ROOT_DIR / "Worde_Yapistir"
PYTHON_VERISI_DIR = ROOT_DIR / "Python_Verisi"
TEMIZ_METIN_DIR = PYTHON_VERISI_DIR / "temiz_metin"
GORSSELLER_DIR = ROOT_DIR / "Gorseller"
TABLOLAR_DIR = ROOT_DIR / "Tablolar"


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
