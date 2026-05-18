def start_text(
    sent: int,
    failed: int,
    batch_size: int,
    interval: int,
    is_running: bool,
) -> str:
    status = "🟢 работает" if is_running else "⚪ остановлена"

    return (
        f"<b>📨 Рассылка</b>\n\n"
        f"Статус: <b>{status}</b>\n\n"
        f"За раз: <code>{batch_size}</code>\n"
        f"Интервал: <code>{interval} сек.</code>\n\n"
        f"Отправлено: <code>{sent}</code>\n"
        f"Ошибок: <code>{failed}</code>"
    )