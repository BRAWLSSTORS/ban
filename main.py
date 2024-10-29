import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging
import time
import random
import re  # Для регулярных выражений

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Замените на ваш API токен
API_TOKEN = '7368730334:AAH9xUG8G_Ro8mvV_fDQxd5ddkwjxHnBoeg'

bot = telebot.TeleBot(API_TOKEN)

def take_screenshot_and_extract_email(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Открытие браузера в фоновом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        logger.info(f"Загружена страница: {url}")
        time.sleep(random.uniform(2, 5))  # Случайная задержка после загрузки страницы

        # Скриншот страницы
        screenshot_path = 'tempmail_screenshot.png'
        driver.save_screenshot(screenshot_path)
        logger.info("Скриншот сохранен")

        # Парсинг текста на странице для поиска email
        page_text = driver.find_element("tag name", "body").text
        email = extract_email(page_text)

        return screenshot_path, email

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return None, None

    finally:
        driver.quit()

def extract_email(text):
    """Ищет email с символом '@' в тексте. Прекращает парсинг после пробела."""
    match = re.search(r'\b[\w.-]+@[\w.-]+\b', text)  # Регулярное выражение для поиска email
    if match:
        return match.group(0)
    return None

@bot.message_handler(commands=['tempmail'])
def handle_tempmail(message):
    url = "https://temp-mail.io/ru"
    screenshot_path, email = take_screenshot_and_extract_email(url)

    if screenshot_path:
        with open(screenshot_path, 'rb') as file:
            bot.send_photo(message.chat.id, file)
        os.remove(screenshot_path)

        if email:
            bot.send_message(message.chat.id, f"Найден email: {email}")
        else:
            bot.send_message(message.chat.id, "Email не найден на странице.")
    else:
        bot.reply_to(message, "Произошла ошибка при создании скриншота. Попробуйте снова.")

bot.polling()
