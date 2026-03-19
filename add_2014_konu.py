import os
import re

file_path = r"C:\Users\osman\Desktop\OSYM\Worde_Yapistir\2014_DKAB_Sorulari.txt"

# Verify file exists
if not os.path.exists(file_path):
    print("File not found:", file_path)
    exit(1)

# Read file
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Topic mapping
konu_map = {}
def add_to_map(name, nums):
    for n in nums:
        konu_map[n] = name

add_to_map("Din Eğitimi", [40, 42, 43, 44, 45, 46, 48])
add_to_map("Kelam / Akaid", [13, 14, 15, 16, 17])
add_to_map("İslam Tarihi / Siyer", [1, 2, 3, 47])
add_to_map("Tefsir", [7, 8, 10, 12])
add_to_map("Fıkıh", [18, 19, 20])
add_to_map("Dinler Tarihi", [30, 34, 35, 36])
add_to_map("Din Psikolojisi", [29, 32, 33, 49, 50])
add_to_map("Hadis", [4, 5, 6])
add_to_map("İslam Mezhepleri ve Akımları", [16, 27, 28]) # Overrides 16 from Kelam
add_to_map("İslam Kültür ve Medeniyeti", [24, 25, 26, 39])
add_to_map("Din Felsefesi", [37, 38, 41])
add_to_map("Kur'an-ı Kerim ve Tecvid", [9, 11])
add_to_map("İslam Felsefesi", [21, 22, 23])
add_to_map("Din Sosyolojisi", [31])

new_lines = []
current_q = None
konu_added_for_q = False

i = 0
while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    
    # Check if this is a starting question line like: "Soru 1:" or "Soru 1 :"
    m = re.match(r"^Soru\s+(\d+)\s*:", line.strip())
    if m:
        current_q = int(m.group(1))
        konu_added_for_q = False
        
        # Check if next line is already KONU
        if i+1 < len(lines) and lines[i+1].strip().startswith("KONU:"):
            pass # Already has topic, skip adding one
        else:
            # We need to add the topic right under Soru
            topic = konu_map.get(current_q, "BİLİNMEYEN KONU")
            new_lines.append(f"KONU: {topic}\n")
            konu_added_for_q = True
    
    i += 1

# Write back
with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Done. Replaced 2014 file with KONU annotations.")
