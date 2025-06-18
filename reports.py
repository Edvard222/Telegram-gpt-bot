from collections import defaultdict

def generate_report(purchases):
    grouped = defaultdict(list)
    for p in purchases:
        sklad = p.get("склад", "Не указан")  # Защита от KeyError
        grouped[sklad].append(p)

    lines = ["📦 📦 Отчёт по закупкам:"]
    total = 0

    for sklad in sorted(grouped):  # Сортировка складов по алфавиту
        lines.append(f"\n🏬 Склад: {sklad}")
        # Сортировка по дате внутри склада
        for row in sorted(grouped[sklad], key=lambda x: x["дата"]):
            lines.append(f'{row["дата"]}: {row["товар"]} — {row["сумма"]} руб.')
            total += row["сумма"]

    lines.append(f"\n💰 Итого: {round(total, 2)} руб.")
    return "\n".join(lines)
