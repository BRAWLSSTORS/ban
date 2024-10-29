import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging
import time
import random
import re
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Замените на ваш API токен
API_TOKEN = '7368730334:AAH9xUG8G_Ro8mvV_fDQxd5ddkwjxHnBoeg'

bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения почтовых адресов пользователей
user_emails = {}

def take_screenshot_and_extract_email(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        logger.info(f"Загружена страница: {url}")
        time.sleep(random.uniform(2, 5))

        screenshot_path = 'tempmail_screenshot.png'
        driver.save_screenshot(screenshot_path)
        logger.info("Скриншот сохранен")

        email = extract_selected_email(driver)
        return screenshot_path, email

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return None, None

    finally:
        driver.quit()

def extract_selected_email(driver):
    try:
        email = driver.execute_script("return window.getSelection().toString();")
        if email and "@" in email:
            return email.strip()

        active_element_text = driver.execute_script("return document.activeElement.textContent;")
        if active_element_text and "@" in active_element_text:
            return active_element_text.strip()

    except Exception as e:
        logger.error(f"Ошибка при поиске email: {str(e)}")

    return None

def parse_email_messages(email):
    url = f"https://temp-mail.io/ru/email/{email}/token/2y9kMzVYoSeKGkteeXfK"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        time.sleep(random.uniform(2, 5))

        messages = driver.execute_script("return document.body.innerText;")
        if not messages:
            return "Сообщений не найдено."

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
            "Условия использования", "Контакты", "Что такое временная почта"
        ]

        for phrase in unwanted_phrases:
            messages = messages.replace(phrase, "")

        cleaned_messages = "\n".join([line.strip() for line in messages.splitlines() if line.strip()])
        
        numbers_pattern = r'\n1\n2\n3\n*$'
        cleaned_messages = re.sub(numbers_pattern, '', cleaned_messages)

        return cleaned_messages if cleaned_messages else "Сообщений не найдено."

    except Exception as e:
        logger.error(f"Ошибка при парсинге сообщений: {str(e)}")
        return "Произошла ошибка при получении сообщений."

    finally:
        driver.quit()

def get_email_menu_keyboard(email):
    """Создает клавиатуру для главного меню почты"""
    keyboard = InlineKeyboardMarkup()
    email_url = f"https://temp-mail.io/ru/email/{email}/token/2y9kMzVYoSeKGkteeXfK"
    keyboard.add(
        InlineKeyboardButton(text="Перейти и посмотреть сообщения", url=email_url),
        InlineKeyboardButton(text="Посмотреть сообщения в боте", callback_data=f"parse_{email}")
    )
    return keyboard

def get_messages_menu_keyboard(email):
    """Создает клавиатуру для меню сообщений"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(text="Посмотреть новые сообщения", callback_data=f"refresh_messages_{email}")
    )
    keyboard.add(
        InlineKeyboardButton(text="Вернуться в меню почты", callback_data=f"back_to_menu_{email}")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, 
                 "Привет! Я бот для работы с временной почтой.\n"
                 "Используйте команду /tempmail чтобы создать новый временный почтовый ящик.")

@bot.message_handler(commands=['tempmail'])
def handle_tempmail(message):
    url = "https://temp-mail.io/ru"
    screenshot_path, email = take_screenshot_and_extract_email(url)

    if screenshot_path:
        with open(screenshot_path, 'rb') as file:
            bot.send_photo(message.chat.id, file)
        os.remove(screenshot_path)

        if email:
            # Сохраняем email для пользователя
            user_emails[message.chat.id] = email
            
            response_text = (
                f"Ваша временная почта: {email}\n\n"
                "Вы можете использовать её для регистрации на любых сайтах или сервисах.\n"
                "Вы можете управлять своим email кнопками ниже."
            )

            keyboard = get_email_menu_keyboard(email)
            bot.send_message(message.chat.id, response_text, reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Не удалось найти выделенный email.")
    else:
        bot.reply_to(message, "Произошла ошибка при создании скриншота. Попробуйте снова.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("parse_", "back_to_menu_", "refresh_messages_")))
def handle_parse_messages(call: CallbackQuery):
    action, email = call.data.split("_", 1)
    user_id = call.message.chat.id
    
    # Проверяем, соответствует ли email сохраненному для пользователя
    if user_id not in user_emails or user_emails[user_id] != email:
        bot.answer_callback_query(call.id, "Этот email больше не действителен. Создайте новый с помощью /tempmail")
        return

    try:
        if action == "parse" or action == "refresh_messages":
            messages = parse_email_messages(email)
            keyboard = get_messages_menu_keyboard(email)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=messages,
                reply_markup=keyboard
            )
            
        elif action == "back_to_menu":
            response_text = (
                f"Ваша временная почта: {email}\n\n"
                "Вы можете использовать её для регистрации на любых сайтах или сервисах.\n"
                "Вы можете управлять своим email кнопками ниже."
            )
            
            keyboard = get_email_menu_keyboard(email)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response_text,
                reply_markup=keyboard
            )

        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке callback query: {str(e)}")
        bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте снова.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Используйте команду /tempmail для создания временной почты.")

if __name__ == "__main__":
    logger.info("Бот запущен")
    bot.polling(none_stop=True)
