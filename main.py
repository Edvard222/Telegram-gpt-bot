import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from moysklad import get_purchases
from reports import generate_report

load_dotenv()
TELEGRAM_TOKEN = os.getenv("8075075075:AAHMDK-iHkY2K9ZFDQBd3JXc25pP0U5Pv44")
PROXY_API_KEY = os.getenv("sk-NXVc98OWiPlnqx2ufTlsPSW93CX2Fx6I")

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

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        return f"Ошибка при обращении к GPT: {str(e)}"

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
