import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging
import time
import random
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

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

def parse_email_messages(email):
    """Функция для парсинга сообщений с сайта temp-mail."""
    url = f"https://temp-mail.io/ru/email/{email}/token/2y9kMzVYoSeKGkteeXfK"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        time.sleep(random.uniform(2, 5))  # Задержка для загрузки контента

        # Извлечение текста сообщений с помощью JavaScript
        messages = driver.execute_script("return document.body.innerText;")
        if not messages:
            return "Сообщений не найдено."

        # Список фраз, которые нужно удалить
        unwanted_phrases = [
            "Ваш временный email", "?", "скопировать", "обновить", "случайный",
            "изменить", "пересылка", "удалить", "Премиум",
            "Как использовать временную почту?",
            "Скопируйте email адрес из левого верхнего угла",
            "Используйте этот email для регистрации на сайтах, загрузки контента, и так далее",
            "Прочитайте входящие письма на этой странице в левой части сайта",
            "Что такое временная почта?",
            "Временная почта защищает основной email адрес от надоедливых рекламных рассылок, спама и злоумышленников. "
            "Она анонимна и полностью бесплатна. У неё ограниченный срок действия: если в течение "
            "определённого времени на такой email не будут приходить письма, то он удалится. В интернете встречаются "
            "другие названия для такой почты — «анонимная почта», «почта на 10 минут», «одноразовая почта». "
            "Временная почта позволяет регистрироваться на разных сайтах (например, в социальных сетях), "
            "скачивать файлы из файлообменников, применять там, где можно скрыть реальный email.",
            "Мы используем собственные и сторонние cookie, чтобы улучшить ваше взаимодействие с нашим сервисом, "
            "анализируя, как пользователи используют сайт. Продолжая использовать сайт, вы подтверждаете, что согласны с этим.",
            "Русский", "Выберите язык", "English", "Deutsch", "Français",
            "Türkçe", "Espanol", "中文", "Italiano", "Українська", "فارسی",
            "हिन्दी", "العربية", "© temp-mail.io 2024", "Bump", "Меню",
            "Блог", "Расширения", "Пожертвования", "FAQ", "Политика конфиденциальности",
            "Условия использования", "Контакты", "Что такое временная почта", "Временная почта защищает основной email адрес от надоедливых рекламных рассылок, спама и злоумышленников. Она анонимна и полностью бесплатна. У неё ограниченный срок действия: если в течении определённого времени на такой email не будут приходить письма, то он удалится. В интернете встречаются другие названия для такой почты — «анонимная почта», «почта на 10 минут», «одноразовая почта». Временная почта позволяет регистрироваться на разных сайтах (к примеру, в социальных сетях), скачивать файлы из файлообменников, применять там, где можно скрыть реальный email и воспользоваться временной почтой. Например, общественные wi-fi точки, различные форумы и блоги требуют от посетителей зарегистрироваться, чтобы полноценно использовать их сайт.", "Как использовать временную почту"
        ]

        # Удаление нежелательных фраз
        for phrase in unwanted_phrases:
            messages = messages.replace(phrase, "")

        # Удаление лишних пробелов и пустых строк
        cleaned_messages = "\n".join([line.strip() for line in messages.splitlines() if line.strip()])

        return cleaned_messages if cleaned_messages else "Сообщений не найдено."

    except Exception as e:
        logger.error(f"Ошибка при парсинге сообщений: {str(e)}")
        return "Произошла ошибка при получении сообщений."

    finally:
        driver.quit()

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

            # Создание кнопок
            email_url = f"https://temp-mail.io/ru/email/{email}/token/2y9kMzVYoSeKGkteeXfK"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(text="Перейти и посмотреть сообщения", url=email_url),
                InlineKeyboardButton(text="Посмотреть сообщения в боте", callback_data=f"parse_{email}")
            )

            bot.send_message(message.chat.id, response_text, reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Не удалось найти выделенный email.")
    else:
        bot.reply_to(message, "Произошла ошибка при создании скриншота. Попробуйте снова.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("parse_"))
def handle_parse_messages(call: CallbackQuery):
    email = call.data.split("_", 1)[1]
    messages = parse_email_messages(email)
    bot.send_message(call.message.chat.id, f"{messages}")

bot.polling()
