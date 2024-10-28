import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Замените на ваш API токен
API_TOKEN = '7368730334:AAH9xUG8G_Ro8mvV_fDQxd5ddkwjxHnBoeg'

bot = telebot.TeleBot(API_TOKEN)

def parse_site(option):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://temp-mail.io/ru")
    
    try:
        if option == "create_email":
            # Ждем загрузки страницы и получаем текст
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # Получаем текст из основного контейнера
            main_content = driver.find_element(By.CSS_SELECTOR, ".container").text
            logger.info("Получен текст из секции create_email")
            return f"Текст из раздела создания почты:\n{main_content[:500]}..."  # Ограничиваем вывод

        elif option == "view_messages":
            # Ждем загрузку и получаем текст из другой секции
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # Получаем текст из секции с сообщениями
            messages_content = driver.find_element(By.CSS_SELECTOR, ".main-content").text
            logger.info("Получен текст из секции view_messages")
            return f"Текст из раздела сообщений:\n{messages_content[:500]}..."  # Ограничиваем вывод

    except Exception as e:
        logger.error(f"Произошла ошибка при парсинге: {str(e)}")
        return "Произошла ошибка при получении данных с сайта."

    finally:
        driver.quit()

@bot.message_handler(commands=['start'])
def send_options(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton("Раздел 1", callback_data="create_email")
    btn2 = telebot.types.InlineKeyboardButton("Раздел 2", callback_data="view_messages")
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, "Выберите раздел для парсинга:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["create_email", "view_messages"])
def handle_query(call):
    bot.answer_callback_query(call.id)
    
    # Отправляем сообщение о начале парсинга
    processing_msg = bot.send_message(call.message.chat.id, "Начинаем парсинг...")
    
    # Выполняем парсинг
    result = parse_site(call.data)
    
    # Удаляем сообщение о процессе
    bot.delete_message(call.message.chat.id, processing_msg.message_id)
    
    # Отправляем результат
    bot.send_message(call.message.chat.id, result)

bot.polling()
