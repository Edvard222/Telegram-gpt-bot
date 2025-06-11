import os
import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from moysklad import get_purchases
from reports import generate_report

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PROXY_API_KEY = "sk-NXVc98OWiPlnqx2ufTlsPSW93CX2Fx6I"  # твой ключ от proxyapi.ru

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-архитектор. Напиши, что сделать.")

def ask_gpt_proxyapi(user_message: str) -> str:
    url = "https://proxyapi.ru/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_message}]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ошибка GPT: {response.status_code} — {response.text}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if "закупки" in user_message.lower():
        report = get_purchases("2025-05-01", "2025-05-31")
        result = generate_report(report)
        await update.message.reply_text(result)
    else:
        gpt_reply = ask_gpt_proxyapi(user_message)
        await update.message.reply_text(gpt_reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
