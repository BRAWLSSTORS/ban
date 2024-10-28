import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Замените на ваш API токен
API_TOKEN = '7368730334:AAH9xUG8G_Ro8mvV_fDQxd5ddkwjxHnBoeg'

bot = telebot.TeleBot(API_TOKEN)

def visit_temp_mail(option):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://temp-mail.io/ru")
    
    try:
        if option == "create_email":
            # Нажать кнопку "Создать новую почту"
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.header-btn.v-tooltip-open'))
            )
            button.click()
            time.sleep(2)  # Ожидание загрузки почты
            
            # Парсинг почты из input поля
            email_element = driver.find_element(By.CSS_SELECTOR, 'input#email')
            email = email_element.get_attribute("value")
            logger.info(f"Сгенерирован новый адрес почты: {email}")
            return f"Ваш новый почтовый адрес: {email}"

        elif option == "view_messages":
            # Парсинг всех сообщений на странице
            messages = driver.page_source
            logger.info("Сообщения на странице успешно получены")
            return messages[:1000]  # Ограничение на вывод текста

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return "Произошла ошибка при взаимодействии с сайтом."

    finally:
        driver.quit()

@bot.message_handler(commands=['tempmail'])
def send_temp_mail_options(message):
    markup = telebot.types.InlineKeyboardMarkup()
    create_email_btn = telebot.types.InlineKeyboardButton("Создать новую почту", callback_data="create_email")
    view_messages_btn = telebot.types.InlineKeyboardButton("Посмотреть сообщения в почте", callback_data="view_messages")
    markup.add(create_email_btn, view_messages_btn)
    
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["create_email", "view_messages"])
def handle_temp_mail_option(call):
    bot.answer_callback_query(call.id)
    
    if call.data == "create_email":
        result = visit_temp_mail("create_email")
    elif call.data == "view_messages":
        result = visit_temp_mail("view_messages")
    
    bot.send_message(call.message.chat.id, result)

bot.polling()
