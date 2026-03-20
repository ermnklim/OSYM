import re

with open('Worde_Yapistir/2021_IHL_Sorulari.txt', 'r', encoding='utf-8') as f:
    text = f.read()

parts = text.split('\nSoru 27:\n')
if len(parts) == 2:
    part1 = parts[0]
    part2 = '\nSoru 27:\n' + parts[1]
    
    def replacer(m):
        num = int(m.group(1))
        return f'\nSoru {num+1}:\n'
        
    part2_renumbered = re.sub(r'\nSoru (\d+):\n', replacer, part2)
    
    new_question = """
Soru 27:
KONU: Kelam / Akaid
Günümüzde ezanın "eşhedü enne aliyyen veliyyullah" ifadesi eklenerek okunduğu ülke aşağıdakilerden hangisidir?

A) İran
B) Ürdün
C) Umman
D) Katar
E) Cezayir

Doğru Cevap: A

---SONRAKI SORU---
"""
    final_text = part1 + new_question + part2_renumbered
    
    with open('Worde_Yapistir/2021_IHL_Sorulari.txt', 'w', encoding='utf-8') as f:
        f.write(final_text)
    print("Success! Inserted Soru 27 and shifted the rest.")
else:
    print("Failed to split.")
