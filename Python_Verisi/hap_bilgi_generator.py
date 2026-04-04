#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    from analiz_araci import SUBTOPIC_KEYWORDS, extract_subtopics
    from project_paths import PYTHON_VERISI_DIR, WORDE_DIR, ensure_directory
    from question_bank import (
        format_subject_label as format_exam_subject_label,
        iter_exam_files,
        parse_questions_from_file,
    )
    from topic_catalog import (
        normalize_topic_name,
        sanitize_topic_for_filename,
        sort_topics_for_exam_family,
    )
except ImportError:
    from Python_Verisi.analiz_araci import SUBTOPIC_KEYWORDS, extract_subtopics
    from Python_Verisi.project_paths import PYTHON_VERISI_DIR, WORDE_DIR, ensure_directory
    from Python_Verisi.question_bank import (
        format_subject_label as format_exam_subject_label,
        iter_exam_files,
        parse_questions_from_file,
    )
    from Python_Verisi.topic_catalog import (
        normalize_topic_name,
        sanitize_topic_for_filename,
        sort_topics_for_exam_family,
    )


HAP_BILGI_DIR = PYTHON_VERISI_DIR / "hap_bilgiler"
HAP_BILGI_INDEX = HAP_BILGI_DIR / "index.json"

SUBJECT_FAMILY_LABELS = {
    "DKAB": "ÖABT DKAB",
    "IHL": "ÖABT İHL",
    "MBSTS": "MBSTS",
}

STYLE_ORDER = (
    "Kavram / eşleştirme",
    "İstisna / ters kök",
    "Doğru kombinasyon",
    "Örnek / uygulama",
    "Yorum / çıkarım",
    "Genel bilgi",
)

QUESTION_STYLE_PATTERNS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    (
        "İstisna / ters kök",
        (
            r"yer almaz",
            r"söylenemez",
            r"değildir",
            r"gösterilemez",
            r"verilemez",
            r"olamaz",
            r"kapsamında değerlendirilemez",
        ),
    ),
    (
        "Doğru kombinasyon",
        (
            r"hangileri",
            r"ifadelerinden hangileri",
            r"eşleştirmelerinden hangileri",
        ),
    ),
    (
        "Örnek / uygulama",
        (
            r"örnektir",
            r"örneğine",
            r"örnek olarak",
            r"uygun bir örnek",
            r"boşluklara yazabileceği",
        ),
    ),
    (
        "Yorum / çıkarım",
        (
            r"söylenebilir",
            r"göstermektedir",
            r"ortaya koymaktadır",
            r"ifade etmektedir",
            r"ulaştığını göstermektedir",
        ),
    ),
    (
        "Kavram / eşleştirme",
        (
            r"hangisidir",
            r"hangisinde verilmiştir",
            r"hangi kavram",
            r"hangi sure",
            r"hangi eser",
            r"hangi peygamber",
            r"ifade edilir",
            r"adlandırılır",
            r"adı verilmiştir",
            r"karşılığı",
        ),
    ),
)

GENERIC_LINE_PATTERNS = (
    r"^I+\.$",
    r"^V+$",
    r"^[IVXLCDM]+\.$",
    r"^[IVXLCDM]+\.\s*$",
    r"^[A-E]\)$",
    r"^Altı çizili kelimeler:?$",
)

ADDITIONAL_TOPIC_HINTS: Dict[str, Tuple[Tuple[str, Tuple[str, ...]], ...]] = {
    "Kelam / Akaid": (
        (
            "Kelam terminolojisi",
            (
                r"\bkelam\b",
                r"mesail",
                r"vesail",
                r"mead",
                r"akıl[- ]nakil",
                r"eş[’']?ari",
                r"matüridi",
                r"mürcie",
                r"şerrin varlığı",
                r"gaye ve nizam",
            ),
        ),
    ),
    "Siyer": (
        (
            "Siyer ipuçları",
            (
                r"cahiliye",
                r"habeşistan",
                r"ca[’']?fer b\. eb[ûu] talib",
                r"ash[âa]b[-ıi ]?suffe",
                r"mute savaşı",
                r"belk[aâ]",
                r"hicretin",
                r"hz\. muhammed",
            ),
        ),
    ),
    "İslam Tarihi": (
        (
            "Tarih ipuçları",
            (
                r"ecn[aâ]deyn",
                r"idr[iî]s[iî]ler",
                r"ağleb[iî]ler",
                r"karahanl[ıi]lar",
                r"gazneliler",
                r"emev[iî]ler",
                r"abbas[iî]ler",
                r"hz\. eb[ûu] bekir",
                r"kerbel[aâ]",
                r"zenc [iı]syan",
                r"nebat[iî]ler",
                r"gass[aâ]n[iî]ler",
                r"hireliler",
                r"petra",
                r"islam [öo]ncesi arap devlet",
            ),
        ),
    ),
    "Hadis": (
        (
            "Hadis literatürü",
            (
                r"m[üu]tev[aâ]tir",
                r"tedvin",
                r"m[üu]sned",
                r"musannef",
                r"s[üu]nen",
                r"c[aâ]mi",
                r"isnad",
                r"sened",
            ),
        ),
    ),
    "Fıkıh": (
        (
            "Fıkıh ek ipuçları",
            (
                r"m[üu]stehap",
                r"ihram",
                r"tahall[üu]l",
                r"hedy",
                r"akika",
                r"adak kurban",
                r"irtifak",
                r"mür[ûu]r",
                r"mecr[aâ]",
                r"mes[iî]l",
                r"şirb",
                r"fuz[ûu]l[iî]",
                r"iddet",
                r"ashab[üu]['’]?l-fer[aâ]iz",
                r"asabe",
                r"karz",
                r"kefalet",
                r"rehin",
                r"hibe",
            ),
        ),
    ),
    "Fıkıh Usulü": (
        (
            "Usul ipuçları",
            (
                r"ink[ıi]r[aâ]z[üu]['’]?l-asr",
                r"vacip t[üu]r",
                r"usulc[üu]",
                r"icma",
                r"m[üu]ctehid",
                r"delillerden hangisi",
                r"istihs[aâ]n",
            ),
        ),
    ),
    "İslam Mezhepleri ve Akımları": (
        (
            "Mezhep ve akım ipuçları",
            (
                r"mirz[aâ] gul[aâ]m",
                r"k[aâ]diy[aâ]n",
                r"lahor",
                r"d[üu]rz[iî]",
                r"zeydiyye",
                r"h[aâ]kim biemrill[aâ]h",
                r"hul[ûu]l",
                r"imamet",
            ),
        ),
    ),
    "Dinler Tarihi": (
        (
            "Dinler tarihi ipuçları",
            (
                r"s[aâ]bi[iî]lik",
                r"ginza",
                r"protestan",
                r"evharist",
                r"vaftiz",
                r"papan[ıi]n yan[ıi]lmazl[ıi][ğg][ıi]",
            ),
        ),
    ),
}


