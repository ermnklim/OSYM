#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DKAB ÖABT Sınav Analiz Aracı
Yıllara ve konulara göre soru dağılımı analizi
Otomatik güncellenir - yeni sınav eklendiğinde bildirim yapar
"""

import os
import re
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple
import json

ANALYSIS_FILE = os.path.join(os.path.dirname(__file__), "analiz_sonuc.txt")
ANALYSIS_JSON = os.path.join(os.path.dirname(__file__), "analiz_data.json")
LAST_CHECK_FILE = os.path.join(os.path.dirname(__file__), "last_check.json")

EXAM_DIR = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir"

KONULAR = [
    "Kur'an-ı Kerim ve Tecvid",
    "Tefsir",
    "Hadis",
    "Fıkıh",
    "Kelam / Akaid",
    "İslam Mezhepleri ve Akımları",
    "İslam Tarihi / Siyer",
    "İslam Kültür ve Medeniyeti",
    "İslam Felsefesi",
    "Din Felsefesi",
    "Din Sosyolojisi",
    "Din Psikolojisi",
    "Din Eğitimi",
    "Dinler Tarihi"
]

def get_file_mod_time(file_path):
    try:
        return os.path.getmtime(file_path)
    except:
        return 0

def get_last_check():
    try:
        if os.path.exists(LAST_CHECK_FILE):
            with open(LAST_CHECK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"files": {}, "last_run": ""}

def save_last_check(data):
    try:
        with open(LAST_CHECK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def check_new_files():
    """Yeni eklenen dosyaları kontrol eder"""
    last_check = get_last_check()
    current_files = {}
    new_files = []
    
    if os.path.exists(EXAM_DIR):
        for filename in os.listdir(EXAM_DIR):
            match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
            if match:
                file_path = os.path.join(EXAM_DIR, filename)
                mod_time = get_file_mod_time(file_path)
                current_files[filename] = mod_time
                
                if filename not in last_check.get("files", {}):
                    new_files.append(filename)
                elif last_check["files"].get(filename, 0) != mod_time:
                    new_files.append(f"{filename} (güncellendi)")
    
    last_check["files"] = current_files
    last_check["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_last_check(last_check)
    
    return new_files

def parse_questions_from_file(file_path: str, year: int, subject: str = "DKAB") -> List[Dict]:
    """Dosyadan soruları parse eder"""
    questions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = content.replace('---SONRAKİ SORU---', '---SONRAKI SORU---')
        content = content.replace('---SONRAKÄ° SORU---', '---SONRAKI SORU---')
        soru_blocks = content.split('---SONRAKI SORU---')
        
        for block in soru_blocks:
            if 'Soru ' in block and ('Doğru Cevap:' in block or 'Dogru Cevap:' in block or 'DoÄŸru Cevap:' in block):
                question = parse_single_question(block, year, subject)
                if question:
                    questions.append(question)
                    
    except Exception as e:
        print(f"Parse hatası {year}: {e}")
        
    return questions

def parse_single_question(text: str, year: int, subject: str = "DKAB") -> Dict:
    """Tek soruyu parse eder"""
    try:
        lines = text.strip().split('\n')
        
        soru_no = None
        soru_metni = []
        konu = ""
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Soru ') and ':' in line:
                soru_no_str = line.split()[1].replace(':', '')
                try:
                    soru_no = int(soru_no_str)
                except ValueError:
                    soru_no = None
            elif line.startswith('KONU:'):
                konu = line.split(':', 1)[1].strip()
            elif soru_no and not any(line.startswith(x) for x in ['A)', 'B)', 'C)', 'D)', 'E)', 'Doğru', 'Dogru', 'Açıklama', 'Aciklama', '[RESIM', 'Görsel', 'Gorsel']):
                soru_metni.append(line)
        
        if soru_no:
            return {
                "yil": year,
                "ders": subject,
                "konu": konu if konu else "Diğer",
                "soru_no": soru_no
            }
    except:
        pass
    return None

def analyze_all_exams():
    """Tüm sınavları analiz eder"""
    all_questions = []
    years_data = defaultdict(lambda: defaultdict(int))
    konu_data = defaultdict(lambda: defaultdict(int))
    
    if os.path.exists(EXAM_DIR):
        for filename in os.listdir(EXAM_DIR):
            match = re.search(r"(\d{4})_(.+)_Sorulari\.txt", filename)
            if match:
                year = int(match.group(1))
                subject = match.group(2)
                file_path = os.path.join(EXAM_DIR, filename)
                questions = parse_questions_from_file(file_path, year, subject)
                all_questions.extend(questions)
                
                for q in questions:
                    years_data[q['yil']][q['ders']] += 1
                    konu_data[q['konu']][q['ders']] += 1
    
    return all_questions, years_data, konu_data

def generate_analysis_text():
    """Analiz metnini oluşturur"""
    questions, years_data, konu_data = analyze_all_exams()
    new_files = check_new_files()
    
    total = len(questions)
    dkab_total = sum(v["DKAB"] for v in years_data.values())
    ihl_total = sum(v["IHL"] for v in years_data.values())
    
    text = []
    text.append("=" * 70)
    text.append("DKAB ÖABT SORU ANALİZ RAPORU")
    text.append(f"Oluşturulma: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    text.append("=" * 70)
    
    if new_files:
        text.append("")
        text.append("🔔 YENİ EKLENEN DOSYALAR:")
        for f in new_files:
            text.append(f"   • {f}")
        text.append("")
    
    text.append("")
    text.append("📊 GENEL İSTATİSTİKLER")
    text.append("-" * 50)
    text.append(f"Toplam Soru Sayısı: {total}")
    text.append(f"  - DKAB: {dkab_total} soru")
    text.append(f"  - IHL:  {ihl_total} soru")
    text.append("")
    
    text.append("📅 YILLARA GÖRE DAĞILIM")
    text.append("-" * 50)
    text.append(f"{'Yıl':<8} {'DKAB':<10} {'IHL':<10} {'Toplam':<10}")
    text.append("-" * 50)
    
    sorted_years = sorted(years_data.keys(), reverse=True)
    for year in sorted_years:
        dkab = years_data[year]["DKAB"]
        ihl = years_data[year]["IHL"]
        text.append(f"{year:<8} {dkab:<10} {ihl:<10} {dkab+ihl:<10}")
    
    text.append("-" * 50)
    text.append("")
    
    text.append("📚 KONULARA GÖRE DAĞILIM (GENEL)")
    text.append("-" * 50)
    text.append(f"{'Konu':<35} {'DKAB':<8} {'IHL':<8} {'Toplam':<8}")
    text.append("-" * 50)
    
    konu_totals = {}
    for konu in konu_data:
        dkab = konu_data[konu]["DKAB"]
        ihl = konu_data[konu]["IHL"]
        konu_totals[konu] = dkab + ihl
    
    sorted_konular = sorted(konu_totals.items(), key=lambda x: x[1], reverse=True)
    
    for konu, total_konu in sorted_konular:
        dkab = konu_data[konu]["DKAB"]
        ihl = konu_data[konu]["IHL"]
        text.append(f"{konu:<35} {dkab:<8} {ihl:<8} {total_konu:<8}")
    
    text.append("-" * 50)
    text.append("")
    
    # Bilinmeyen konu soruları
    unknown_questions = [(q['yil'], q['ders'], q['soru_no']) for q in questions if q.get('konu') in ['BİLİNMEYEN KONU', '', None] or not q.get('konu')]
    if unknown_questions:
        text.append("⚠️ BİLİNMEYEN KONU SORULARI")
        text.append("-" * 50)
        text.append("Bu soruların KONU etiketi bulunamadı:")
        for yil, ders, no in unknown_questions:
            text.append(f"  • {yil} {ders} - Soru {no}")
        text.append("-" * 50)
        text.append("")
    
    text.append("📋 YIL × DERS × KONU DAĞILIMI")
    text.append("-" * 70)
    
    yil_ders_konu = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for q in questions:
        if q.get('konu') and q.get('konu') not in ['BİLİNMEYEN KONU', '']:
            yil_ders_konu[q['yil']][q['ders']][q['konu']] += 1
    
    sorted_yil_ders_konu_years = sorted(yil_ders_konu.keys(), reverse=True)
    all_ders = sorted(set(d for y in sorted_yil_ders_konu_years for d in yil_ders_konu[y].keys()))
    all_konular = sorted(set(k for y in sorted_yil_ders_konu_years for d in all_ders for k in yil_ders_konu[y][d].keys()))
    
    for year in sorted_yil_ders_konu_years:
        text.append(f"\n{year}:")
        for ders in all_ders:
            konular_str = ", ".join([f"{k}: {yil_ders_konu[year][ders].get(k, 0)}" for k in all_konular])
            text.append(f"  {ders}: {konular_str}")
    
    text.append("")
    text.append("=" * 70)
    text.append("")
    
    text.append("📋 YIL × KONU MATRİSİ (DKAB)")
    text.append("-" * 70)
    
    dkab_konular = set()
    dkab_years = sorted(set(y for y in years_data.keys() if years_data[y]["DKAB"] > 0), reverse=True)
    for konu in konu_data:
        if konu_data[konu]["DKAB"] > 0:
            dkab_konular.add(konu)
    
    header = f"{'Konu':<30}"
    for year in dkab_years:
        header += f" {year:<8}"
    text.append(header)
    text.append("-" * 70)
    
    for konu in sorted_konular:
        if isinstance(konu, tuple):
            konu_name = konu[0]
        else:
            konu_name = konu
        
        row = f"{konu_name[:28]:<30}"
        for year in dkab_years:
            count = 0
            for q in questions:
                if q['yil'] == year and q['konu'] == konu_name and q['ders'] == 'DKAB':
                    count += 1
            row += f" {count:<8}"
        text.append(row)
    
    text.append("-" * 70)
    text.append("")
    
    text.append("📋 YIL × KONU MATRİSİ (IHL)")
    text.append("-" * 70)
    
    ihl_years = sorted(set(y for y in years_data.keys() if years_data[y]["IHL"] > 0), reverse=True)
    if ihl_years:
        header = f"{'Konu':<30}"
        for year in ihl_years:
            header += f" {year:<8}"
        text.append(header)
        text.append("-" * 70)
        
        for konu in sorted_konular:
            if isinstance(konu, tuple):
                konu_name = konu[0]
            else:
                konu_name = konu
            
            row = f"{konu_name[:28]:<30}"
            for year in ihl_years:
                count = 0
                for q in questions:
                    if q['yil'] == year and q['konu'] == konu_name and q['ders'] == 'IHL':
                        count += 1
                row += f" {count:<8}"
            text.append(row)
    else:
        text.append("IHL verisi bulunamadı.")
    
    text.append("-" * 70)
    text.append("")
    
    text.append("=" * 70)
    text.append("Analiz tamamlandı.")
    text.append("=" * 70)
    
    return "\n".join(text), new_files

def save_analysis():
    """Analiz sonucunu dosyaya kaydeder"""
    text, new_files = generate_analysis_text()
    
    with open(ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        f.write(text)
    
    data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "new_files": new_files,
        "total_questions": len([q for q in analyze_all_exams()[0]])
    }
    with open(ANALYSIS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return text, new_files

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("DKAB Analiz araci calisiyor...\n")
    result, new_files = save_analysis()
    print(result)
    
    if new_files:
        print("\n[YENI DOSYALAR TESPIT EDILDI]")
        for f in new_files:
            print(f"   - {f}")
