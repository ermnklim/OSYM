import os, re

base_path = r'C:\Users\osman\Desktop\OSYM\Worde_Yapistir'

all_qs = []
for file in os.listdir(base_path):
    m = re.search(r'(\d{4})_(.+)_Sorulari\.txt', file)
    if not m: continue
    
    y = int(m.group(1))
    d = m.group(2)
    with open(os.path.join(base_path, file), 'r', encoding='utf-8') as f:
        blocks = f.read().split('---SONRAKİ SORU---')
    
    for b in blocks:
        lines = b.strip().split('\n')
        if not lines or not lines[0]: continue
        
        no = '?'
        m_no = re.search(r'Soru\s+(\d+)', b)
        if m_no: no = m_no.group(1)
        
        m_k = re.search(r'KONU:\s*(.+)', b)
        k = m_k.group(1).strip() if m_k else ''
        
        text = []
        for l in lines:
            l = l.strip()
            if not l or re.match(r'^(DERS:|KONU:|YIL:|Soru\s+\d+|Doğru Cevap:|A\)|B\)|C\)|D\)|E\)|Görsel Notu:|Dosya:|Konum:)', l):
                continue
            text.append(l)
        
        if text:
            full_text = ' '.join(text).lower()
            full_text = re.sub(r'[^\w\s]', '', full_text)  # remove punctuation
            words = set(full_text.split())
            if words:
                all_qs.append({'y': y, 'd': d, 'no': no, 'k': k, 'words': words, 'raw': ' '.join(text)[:60]})

print(f"Total questions: {len(all_qs)}")

similar = []
for i in range(len(all_qs)):
    for j in range(i+1, len(all_qs)):
        w1, w2 = all_qs[i]['words'], all_qs[j]['words']
        inter = len(w1.intersection(w2))
        union = len(w1.union(w2))
        sim = inter / union if union else 0
        if sim > 0.65:
            similar.append((sim, all_qs[i], all_qs[j]))

similar.sort(key=lambda x: x[0], reverse=True)
print("Top similar questions:")
# remove duplicates (where same text appears multiple times)
seen = set()
count = 0
for sim, q1, q2 in similar:
    pair_id = tuple(sorted([f"{q1['y']}{q1['d']}{q1['no']}", f"{q2['y']}{q2['d']}{q2['no']}"]))
    if pair_id in seen: continue
    seen.add(pair_id)
    
    print(f"\n{sim:.2f} | {q1['y']} {q1['d']} S:{q1['no']} ({q1['k']}) -- {q2['y']} {q2['d']} S:{q2['no']} ({q2['k']})")
    print(f"Q1: {q1['raw']}...")
    print(f"Q2: {q2['raw']}...")
    
    count += 1
    if count >= 10: break
