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

    # Без времени! Только даты
    filter_query = urllib.parse.quote(f"moment>={date_from};moment<={date_to}")
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
            date = row.get("moment", "").split("T")[0]
            sum_rub = row.get("sum", 0) / 100
            name = row.get("name", "Без названия")
            purchases.append({"дата": date, "товар": name, "сумма": round(sum_rub, 2)})

        return purchases

    except requests.RequestException as e:
        return [{"дата": "Ошибка", "товар": f"Ошибка запроса — {str(e)}", "сумма": 0}]
# Обработка входящих сообщений

import re
from datetime import datetime
import locale

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')  # Только для Linux-систем с русским языком

def parse_date_period(text: str):
    pattern = r"с\s+(\d{1,2})\s+([а-яА-Я]+)\s+по\s+(\d{1,2})\s+([а-яА-Я]+)"
    match = re.search(pattern, text.lower())

    if not match:
        return None, None

    day_from, month_from, day_to, month_to = match.groups()

    try:
        year = datetime.now().year
        date_from = datetime.strptime(f"{day_from} {month_from} {year}", "%d %B %Y").date()
        date_to = datetime.strptime(f"{day_to} {month_to} {year}", "%d %B %Y").date()
        return date_from.isoformat(), date_to.isoformat()
    except Exception:
        return None, None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()

    if "приемки" in user_message and "с" in user_message and "по" in user_message:
        date_from, date_to = parse_date_period(user_message)
        if date_from and date_to:
            report = get_purchases(date_from, date_to)  # пока те же данные, можешь позже заменить на get_receipts
            result = generate_report(report)
            await update.message.reply_text(f"📦 {result}")
        else:
            await update.message.reply_text("❗Не смог распознать даты. Пример: 'приемки с 5 июня по 10 июня'")
    elif "закупки" in user_message:
        report = get_purchases("2025-06-01", "2025-06-09")
        result = generate_report(report)
        await update.message.reply_text(f"📦 {result}")
    else:
        gpt_reply = ask_gpt_proxyapi(user_message)
        await update.message.reply_text(gpt_reply)

# Запуск бота
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
