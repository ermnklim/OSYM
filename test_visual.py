# Test parsing of question 3 to see if visual files are detected
import sys
sys.path.append('Python_Verisi')
from dkab_quiz_modern import ModernDKABQuiz

# Create a test instance
quiz = ModernDKABQuiz(None)

# Parse 2020 questions
questions = quiz.parse_questions_from_file('Worde_Yapistir/2020_DKAB_Sorulari.txt', 2020)

# Find question 3 and 13
q3 = next((q for q in questions if q['soru_no'] == 3), None)
q13 = next((q for q in questions if q['soru_no'] == 13), None)

print('Soru 3 görsel bilgisi:')
if q3:
    print(f'  Görsel var: {q3.get("gorsel_var", False)}')
    print(f'  Görsel dosyaları: {q3.get("gorsel_dosyalari", [])}')

print('')
print('Soru 13 görsel bilgisi:')
if q13:
    print(f'  Görsel var: {q13.get("gorsel_var", False)}')
    print(f'  Görsel dosyaları: {q13.get("gorsel_dosyalari", [])}')