def _build_topic_inference_groups() -> Dict[str, Tuple[Tuple[str, Tuple[str, ...]], ...]]:
    grouped_patterns: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {}

    for topic_name, label_groups in SUBTOPIC_KEYWORDS.items():
        normalized_topic = normalize_topic_name(topic_name)
        grouped_patterns.setdefault(normalized_topic, []).extend(label_groups)

    for topic_name, label_groups in ADDITIONAL_TOPIC_HINTS.items():
        normalized_topic = normalize_topic_name(topic_name)
        grouped_patterns.setdefault(normalized_topic, []).extend(label_groups)

    return {
        topic_name: tuple(groups)
        for topic_name, groups in grouped_patterns.items()
    }


TOPIC_INFERENCE_GROUPS = _build_topic_inference_groups()

FORCED_TOPIC_OVERRIDES = {
    (2026, "MBSTS", 15): "Kelam / Akaid",
}

BASE_TOPIC_STUDY_NOTES: Dict[str, Tuple[str, ...]] = {
    "Kelam / Akaid": (
        "İman: kalp ile tasdik esastır; dil ile ikrar dünya ahkamı içindir.",
        "Tevhid, Allah'ın zatında, sıfatlarında ve fiillerinde bir olmasıdır.",
        "Sıfatlar genelde zati ve subuti başlığı altında çalışılır.",
        "Kader Allah'ın ezeli ilmi; kaza hükmün gerçekleşmesidir.",
        "Maturidilik akla daha geniş alan açar; Eşarilikte kudret ve irade vurgusu daha belirgindir.",
        "Ehl-i sünnete göre büyük günah işleyen mümin dinden çıkmaz.",
    ),
    "Fıkıh": (
        "Hüküm türleri: farz, vacip, sünnet, müstehap, mubah, mekruh ve haram.",
        "Farz inkarı küfür sayılır; vacip inkarı küfür sayılmaz ama sorumluluk doğurur.",
        "Abdestin farzları 4'tür; teyemmüm su yokluğu veya suyu kullanamama halinde devreye girer.",
        "Şart dışta, rükün ibadetin içindedir; bu ayrım sık karıştırılır.",
        "Zekatta nisap, yıl dolumu ve artıcı mal niteliği temel başlıklardır.",
        "Oruçta sadece kaza gereken durumlarla kaza+kefaret gereken durumları birlikte çalış.",
        "Miras, nikah engelleri, talak çeşitleri ve akitler tekrar isteyen başlıklardır.",
    ),
    "Fıkıh Usulü": (
        "Deliller sıralanırken kitap, sünnet, icma ve kıyas omurgayı oluşturur.",
        "Hüküm çıkarma usulünde lafız, delalet, illet ve maslahat başlıkları birlikte düşünülür.",
        "Kıyas için asıl, fer, illet ve hüküm unsurlarını ayır.",
        "İcma, istihsan, istishab ve örf gibi delilleri birbirine karıştırma.",
        "Vacip türleri, umum-husus ve mutlak-mukayyed ayrımları klasik soru alanıdır.",
    ),
    "Tefsir": (
        "Vahiy çeşitleri, nüzul sebepleri ve Mekki-Medeni ayrımı temel omurgadır.",
        "Mekki surelerde iman, ahiret ve tevhid; Medeni surelerde hukuk ve toplumsal düzen daha belirgindir.",
        "Muhkem anlamı açık; müteşabih yoruma daha açık metindir.",
        "Nesih, esbab-ı nüzul, garibü'l-Kur'an ve icazü'l-Kur'an kavramlarını birlikte tekrar et.",
        "Müfessir-yöntem eşleştirmelerinde Taberi rivayet, Razi dirayet, İbn Kesir rivayet ağırlıklıdır.",
    ),
    "Hadis": (
        "Hadisin iki ana unsuru sened ve metindir.",
        "Sahih, hasen ve zayıf ayrımında ravi adaleti ile zabtı temel ölçüdür.",
        "Merfu, mevkuf, maktu ile muttasıl, munkatı, mürsel, muallak ayrımlarını birlikte çalış.",
        "Cerh ve tadil raviyi değerlendiren ilimdir.",
        "Kütüb-i Sitte ve müelliflerini karıştırmamak için tablo halinde tekrar et.",
        "Mütevatirlik kıraat değil rivayet çokluğu ile ilgilidir.",
    ),
    "Kur'an-ı Kerim ve Tecvid": (
        "İzhar, idgam, iklab ve ihfa en temel tekrar alanıdır.",
        "Med çeşitleri, vakıf-ibtida, kalınlık-incelik ve kalkale birlikte çalışılmalıdır.",
        "Mahreç ve sıfat bilgisi kavramsal soruların çekirdeğini oluşturur.",
        "Kıraat imamları ve aşıra/aşere bilgisi genelde isim eşleştirmesi şeklinde gelir.",
        "Vakfın manayı bozduğu ve koruduğu yerleri örneklerle tekrar etmek faydalıdır.",
    ),
    "Siyer": (
        "Hicret sadece göç değil, İslam toplumunun kurumsallaşma eşiğidir.",
        "Medine Vesikası ilk toplumsal sözleşme örneklerinden biri olarak çalışılır.",
        "Bedir, Uhud ve Hendek sonuçları; Hudeybiye ise siyasi kazanım yönüyle bilinmelidir.",
        "Veda Hutbesi can-mal emniyeti, faiz yasağı ve insan hakları başlıklarıyla önemlidir.",
        "Mekke ve Medine dönemi olaylarını kronolojik zincir halinde çalış.",
    ),
    "İslam Tarihi": (
        "Dört Halife dönemi olaylarını kronolojik sırayla çalışmak çok verimlidir.",
        "Emeviler ve Abbasilerde siyasi kırılmalar, isyanlar ve idari yapı birlikte düşünülmelidir.",
        "Fetih hareketlerinde savaş-sonuç eşleştirmeleri sık karışır.",
        "Devlet-hanedan-coğrafya eşleştirmelerini tablo halinde tekrar etmek hız kazandırır.",
        "İslam öncesi Arap siyasi yapıları ile ilk fetih dönemi birlikte sorulabilir.",
    ),
    "İslam Mezhepleri ve Akımları": (
        "Hariciler büyük günah konusunda serttir; Mürcie ameli imandan ayırma eğilimindedir.",
        "Mutezile akıl vurgusu ve beş esasla tanınır.",
        "Şia'da imamet merkezi konudur; Caferilik, Zeydilik ve İsmaililik farkları bilinmelidir.",
        "Ehl-i sünnet ana damarı Maturidilik ve Eşarilik üzerinden düşünülür.",
        "Modern akımlarda kurucu isim, temel iddia ve coğrafya üçlüsünü birlikte çalış.",
    ),
    "Mezhepler Tarihi": (
        "Siyasi doğuş, itikadi farklılaşma ve coğrafi yayılım çizgisini birlikte okumak gerekir.",
        "Şia kolları, Haricilik ve modern dini akımlar karşılaştırmalı çalışılmalıdır.",
        "İmamet, büyük günah ve otorite başlıkları mezhep ayrımlarında belirleyicidir.",
        "Kurucu şahıs ve temel görüş eşleştirmeleri hızlı tekrar için idealdir.",
    ),
    "İslam Ahlakı ve Tasavvuf": (
        "Tasavvufta amaç ihsan bilinci ve nefis terbiyesidir.",
        "Zühd, takva, ihlas, murakabe, muhasebe ve tevekkül kavramlarını birlikte çalış.",
        "Tarikat, mürşid, mürid ve seyrüsüluk ilişkisi temel düzeyde bilinmelidir.",
        "Ahlakta niyet, irade, sorumluluk ve erdem kavramları öne çıkar.",
        "Gazali, Mevlana, Yunus Emre ve Hacı Bektaş Veli gibi isimler sık geçer.",
    ),
    "Dinler Tarihi": (
        "İlahi dinler ile beşeri dinler ayrımı temel çerçevedir.",
        "Yahudilikte Tevrat, Hristiyanlıkta İncil ve mezhep farkları sık sorulur.",
        "Hinduizm ve Budizm temel kavramları yüzeysel de olsa bilinmelidir.",
        "Benzerlik aramaktan çok ayırt edici özellik çalışmak daha verimlidir.",
        "Kutsal metin, ibadet ve kurucu şahıs üçlüsü karşılaştırmalı tekrar için uygundur.",
    ),
    "Din Eğitimi": (
        "Hedef, içerik, yöntem-teknik ve ölçme-değerlendirme ana çerçevedir.",
        "Sunuş, buluş ve araştırma-inceleme yoluyla öğretim ayrımları net bilinmelidir.",
        "Kazanım, içerik, öğrenme yaşantısı ve değerlendirme uyumlu kurulmalıdır.",
        "Öğrenci seviyesi, gelişim özellikleri ve bireysel farklar ders tasarımında belirleyicidir.",
        "Yapılandırmacı yaklaşım, aktif öğrenme ve değerler eğitimi başlıkları sık döner.",
    ),
    "Din Sosyolojisi": (
        "Din-toplum ilişkisi, kurumlaşma ve toplumsallaşma ana eksendir.",
        "Dini grup, cemaat, tarikat ve kurum kavramlarını birbirinden ayır.",
        "Sekülerleşme, modernleşme ve toplumsal değişim başlıkları birlikte düşünülmelidir.",
        "Dinî otorite, sosyal kontrol ve kimlik oluşumu sık karşılaştırılır.",
    ),
    "Din Psikolojisi": (
        "Dinî gelişim bireyin yaş, ihtiyaç ve psikolojik olgunluk çizgisiyle birlikte ele alınır.",
        "Tutum, güdü, kişilik ve deneyim kavramları din psikolojisinin temel dilidir.",
        "İnanç gelişimi, ergenlik ve yetişkinlik dönemleriyle ilişkilendirilerek çalışılmalıdır.",
        "Dinî duygu ve davranışın içsel-dışsal motivasyon farkı sık karışır.",
    ),
    "Din Felsefesi": (
        "Tanrı delilleri, kötülük problemi ve vahiy-akıl ilişkisi ana başlıklardır.",
        "Ontolojik, kozmolojik ve gaye-nizam delillerini karşılaştırmalı çalış.",
        "Din dili, mucize, özgürlük ve sorumluluk tartışmaları temel soru alanıdır.",
        "Teizm, deizm, ateizm ve agnostisizm ayrımları net olmalıdır.",
    ),
    "İslam Felsefesi": (
        "Kindi, Farabi, İbn Sina, Gazali ve İbn Rüşd ana isimlerdir.",
        "Akıl-vahiy ilişkisi, sudur, nefs ve mutluluk öğretisi temel eksenlerdendir.",
        "Filozof-eser-görüş eşleştirmeleri kısa kartlar halinde tekrar edilmelidir.",
        "Meşşailik ve işrakilik gibi ekollerin temel farkları bilinmelidir.",
    ),
    "İslam Kültür ve Medeniyeti": (
        "İlim, kurum, şehir ve sanat başlıkları birlikte ele alınmalıdır.",
        "Medrese, vakıf, kütüphane ve saray teşkilatı medeniyet sorularının çekirdeğidir.",
        "Bilim insanı-eser-alan eşleştirmeleri bu başlıkta hız kazandırır.",
        "Mimari, eğitim ve sosyal yardım kurumları karşılaştırmalı çalışılmalıdır.",
    ),
    "Din Hizmetleri ve Hitabet": (
        "Hutbe, vaaz, irşat ve temsil görevi birlikte düşünülmelidir.",
        "Hedef kitle, iletişim dili ve dini rehberlik ilkeleri temel başlıklardır.",
        "Din hizmetlerinde planlama, uygulama ve geri bildirim döngüsü önemlidir.",
        "Hitabette açıklık, uygun üslup ve güvenilir temsil öne çıkar.",
    ),
}

