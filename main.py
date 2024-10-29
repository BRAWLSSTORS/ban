import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging
import time
import random
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

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
        time.sleep(random.uniform(2, 5))  # Случайная задержка

        # Скриншот страницы
        screenshot_path = 'tempmail_screenshot.png'
        driver.save_screenshot(screenshot_path)
        logger.info("Скриншот сохранен")

        # Попытка найти выделенный email
        email = extract_selected_email(driver)

        return screenshot_path, email

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return None, None

    finally:
        driver.quit()

def extract_selected_email(driver):
    """Ищет текст, который выделен на странице (или активный элемент)."""
    try:
        # Выполнение JavaScript для получения выделенного текста
        email = driver.execute_script("return window.getSelection().toString();")
        if email and "@" in email:
            return email.strip()

        # Альтернативная проверка активного элемента
        active_element_text = driver.execute_script("return document.activeElement.textContent;")
        if active_element_text and "@" in active_element_text:
            return active_element_text.strip()

    except Exception as e:
        logger.error(f"Ошибка при поиске email: {str(e)}")

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
            response_text = (
                f"Ваша временная почта: {email}\n\n"
                "Вы можете использовать её для регистрации на любых сайтах или сервисах.\n"
                "Вы можете управлять своим email кнопками ниже."
            )

            # Создание инлайн-кнопки с ссылкой на почту
            email_url = f"https://temp-mail.io/ru/email/{email}/token/2y9kMzVYoSeKGkteeXfK?utm_campaign=TempMailBot&utm_content=message_details&utm_medium=organic&utm_source=telegram-bot"
            keyboard = InlineKeyboardMarkup()
            button = InlineKeyboardButton(text="Просмотреть сообщения", url=email_url)
            keyboard.add(button)

            bot.send_message(message.chat.id, response_text, reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Не удалось найти выделенный email.")
    else:
        bot.reply_to(message, "Произошла ошибка при создании скриншота. Попробуйте снова.")

bot.polling()
