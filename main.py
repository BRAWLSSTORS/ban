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
from typing import Dict, Tuple

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Замените на ваш API токен
API_TOKEN = '7368730334:AAH9xUG8G_Ro8mvV_fDQxd5ddkwjxHnBoeg'

bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения email адресов пользователей
# Формат: {user_id: {'email': email, 'timestamp': time_created}}
user_emails: Dict[int, dict] = {}

def get_user_email(user_id: int) -> Tuple[str, bool]:
    """
    Получает email пользователя из хранилища.
    Возвращает tuple(email, is_expired)
    """
    if user_id not in user_emails:
        return None, True
    
    user_data = user_emails[user_id]
    current_time = time.time()
    # Проверяем, прошло ли больше 2 часов с момента создания
    is_expired = (current_time - user_data['timestamp']) > 7200  # 2 часа в секундах
    
    return user_data['email'], is_expired

def save_user_email(user_id: int, email: str):
    """Сохраняет email пользователя"""
    user_emails[user_id] = {
        'email': email,
        'timestamp': time.time()
    }

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
        # Пробуем получить выделенный текст
        email = driver.execute_script("return window.getSelection().toString();")
        if email and "@" in email:
            return email.strip()

        # Пробуем получить текст активного элемента
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

def create_email_keyboard(email: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления временной почтой"""
    keyboard = InlineKeyboardMarkup()
    email_url = f"https://temp-mail.io/ru/email/{email}/token/2y9kMzVYoSeKGkteeXfK"
    
    keyboard.row(
        InlineKeyboardButton(
            text="Перейти и посмотреть сообщения", 
            url=email_url
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="Посмотреть сообщения в боте", 
            callback_data=f"parse_{email}"
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="Получить новый адрес", 
            callback_data="new_email"
        )
    )
    
    return keyboard

@bot.message_handler(commands=['start', 'tempmail'])
def handle_tempmail(message):
    user_id = message.from_user.id
    email, is_expired = get_user_email(user_id)
    
    if email and not is_expired:
        # У пользователя есть действующий email
        response_text = (
            f"У вас уже есть активная временная почта:\n{email}\n\n"
            "Вы можете использовать её для регистрации на любых сайтах или сервисах.\n"
            "Или получить новый адрес, нажав соответствующую кнопку ниже."
        )
        bot.send_message(
            message.chat.id,
            response_text,
            reply_markup=create_email_keyboard(email)
        )
        return

    # Создаем новый email
    url = "https://temp-mail.io/ru"
    screenshot_path, email = take_screenshot_and_extract_email(url)

    if screenshot_path and email:
        with open(screenshot_path, 'rb') as file:
            bot.send_photo(message.chat.id, file)
        os.remove(screenshot_path)

        # Сохраняем email пользователя
        save_user_email(user_id, email)

        response_text = (
            f"Ваша новая временная почта: {email}\n\n"
            "Вы можете использовать её для регистрации на любых сайтах или сервисах.\n"
            "Почта действительна в течение 2 часов."
        )

        bot.send_message(
            message.chat.id,
            response_text,
            reply_markup=create_email_keyboard(email)
        )
    else:
        bot.reply_to(
            message,
            "Произошла ошибка при создании временной почты. Попробуйте снова через несколько минут."
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call: CallbackQuery):
    user_id = call.from_user.id
    
    if call.data == "new_email":
        # Пользователь запросил новый email
        handle_tempmail(call.message)
        return

    action, email = call.data.split("_", 1)
    
    if action == "parse" or action == "refresh_messages":
        stored_email, is_expired = get_user_email(user_id)
        
        if is_expired or stored_email != email:
            bot.answer_callback_query(
                call.id,
                "Срок действия этой почты истек. Пожалуйста, получите новый адрес.",
                show_alert=True
            )
            handle_tempmail(call.message)
            return
            
        messages = parse_email_messages(email)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton(
                text="Обновить сообщения", 
                callback_data=f"refresh_messages_{email}"
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                text="Вернуться в меню почты", 
                callback_data=f"back_to_menu_{email}"
            )
        )
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=messages,
                reply_markup=keyboard
            )
        except telebot.apihelper.ApiException as e:
            if "message is not modified" in str(e).lower():
                bot.answer_callback_query(
                    call.id,
                    "Новых сообщений пока нет",
                    show_alert=True
                )
            else:
                raise
                
    elif action == "back_to_menu":
        stored_email, is_expired = get_user_email(user_id)
        
        if is_expired or stored_email != email:
            bot.answer_callback_query(
                call.id,
                "Срок действия этой почты истек. Пожалуйста, получите новый адрес.",
                show_alert=True
            )
            handle_tempmail(call.message)
            return
            
        response_text = (
            f"Ваша временная почта: {email}\n\n"
            "Вы можете использовать её для регистрации на любых сайтах или сервисах.\n"
            "Почта действительна в течение 2 часов."
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=response_text,
            reply_markup=create_email_keyboard(email)
        )

if __name__ == "__main__":
    logger.info("Бот запущен")
    bot.infinity_polling()