BASE_TOPIC_MINI_NOTES: Dict[str, Tuple[str, ...]] = {
    "Kelam / Akaid": (
        "Kader-kaza ve Maturidilik-Eşarilik ayrımını karıştırma.",
        "Büyük günah meselesinde Harici, Mürcie ve Ehl-i sünnet farkını birlikte tekrar et.",
    ),
    "Fıkıh": (
        "Farz-vacip, şart-rükün ve zekat-fitre ayrımlarını kısa kart yap.",
        "Kaza gerektirenle kefaret gerektiren oruç bozmalarını karşılaştırmalı çalış.",
    ),
    "Fıkıh Usulü": (
        "İcma-istihsan-istishab-örf dörtlüsünü örnek üzerinden ayır.",
        "Umum-husus ve mutlak-mukayyed kavramlarını lafız başlığında birlikte tekrar et.",
    ),
    "Tefsir": (
        "Mekki-Medeni, muhkem-müteşabih ve rivayet-dirayet ayrımlarını karıştırma.",
        "Nesih ile esbab-ı nüzul başlıklarını aynı tablo içinde tekrar etmek faydalıdır.",
    ),
    "Hadis": (
        "Sahih-hasen-zayıf ile mürsel-munkatı-muallak ayrımlarını aynı kartta çalış.",
        "Merfu, mevkuf ve maktu kavramlarını ravi zinciriyle birlikte düşün.",
    ),
    "Kur'an-ı Kerim ve Tecvid": (
        "İzhar-idgam-ihfa-iklab ve mahreç-sıfat ayrımını birlikte tekrar et.",
        "Vakf-ibtida ve med çeşitlerini örnekli çalışmak daha kalıcıdır.",
    ),
    "Siyer": (
        "Bedir-Uhud-Hendek ve Hudeybiye çizgisini kronolojiyle birlikte çalış.",
    ),
    "İslam Tarihi": (
        "Dört Halife ve Emevi-Abbasi geçişlerini zaman sırasıyla tekrar et.",
    ),
    "İslam Mezhepleri ve Akımları": (
        "Harici-Mürcie-Mutezile-Şia ayrımlarını tek tabloya dökmek çok işe yarar.",
    ),
    "Mezhepler Tarihi": (
        "Kurucu isim, temel görüş ve coğrafya üçlüsünü birlikte ezberle.",
    ),
    "Dinler Tarihi": (
        "Metin-mezhep-ibadet ayrımıyla çalışmak benzerlik aramaktan daha verimlidir.",
    ),
    "Din Eğitimi": (
        "Yöntem-teknik ile ölçme-değerlendirme araçlarını aynı başlık altında ezberleme; ayrı düşün.",
    ),
}

