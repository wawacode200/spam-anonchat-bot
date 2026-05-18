from database.models import User


def profile_text(user: User) -> str:
    username = (
        f"@{user.username}"
        if user.username
        else "отсутствует"
    )

    return (
        f"<b>👤 Профиль</b>\n\n"
        f"🆔 ID: <code>{user.user_id}</code>\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"📅 В базе с: <code>{user.created_at:%d.%m.%Y %H:%M}</code>"
    )