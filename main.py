import os
import asyncio
import urllib.parse
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from reports import generate_report

# Загрузка переменных из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")
MOYSKLAD_TOKEN = os.getenv("MOYSKLAD_TOKEN")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-архитектор. Напиши, что сделать.")

# Запрос к ProxyAPI (GPT)
def ask_gpt_proxyapi(user_message: str) -> str:
    url = "https://api.proxyapi.ru/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_message}]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        return f"Ошибка при обращении к GPT: {str(e)}"

# Получение закупок из МойСклад
def get_purchases(date_from: str, date_to: str):
    token = os.getenv("MOYSKLAD_TOKEN")
    if not token:
        return [{"дата": "Ошибка", "товар": "Токен МойСклад не найден", "сумма": 0}]

    # Формируем фильтр с корректным форматом времени и URL-кодированием
    raw_filter = f'moment>={date_from} 00:00:00;moment<={date_to} 23:59:59'
    filter_query = urllib.parse.quote(raw_filter)

    url = f"https://api.moysklad.ru/api/remap/1.2/entity/supply?filter={filter_query}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json;charset=utf-8",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return [{
                "дата": "Ошибка",
                "товар": response.text,
                "сумма": 0
            }]

        raw = response.json()
        purchases = []

        for row in raw.get("rows", []):
            date = row.get("moment", "").replace("T", " ")[:19]
            sum_rub = row.get("sum", 0) / 100
            name = row.get("name", "Без названия")
            store = row.get("store", {}).get("name", "Не указан склад")
            purchases.append({
                "дата": date,
                "товар": name,
                "сумма": round(sum_rub, 2),
                "склад": store
            })

        return purchases

    except requests.RequestException as e:
        return [{"дата": "Ошибка", "товар": f"Ошибка запроса — {str(e)}", "сумма": 0}]

from datetime import datetime
from utils import parse_date_period  # убедись, что эта функция есть

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()

    # Распознаём даты (если есть)
    date_from, date_to = parse_date_period(user_message)

    if not date_from:
        # Если даты не распознаны, берем "сегодня"
        today = datetime.now().strftime("%Y-%m-%d")
        date_from = date_to = today

    # Закупки
    if "закупки" in user_message:
        report = get_purchases(date_from, date_to)
        result = generate_report(report)
        await update.message.reply_text(f"📦 Закупки с {date_from} по {date_to}:\n\n{result}")
    
    # Продажи
    elif "продажи" in user_message:
        report = get_sales(date_from, date_to)  # ты напишешь эту функцию позже
        result = generate_sales_report(report)
        await update.message.reply_text(f"💸 Продажи с {date_from} по {date_to}:\n\n{result}")
    
    # Отгрузки
    elif "отгрузки" in user_message:
        report = get_shipments(date_from, date_to)  # функция для отгрузок
        result = generate_shipments_report(report)
        await update.message.reply_text(f"🚚 Отгрузки с {date_from} по {date_to}:\n\n{result}")
    
    # По умолчанию — отправить в GPT
    else:
        gpt_reply = ask_gpt_proxyapi(user_message)
        await update.message.reply_text(gpt_reply)

# Запуск бота
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