GLOBAL_MINI_NOTES: Tuple[str, ...] = (
    "Farz-vacip, şart-rükün, sahih-hasen, Mekki-Medeni, kader-kaza ayrımlarını kısa kart yap.",
    "Mürsel-munkatı, Maturidilik-Eşarilik ve zekat-fitre farkları hızlı tekrar listesinin başında olsun.",
    "Şahıs-eser-ekol eşleştirmeleri son turda değil, erken aşamada bitirilirse soru çözümü hızlanır.",
)

GLOBAL_STUDY_TACTICS: Tuple[str, ...] = (
    "Önce kavram eşleştirme.",
    "Sonra şahıs-eser-ekol listesi.",
    "Sonra kronoloji.",
    "En son çıkmış soru mantığı.",
)


def normalize_target_specs(targets: Iterable[Tuple[int, str]]) -> List[Tuple[int, str]]:
    normalized: List[Tuple[int, str]] = []
    seen = set()
    for year, subject in targets:
        try:
            year_value = int(year)
        except (TypeError, ValueError):
            continue
        subject_value = stable_subject_label(subject)
        if not subject_value:
            continue
        key = (year_value, subject_value)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(key)
    return normalized


def stable_subject_label(subject: object) -> str:
    raw_value = str(subject or "").replace("_", " ").strip()
    if not raw_value:
        return ""
    formatted = format_exam_subject_label(raw_value)
    formatted = re.sub(r"(?:\s*\(1-20\))+", " (1-20)", formatted)
    return re.sub(r"\s+", " ", formatted).strip()


def merge_targets(*target_groups: Iterable[Tuple[int, str]]) -> List[Tuple[int, str]]:
    merged: List[Tuple[int, str]] = []
    seen = set()
    for group in target_groups:
        for target in normalize_target_specs(group):
            if target in seen:
                continue
            seen.add(target)
            merged.append(target)
    return merged


def available_exam_targets(*, min_year: int = 2013) -> List[Tuple[int, str]]:
    targets: List[Tuple[int, str]] = []
    for _file_path, year, subject in iter_exam_files(WORDE_DIR):
        if int(year) < int(min_year):
            continue
        targets.append((int(year), stable_subject_label(subject)))
    return normalize_target_specs(targets)


def exam_family_for_subject(subject: str) -> str:
    subject_name = stable_subject_label(subject)
    if subject_name.startswith("DHBT"):
        return "DHBT"
    return SUBJECT_FAMILY_LABELS.get(subject_name, subject_name)


def exam_label(year: int, subject: str) -> str:
    return f"{year} {stable_subject_label(subject)}"


def normalize_spaces(text: object) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def build_topic_inference_text(question: Dict) -> str:
    options = question.get("siklar") or {}
    option_text = " ".join(normalize_spaces(value) for value in options.values())
    parts = [
        question.get("soru_metni", ""),
        option_text,
        question.get("dogru_cevap", ""),
    ]
    return normalize_spaces(" ".join(str(part or "") for part in parts))


def score_question_for_topic(question_text: str, topic_name: str) -> int:
    normalized_topic = normalize_topic_name(topic_name)
    groups = TOPIC_INFERENCE_GROUPS.get(normalized_topic, ())
    if not groups:
        return 0

    score = 0
    for _label, patterns in groups:
        hit_count = sum(
            1
            for pattern in patterns
            if re.search(pattern, question_text, flags=re.IGNORECASE)
        )
        if hit_count:
            score += 2 + min(2, hit_count - 1)
    return score


def infer_topic_from_question(question: Dict, exam_family: str) -> Tuple[str, int]:
    inference_text = build_topic_inference_text(question)
    candidate_scores = {}
    for topic_name in TOPIC_INFERENCE_GROUPS:
        topic_score = score_question_for_topic(inference_text, topic_name)
        if topic_score > 0:
            candidate_scores[topic_name] = topic_score

    if not candidate_scores:
        return "", 0

    sorted_candidates = sort_topics_for_exam_family(exam_family, candidate_scores)
    best_topic, best_score = sorted_candidates[0]
    return best_topic, int(best_score)


