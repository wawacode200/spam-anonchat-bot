ADMIN_TEXT = (
    "<b>🔐 Админ-панель</b>\n\n"
    "Выбери действие:"
)

def admin_stats_text(users_count: int) -> str:
    return (
        "<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей в базе: <b>{users_count}</b>"
    )