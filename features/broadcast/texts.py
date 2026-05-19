from html import escape


def truncate_text(text: str, limit: int = 500) -> str:
    if len(text) <= limit:
        return text

    return f"{text[:limit]}..."


def render_start_text(
    session_status_counts: dict[str, int],
    desired_batch_size: int,
    effective_batch_size: int,
    broadcast_text: str,
) -> str:
    text = escape(truncate_text(broadcast_text)) if broadcast_text else "не задан"

    return (
        "<b>📨 Рассылка</b>\n\n"
        "<b>Telethon сессии:</b>\n"
        f"Файлов: {session_status_counts['files']}\n"
        f"Валидных: {session_status_counts['loaded']}\n"
        f"Активных: {session_status_counts['active']}\n"
        f"Paused: {session_status_counts['paused']}\n"
        f"Dead: {session_status_counts['dead']}\n\n"
        f"<b>За раз:</b> {desired_batch_size} / доступно сейчас {effective_batch_size}\n\n"
        "<b>Текущий текст рассылки:</b>\n"
        f"<pre>{text}</pre>"
    )