def resolve_topic_for_question(question: Dict, exam_family: str, year: int, subject: str) -> str:
    forced_topic = FORCED_TOPIC_OVERRIDES.get((int(year), stable_subject_label(subject), int(question.get("soru_no", 0))))
    if forced_topic:
        return normalize_topic_name(forced_topic) or forced_topic

    existing_topic = normalize_topic_name(question.get("konu", "")) or "Diğer"
    inferred_topic, inferred_score = infer_topic_from_question(question, exam_family)

    if existing_topic in {"", "Diğer"} and inferred_score > 0:
        return inferred_topic
    return existing_topic


def base_study_notes_for_topic(topic_name: str) -> List[str]:
    normalized_topic = normalize_topic_name(topic_name)
    return list(BASE_TOPIC_STUDY_NOTES.get(normalized_topic, ()))


def base_mini_notes_for_topic(topic_name: str) -> List[str]:
    normalized_topic = normalize_topic_name(topic_name)
    return list(BASE_TOPIC_MINI_NOTES.get(normalized_topic, ()))


def _looks_like_generic_answer(text: str) -> bool:
    cleaned = normalize_spaces(text)
    if not cleaned:
        return True
    if re.fullmatch(r"[IVXLCM,\sveyalnız]+", cleaned, flags=re.IGNORECASE):
        return True
    if len(cleaned.split()) > 5:
        return True
    generic_words = {"yalnız", "i", "ii", "iii", "iv", "v", "ve", "veya", "doğrudur", "yanlıştır"}
    lowered = cleaned.casefold()
    return lowered in generic_words


def extract_question_anchor_terms(question: Dict) -> List[str]:
    terms: List[str] = []
    for term in _extract_focus_references(question.get("soru_metni", "")):
        value = truncate_text(term, 40)
        if value and value not in terms:
            terms.append(value)

    answer_text = resolve_answer_text(question)
    if not _looks_like_generic_answer(answer_text):
        candidate = truncate_text(answer_text, 40)
        if candidate and candidate not in terms:
            terms.append(candidate)
    return terms[:4]


def build_topic_exam_focus_lines(
    topic_name: str,
    questions: Sequence[Dict],
    subtopic_items: Sequence[Tuple[str, int]],
    style_items: Sequence[Tuple[str, int]],
) -> List[str]:
    lines = [
        f"Bu sınavda en çok {format_counter_text(subtopic_items, limit=3, empty_label='genel tekrar')} çizgisi öne çıktı.",
        f"Soru kalıbında {format_counter_text(style_items, limit=2, empty_label='karma yapı')} ağır bastı.",
    ]

    anchor_counter: Counter[str] = Counter()
    for question in questions:
        for term in extract_question_anchor_terms(question):
            anchor_counter[term] += 1

    anchor_items = ranked_counter_items(anchor_counter)
    if anchor_items:
        lines.append(f"Geçen isim/kavramlar: {format_counter_text(anchor_items, limit=4)}.")
    return lines


def build_topic_quick_route_line(
    topic_name: str,
    question_count: int,
    subtopic_items: Sequence[Tuple[str, int]],
) -> str:
    focus_text = format_counter_text(subtopic_items, limit=2, empty_label="genel tekrar")
    return f"{topic_name}: {focus_text}. ({question_count} soru)"


def build_exam_mini_notes(topic_names: Sequence[str]) -> List[str]:
    notes: List[str] = []
    seen = set()
    for topic_name in topic_names:
        for note in base_mini_notes_for_topic(topic_name):
            if note not in seen:
                seen.add(note)
                notes.append(note)
    for note in GLOBAL_MINI_NOTES:
        if note not in seen:
            notes.append(note)
    return notes[:6]


def truncate_text(text: str, max_chars: int = 92) -> str:
    cleaned = normalize_spaces(text)
    if len(cleaned) <= max_chars:
        return cleaned
    shortened = cleaned[: max_chars - 3].rstrip()
    if " " in shortened:
        shortened = shortened.rsplit(" ", 1)[0]
    return shortened.rstrip(",;:") + "..."


def join_human_list(items: Sequence[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} ve {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])} ve {cleaned[-1]}"


def format_counter_text(
    items: Sequence[Tuple[str, int]],
    *,
    limit: int = 3,
    empty_label: str = "Yeterli veri yok",
) -> str:
    rows = [f"{name} ({count})" for name, count in list(items)[:limit] if str(name).strip()]
    return ", ".join(rows) if rows else empty_label


def sort_style_counts(counter: Counter[str]) -> List[Tuple[str, int]]:
    style_index = {label: index for index, label in enumerate(STYLE_ORDER)}
    return sorted(
        counter.items(),
        key=lambda item: (-item[1], style_index.get(item[0], len(style_index) + 99), item[0]),
    )


def ranked_counter_items(
    counter: Counter[str],
    *,
    fallback_label: str | None = None,
) -> List[Tuple[str, int]]:
    items = [(name, count) for name, count in counter.items() if str(name).strip()]
    if fallback_label and len(items) > 1:
        items = [(name, count) for name, count in items if name != fallback_label] or items
    return sorted(items, key=lambda item: (-item[1], item[0]))


def _latin_ratio(text: str) -> float:
    letters = [char for char in str(text or "") if char.isalpha()]
    if not letters:
        return 0.0
    latin_letters = 0
    for char in letters:
        if "LATIN" in unicodedata.name(char, ""):
            latin_letters += 1
    return latin_letters / len(letters)


def _clean_segment(text: str) -> str:
    value = normalize_spaces(text).strip(" -:;,.")
    value = value.strip('"').strip("'")
    return value


def _iter_text_segments(question_text: str) -> List[str]:
    raw_lines = [normalize_spaces(line) for line in str(question_text or "").splitlines()]
    segments: List[str] = []
    for line in raw_lines:
        if not line:
            continue
        parts = re.split(r"(?<=[.!?])\s+", line)
        for part in parts:
            cleaned = _clean_segment(part)
            if cleaned:
                segments.append(cleaned)
    return segments


