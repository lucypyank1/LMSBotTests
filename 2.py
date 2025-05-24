import re
import json

with open("input.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

result = []
question = ""
answers = {}
correct_letter = ""
correct_answer = ""

for line in lines:
    line = line.strip()
    if re.match(r"^Вопрос \d+:", line):
        question = ""
        answers = {}
        correct_letter = ""
        correct_answer = ""
        continue
    elif question == "" and line and not line.startswith(("А)", "Б)", "В)", "Г)", "Д)", "Правильный ответ:")):
        question = line
    elif re.match(r"^[А-Г]\)", line):
        letter = line[0]
        answer_text = line[2:].strip()
        answers[letter] = answer_text
    elif line.startswith("Правильный ответ:"):
        m = re.search(r"([А-Г])", line)
        if m:
            correct_letter = m.group(1)
            correct_answer = answers.get(correct_letter, "")
            if question and correct_answer:
                result.append((question, correct_answer))
        question = ""
        answers = {}
        correct_letter = ""
        correct_answer = ""

qa_dict = {q: a for q, a in result}

with open("output.json", "w", encoding="utf-8") as f:
    json.dump(qa_dict, f, ensure_ascii=False, indent=2)