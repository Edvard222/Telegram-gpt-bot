def generate_report(data: list) -> str:
    report_lines = ["Отчёт по закупкам:"]
    total = 0

    for row in data:
        line = f"{row['дата']}: {row['товар']} — {row['сумма']} руб."
        report_lines.append(line)
        total += row['сумма']

    report_lines.append(f"\nИтого: {total} руб.")
    return "\n".join(report_lines)