def _is_generic_segment(segment: str) -> bool:
    if not segment:
        return True
    if any(re.fullmatch(pattern, segment, flags=re.IGNORECASE) for pattern in GENERIC_LINE_PATTERNS):
        return True
    if segment.endswith(":") and len(segment.split()) <= 4:
        return True
    if _latin_ratio(segment) < 0.55:
        return True
    if re.fullmatch(r"[\W\d_]+", segment):
        return True
    return False


def _extract_focus_references(question_text: str) -> List[str]:
    text = str(question_text or "")
    references: List[str] = []

    patterns = (
        r"[\"“](.{2,40}?)[\"”]",
        r"\b([A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’-]+(?:\s+[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’-]+){0,2})\s*,\s*\d+:\d+(?:-\d+)?",
        r"\b([A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’-]+(?:\s+[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’-]+){0,2}\s+Suresi)\b",
        r"\b(Hz\.\s*[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’-]+(?:\s+[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’-]+){0,2})\b",
        r"\b(İbn\s+[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’-]+(?:\s+[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’-]+){0,2})\b",
    )

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = truncate_text(_clean_segment(match.group(1)), 48)
            if value and value not in references:
                references.append(value)
            if len(references) >= 4:
                return references
    return references


def classify_question_style(question_text: str) -> str:
    text = normalize_spaces(question_text).casefold()
    for label, patterns in QUESTION_STYLE_PATTERNS:
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            return label
    return "Genel bilgi"


def build_focus_label(question_text: str) -> str:
    references = _extract_focus_references(question_text)
    if references:
        return truncate_text(join_human_list(references[:2]), 84)

    segments = _iter_text_segments(question_text)
    question_like = [
        segment
        for segment in segments
        if not _is_generic_segment(segment)
        and re.search(
            r"hangi|hangileri|hangisidir|yer almaz|söylenebilir|söylenemez|ifade edilir|adlandırılır|örnek",
            segment,
            flags=re.IGNORECASE,
        )
    ]
    if question_like:
        return truncate_text(question_like[-1].rstrip("?"), 84)

    for segment in segments:
        if not _is_generic_segment(segment):
            return truncate_text(segment.rstrip("?"), 84)
    return "Ana odak"


def resolve_answer_text(question: Dict) -> str:
    correct_answer = str(question.get("dogru_cevap", "") or "").strip()
    options = question.get("siklar") or {}
    if correct_answer in options:
        return normalize_spaces(options[correct_answer])
    if correct_answer and correct_answer[:1] in options:
        return normalize_spaces(options[correct_answer[:1]])
    return normalize_spaces(correct_answer) or "Cevap bilgisi yok"


def question_relation_label(style: str) -> str:
    relations = {
        "Kavram / eşleştirme": "ana cevap",
        "İstisna / ters kök": "dışarıda kalan",
        "Doğru kombinasyon": "doğru kombinasyon",
        "Örnek / uygulama": "doğru örnek",
        "Yorum / çıkarım": "çıkarım",
        "Genel bilgi": "cevap",
    }
    return relations.get(style, "cevap")


def build_question_hap_line(question: Dict) -> str:
    style = classify_question_style(question.get("soru_metni", ""))
    focus = build_focus_label(question.get("soru_metni", ""))
    answer = truncate_text(resolve_answer_text(question), 110)
    relation = question_relation_label(style)
    question_no = question.get("soru_no", "?")
    return f"- Soru {question_no} | {focus}: {relation} -> {answer}."


def build_topic_short_panel(
    subtopic_items: Sequence[Tuple[str, int]],
    style_items: Sequence[Tuple[str, int]],
) -> str:
    focus_text = format_counter_text(subtopic_items, limit=2, empty_label="genel tekrar")
    return f"{focus_text}"


def build_topic_summary_lines(
    topic_name: str,
    subtopic_items: Sequence[Tuple[str, int]],
    style_items: Sequence[Tuple[str, int]],
    question_count: int,
) -> List[str]:
    focus_names = [name for name, _ in list(subtopic_items)[:2]]
    lines = [
        f"Bu sınavda öne çıkan çizgi: {format_counter_text(subtopic_items, limit=3, empty_label='genel tekrar')}.",
        f"Soru kalıbı ağırlığı: {format_counter_text(style_items, limit=2, empty_label='karma yapı')}.",
    ]
    if focus_names:
        lines.append(f"Hızlı tekrar sırası: {join_human_list(focus_names)}.")
    return lines


def build_exam_overview_lines(
    topic_items: Sequence[Tuple[str, int]],
    subtopic_items: Sequence[Tuple[str, int]],
    style_items: Sequence[Tuple[str, int]],
    total_questions: int,
) -> List[str]:
    top_topics = list(topic_items)[:3]
    overview = [
        f"Önce {format_counter_text(top_topics, limit=3)} çalışılırsa ana gövde hızlı toparlanır.",
        f"Bu sınavda sık dönen alt başlıklar: {format_counter_text(subtopic_items, limit=4)}.",
        f"Soru kalıbı dağılımı: {format_counter_text(style_items, limit=4)}.",
    ]
    if top_topics and total_questions:
        top_total = sum(count for _, count in top_topics)
        ratio = round((top_total / total_questions) * 100)
        overview.append(f"İlk üç konu yaklaşık %{ratio}'lik alanı kapsıyor.")
    return overview


def build_topic_entry(topic_name: str, questions: Sequence[Dict], exam_family: str) -> Dict[str, object]:
    ordered_questions = sorted(questions, key=lambda item: int(item.get("soru_no", 0)))
    subtopic_counter: Counter[str] = Counter()
    style_counter: Counter[str] = Counter()
    for question in ordered_questions:
        subtopics = question.get("alt_basliklar") or extract_subtopics(question.get("soru_metni", ""), topic_name)
        for subtopic in subtopics:
            subtopic_counter[str(subtopic).strip() or "Genel / Diğer"] += 1
        style_counter[classify_question_style(question.get("soru_metni", ""))] += 1

    ranked_subtopics = ranked_counter_items(subtopic_counter, fallback_label="Genel / Diğer")
    ranked_styles = sort_style_counts(style_counter)
    question_facts = [build_question_hap_line(question) for question in ordered_questions]
    exam_focus_lines = build_topic_exam_focus_lines(
        topic_name,
        ordered_questions,
        ranked_subtopics,
        ranked_styles,
    )
    study_bullets = base_study_notes_for_topic(topic_name)
    mini_notes = base_mini_notes_for_topic(topic_name)

    return {
        "topic": topic_name,
        "question_count": len(ordered_questions),
        "subtopics": [{"name": name, "count": count} for name, count in ranked_subtopics],
        "styles": [{"name": name, "count": count} for name, count in ranked_styles],
        "summary_lines": build_topic_summary_lines(
            topic_name,
            ranked_subtopics,
            ranked_styles,
            len(ordered_questions),
        ),
        "short_panel": build_topic_short_panel(ranked_subtopics, ranked_styles),
        "quick_route_line": build_topic_quick_route_line(topic_name, len(ordered_questions), ranked_subtopics),
        "exam_focus_lines": exam_focus_lines,
        "study_bullets": study_bullets,
        "mini_notes": mini_notes,
        "question_facts": question_facts,
    }


