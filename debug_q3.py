# Debug parsing of question 3
with open('Worde_Yapistir/2020_DKAB_Sorulari.txt', 'r', encoding='utf-8') as file:
    content = file.read()

soru_blocks = content.split('---SONRAKİ SORU---')

for i, block in enumerate(soru_blocks):
    if 'Soru 3:' in block:
        print("=== SORU 3 BLOCK ===")
        print(repr(block))
        print("\n=== SORU 3 READABLE ===")
        print(block)
        break
