from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import re
import json
from difflib import SequenceMatcher

def load_answers_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_text(text):
    text = text.replace('\u00A0', ' ').replace('«', '"').replace('»', '"')
    text = text.replace('–', '-')
    text = text.strip().lower()
    return re.sub(r'\s+', ' ', text)

def texts_match(a, b):
    a_clean = normalize_text(a)
    b_clean = normalize_text(b)
    if a_clean in b_clean or b_clean in a_clean:
        return True
    if set(a_clean.split()) == set(b_clean.split()):
        return True
    return SequenceMatcher(None, a_clean, b_clean).ratio() > 0.85

def find_answer(question, qa_dict):
    norm_q = normalize_text(question)
    best_match = None
    best_ratio = 0
    for key in qa_dict:
        ratio = SequenceMatcher(None, normalize_text(key), norm_q).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = key
    if best_ratio > 0.75:
        return qa_dict[best_match]
    return None

answers = load_answers_from_json("output.json")
print("Загружено ответов:", len(answers))

driver = webdriver.Chrome()
driver.get("https://lmsdo.rea.ru/login/index.php")
login = input("Введите логин: ")
password = input("Введите пароль: ")


driver.find_element(By.ID, "username").send_keys(login)
driver.find_element(By.ID, "password").send_keys(password)
driver.find_element(By.ID, "loginbtn").click()
time.sleep(5)
ref = input("Введите ссылку на тест: ")

driver.get(ref)
time.sleep(5)

def try_click(by, value):
    try:
        driver.find_element(by, value).click()
        return True
    except NoSuchElementException:
        return False

while True:
    time.sleep(2)
    questions = driver.find_elements(By.CLASS_NAME, "que")
    for q in questions:
        try:
            qtext = q.find_element(By.CLASS_NAME, "qtext").text.strip()
        except:
            continue

        print("\n" + "="*60)
        print("Вопрос с сайта:")
        print(qtext)
        print("-" * 60)

        matched_answer = find_answer(qtext, answers)

        if matched_answer:
            print("Найден ответ из файла:")
            print(matched_answer)
        else:
            print("Ответ не найден в файле")

        print("="*60 + "\n")

        if matched_answer:
            clicked = False
            labels = q.find_elements(By.TAG_NAME, "label")
            for label in labels:
                div = label.find_element(By.CSS_SELECTOR, "div.flex-fill.ml-1")
                label_text = div.text.strip()
                print(f"Вариант: '{label_text}' | Ожидаю: '{matched_answer}'")
                if texts_match(matched_answer, label_text):
                    try:
                        driver.execute_script("""
                            var rect = arguments[0].getBoundingClientRect();
                            var viewHeight = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
                            window.scrollBy({top: rect.top + window.scrollY - viewHeight/2, behavior: 'smooth'});
                        """, label)
                        time.sleep(0.3)
                        label.click()
                        print("Ответ выбран (label.click()):", label_text)
                        clicked = True
                        break
                    except Exception as e1:
                        try:
                            from selenium.webdriver.common.action_chains import ActionChains
                            ActionChains(driver).move_to_element(label).click().perform()
                            print("Ответ выбран (ActionChains):", label_text)
                            clicked = True
                            break
                        except Exception as e2:
                            try:
                                input_id = label.get_attribute("for")
                                if input_id:
                                    input_el = q.find_element(By.ID, input_id)
                                    driver.execute_script("arguments[0].scrollIntoView(true);", input_el)
                                    time.sleep(0.2)
                                    input_el.click()
                                    print("Ответ выбран (input.click()):", label_text)
                                    clicked = True
                                    break
                            except Exception as e3:
                                print("Не удалось кликнуть ни по label, ни по input:", e1, e2, e3)

            if not clicked:
                print("Не удалось выбрать правильный вариант для этого вопроса!")
        else:
            print("Нет правильного ответа для этого вопроса в файле — ничего не выбираю.")

    if try_click(By.NAME, "next"):
        print("➡ Переход на следующую страницу")
        continue
    if try_click(By.XPATH, "//button[contains(text(), 'Закончить попытку')]"):
        print("Заканчиваем попытку")
        break

time.sleep(2)
try_click(By.XPATH, "//button[contains(text(), 'Отправить всё и завершить тест')]")
time.sleep(2)
try_click(By.XPATH, "//button[contains(text(), 'Да')]")

print("Тест завершён и отправлен.")
