import os
import requests
from dotenv import load_dotenv

load_dotenv()
MOYSKLAD_TOKEN = os.getenv("MOYSKLAD_TOKEN")

def get_purchases(date_from: str, date_to: str):
    url = f"https://api.moysklad.ru/api/remap/1.2/report/profit/byproduct?momentFrom={date_from}&momentTo={date_to}"
    headers = {
        "Authorization": f"Bearer {MOYSKLAD_TOKEN}",
        "Content-Type": "application/json",
        "Accept-Encoding": "utf-8"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        purchases = []
        for row in data.get("rows", []):
            purchases.append({
                "дата": row.get("moment", "не указано")[:10],
                "товар": row.get("assortment", {}).get("name", "неизвестно"),
                "сумма": row.get("sellCost", 0)
            })

        return purchases

    except requests.RequestException as e:
        return [{"дата": "Ошибка", "товар": "Ошибка запроса", "сумма": str(e)}]
