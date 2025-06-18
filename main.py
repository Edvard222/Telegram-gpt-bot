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
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if "закупки" in user_message.lower():
        report = get_purchases("2025-06-01", "2025-06-09")
        result = generate_report(report)
        await update.message.reply_text(f"📦 📦 Отчёт по закупкам:\n{result}")
    else:
        gpt_reply = await asyncio.to_thread(ask_gpt_proxyapi, user_message)
        await update.message.reply_text(gpt_reply)

# Запуск бота
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
