def generate_report(data: list) -> str:
    if not data:
        return "❗Нет данных по закупкам."

    report_lines = ["📦 Отчёт по закупкам:"]
    total = 0

    for row in data:
        date = row.get("дата", "не указано")
        product = row.get("товар", "неизвестно")
        try:
            amount = float(row.get("сумма", 0))
        except (ValueError, TypeError):
            amount = 0

        line = f"{date}: {product} — {amount:.2f} руб."
        report_lines.append(line)
        total += amount

    report_lines.append(f"\n💰 Итого: {total:.2f} руб.")
    return "\n".join(report_lines)