def build_exam_entry(year: int, subject: str, questions: Sequence[Dict]) -> Dict[str, object]:
    family_label = exam_family_for_subject(subject)
    ordered_questions = sorted(
        questions,
        key=lambda item: (
            normalize_topic_name(item.get("konu", "")),
            int(item.get("soru_no", 0)),
        ),
    )

    topic_groups: Dict[str, List[Dict]] = defaultdict(list)
    topic_counter: Counter[str] = Counter()
    subtopic_counter: Counter[str] = Counter()
    style_counter: Counter[str] = Counter()
    for question in ordered_questions:
        topic_name = normalize_topic_name(question.get("konu", "")) or "Diğer"
        question["konu"] = topic_name
        topic_groups[topic_name].append(question)
        topic_counter[topic_name] += 1
        for subtopic in question.get("alt_basliklar") or extract_subtopics(question.get("soru_metni", ""), topic_name):
            subtopic_counter[str(subtopic).strip() or "Genel / Diğer"] += 1
        style_counter[classify_question_style(question.get("soru_metni", ""))] += 1

    ordered_topics = sort_topics_for_exam_family(family_label, topic_counter)
    topic_entries = [
        build_topic_entry(topic_name, topic_groups.get(topic_name, []), family_label)
        for topic_name, _ in ordered_topics
    ]

    ranked_subtopics = ranked_counter_items(subtopic_counter, fallback_label="Genel / Diğer")
    ranked_styles = sort_style_counts(style_counter)
    topic_names = [topic_name for topic_name, _ in ordered_topics]

    return {
        "id": f"{year}_{subject}",
        "year": year,
        "subject": subject,
        "label": exam_label(year, subject),
        "family_label": family_label,
        "question_count": len(ordered_questions),
        "topic_count": len(topic_entries),
        "overview_lines": build_exam_overview_lines(
            ordered_topics,
            ranked_subtopics,
            ranked_styles,
            len(ordered_questions),
        ),
        "mini_notes": build_exam_mini_notes(topic_names),
        "study_tactics": list(GLOBAL_STUDY_TACTICS),
        "topic_counts": [{"name": name, "count": count} for name, count in ordered_topics],
        "subtopics": [{"name": name, "count": count} for name, count in ranked_subtopics],
        "styles": [{"name": name, "count": count} for name, count in ranked_styles],
        "topics": topic_entries,
    }


def render_exam_text(exam_entry: Dict[str, object]) -> str:
    lines = [
        f"{exam_entry['label']} HAP BİLGİ PANELİ",
        f"Sınav ailesi: {exam_entry['family_label']}",
        f"Toplam soru: {exam_entry['question_count']}",
        f"Konu sayısı: {exam_entry['topic_count']}",
        "",
        "Bu sınav için kısa rota:",
    ]
    for line in exam_entry.get("overview_lines", []):
        lines.append(f"- {line}")

    lines.extend(
        [
            "",
            "Konu konu hızlı hat:",
        ]
    )
    for topic_entry in exam_entry.get("topics", []):
        lines.append(f"- {topic_entry.get('quick_route_line', '')}")

    mini_notes = list(exam_entry.get("mini_notes", []))
    if mini_notes:
        lines.extend(["", "En çok karıştırılan mini notlar:"])
        for note in mini_notes:
            lines.append(f"- {note}")

    tactics = list(exam_entry.get("study_tactics", []))
    if tactics:
        lines.extend(["", "Çalışma taktiği:"])
        for tactic in tactics:
            lines.append(f"- {tactic}")

    return "\n".join(lines).strip() + "\n"


def render_topic_text(exam_entry: Dict[str, object], topic_entry: Dict[str, object]) -> str:
    lines = [
        f"{exam_entry['label']} / {topic_entry['topic']}",
        f"Soru sayısı: {topic_entry['question_count']}",
        "",
        "Bu sınavda öne çıkanlar:",
    ]

    for line in topic_entry.get("exam_focus_lines", []):
        lines.append(f"- {line}")

    study_bullets = list(topic_entry.get("study_bullets", []))
    if study_bullets:
        lines.extend(["", "Hap bilgiler:"])
        for bullet in study_bullets:
            lines.append(f"- {bullet}")

    mini_notes = list(topic_entry.get("mini_notes", []))
    if mini_notes:
        lines.extend(["", "Mini notlar:"])
        for note in mini_notes:
            lines.append(f"- {note}")
    return "\n".join(lines).strip() + "\n"


def load_hap_bilgi_index(output_dir: Path = HAP_BILGI_DIR) -> Dict[str, object] | None:
    index_path = output_dir / "index.json"
    if not index_path.exists():
        return None
    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def targets_from_index(index_data: Dict[str, object] | None) -> List[Tuple[int, str]]:
    if not isinstance(index_data, dict):
        return []
    targets = []
    for item in index_data.get("targets", []):
        if not isinstance(item, dict):
            continue
        targets.append((item.get("year"), item.get("subject")))
    return normalize_target_specs(targets)


def _is_bundle_current(index_data: Dict[str, object] | None) -> bool:
    if not isinstance(index_data, dict):
        return False

    indexed_targets = set(targets_from_index(index_data))
    current_targets = set(available_exam_targets())
    if indexed_targets != current_targets:
        return False

    source_files = index_data.get("source_files") or []
    if not source_files:
        return False

    for source in source_files:
        try:
            path = Path(source.get("path", ""))
            expected_mtime = int(source.get("mtime_ns", -1))
        except Exception:
            return False
        if not path.exists():
            return False
        try:
            if path.stat().st_mtime_ns != expected_mtime:
                return False
        except OSError:
            return False

    for exam_entry in index_data.get("exams", []):
        general_path = Path(str(exam_entry.get("general_path", "")))
        if not general_path.exists():
            return False
        for topic_entry in exam_entry.get("topics", []):
            topic_path = Path(str(topic_entry.get("text_path", "")))
            if not topic_path.exists():
                return False
    return True


def build_hap_bilgi_bundle(targets: Iterable[Tuple[int, str]]) -> Dict[str, object]:
    normalized_targets = normalize_target_specs(targets)
    target_set = set(normalized_targets)
    source_records: List[Dict[str, object]] = []
    grouped_questions: Dict[Tuple[int, str], List[Dict]] = defaultdict(list)

    for file_path, year, subject in iter_exam_files(WORDE_DIR):
        target_key = (int(year), stable_subject_label(subject))
        if target_key not in target_set:
            continue

        parsed_questions = parse_questions_from_file(
            file_path,
            int(year),
            subject,
            base_dir=WORDE_DIR,
            default_topic="Diğer",
        )
        family_label = exam_family_for_subject(subject)
        for question in parsed_questions:
            topic_name = resolve_topic_for_question(question, family_label, int(year), subject)
            question["konu"] = topic_name
            question["sinav_aile"] = family_label
            question["alt_basliklar"] = extract_subtopics(question.get("soru_metni", ""), topic_name)
        grouped_questions[target_key].extend(parsed_questions)
        source_records.append(
            {
                "year": int(year),
                "subject": stable_subject_label(subject),
                "path": str(file_path.resolve()),
                "mtime_ns": file_path.stat().st_mtime_ns,
            }
        )

    warnings = []
    available_keys = set(grouped_questions.keys())
    for target in normalized_targets:
        if target not in available_keys:
            warnings.append(f"Kaynak dosya bulunamadı veya soru yüklenemedi: {target[0]} {target[1]}")

    exam_entries = [
        build_exam_entry(year, subject, grouped_questions[(year, subject)])
        for year, subject in normalized_targets
        if grouped_questions.get((year, subject))
    ]

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "targets": [{"year": year, "subject": subject} for year, subject in normalized_targets],
        "source_files": source_records,
        "warnings": warnings,
        "exams": exam_entries,
    }


def write_hap_bilgi_bundle(
    bundle: Dict[str, object],
    output_dir: Path = HAP_BILGI_DIR,
) -> Dict[str, object]:
    ensure_directory(output_dir)
    bundle_copy = json.loads(json.dumps(bundle, ensure_ascii=False))

    for exam_entry in bundle_copy.get("exams", []):
        subject_dir_name = re.sub(r'[<>:"/\\|?*]+', "_", str(exam_entry.get("subject", "")).strip()) or "Diger"
        exam_dir = ensure_directory(output_dir / subject_dir_name / str(exam_entry.get("year")))

        general_path = exam_dir / "genel_paneli.txt"
        general_path.write_text(render_exam_text(exam_entry), encoding="utf-8")
        exam_entry["general_path"] = str(general_path.resolve())

        for topic_entry in exam_entry.get("topics", []):
            topic_path = exam_dir / f"{sanitize_topic_for_filename(topic_entry.get('topic', 'konu'))}.txt"
            topic_path.write_text(render_topic_text(exam_entry, topic_entry), encoding="utf-8")
            topic_entry["text_path"] = str(topic_path.resolve())

    index_path = output_dir / "index.json"
    index_path.write_text(json.dumps(bundle_copy, ensure_ascii=False, indent=2), encoding="utf-8")
    return bundle_copy


def generate_hap_bilgileri(
    targets: Iterable[Tuple[int, str]],
    *,
    output_dir: Path = HAP_BILGI_DIR,
) -> Dict[str, object]:
    bundle = build_hap_bilgi_bundle(targets)
    return write_hap_bilgi_bundle(bundle, output_dir=output_dir)


def ensure_hap_bilgi_data(
    *,
    output_dir: Path = HAP_BILGI_DIR,
    default_targets: Sequence[Tuple[int, str]] | None = None,
) -> Dict[str, object]:
    current_index = load_hap_bilgi_index(output_dir=output_dir)
    if _is_bundle_current(current_index):
        return current_index

    preferred_targets = normalize_target_specs(default_targets or available_exam_targets())
    indexed_targets = targets_from_index(current_index)
    if set(indexed_targets) == set(preferred_targets) and indexed_targets:
        targets = indexed_targets
    else:
        targets = preferred_targets
    return generate_hap_bilgileri(targets, output_dir=output_dir)


def parse_exam_spec(value: str) -> Tuple[int, str]:
    raw_value = str(value or "").strip()
    if ":" not in raw_value:
        raise ValueError("Sınav biçimi YYYY:DERS olmalı. Örnek: 2025:DKAB")
    year_text, subject_text = raw_value.split(":", 1)
    year_value = int(year_text.strip())
    subject_value = stable_subject_label(subject_text.strip())
    if not subject_value:
        raise ValueError("Ders adı boş olamaz.")
    return year_value, subject_value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seçili sınavlar için yıl ve konu bazlı hap bilgi metinleri üretir."
    )
    parser.add_argument(
        "--exam",
        action="append",
        default=[],
        help="Hedef sınav. Biçim: YYYY:DERS, örnek 2026:MBSTS",
    )
    parser.add_argument(
        "--append-existing",
        action="store_true",
        help="Mevcut hap bilgi hedeflerine yeni sınavları ekleyerek yeniden üretir.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="2013 ve sonrası mevcut tüm sınav dosyaları için üretim yapar.",
    )
    args = parser.parse_args()

    if args.all:
        selected_targets = available_exam_targets()
    elif args.exam:
        selected_targets = [parse_exam_spec(value) for value in args.exam]
    else:
        selected_targets = available_exam_targets()
    if args.append_existing:
        selected_targets = merge_targets(targets_from_index(load_hap_bilgi_index()), selected_targets)
    else:
        selected_targets = normalize_target_specs(selected_targets)

    result = generate_hap_bilgileri(selected_targets, output_dir=HAP_BILGI_DIR)

    print("Hap bilgi üretimi tamamlandı.")
    print(f"Hedef sınav sayısı: {len(result.get('targets', []))}")
    print(f"Oluşturulan sınav paneli: {len(result.get('exams', []))}")
    print(f"Çıktı klasörü: {HAP_BILGI_DIR}")
    warnings = result.get("warnings") or []
    if warnings:
        print("Uyarılar:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
