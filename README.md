# Base Aiogram Bot Template

Базовый шаблон для Telegram-ботов на aiogram 3 с:

- aiogram 3
- SQLAlchemy + SQLite
- Alembic
- Middleware
- Feature-based архитектурой
- Admin системой
- Profile системой
- Git/GitHub workflow
- Systemd deploy
- Автоперезапуском при разработке

---

# Структура проекта

```text
project/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── DEPLOY.md
├── commands.md
├── alembic.ini
│
├── main.py
├── config.py
│
├── bot/
│   ├── factory.py
│   ├── routers.py
│   └── webhooks.py
│
├── database/
│   ├── base.py
│   ├── session.py
│   ├── models.py
│   └── repositories/
│
├── middlewares/
│   ├── db.py
│   ├── user.py
│   └── admin.py
│
├── features/
│   ├── start/
│   ├── profile/
│   └── admin/
│
├── services/
│
├── common/
│   ├── callbacks.py
│   ├── filters.py
│   ├── keyboards.py
│   ├── texts.py
│   ├── time.py
│   └── utils.py
│
└── migrations/
```

---

# Архитектура

Новая функциональность создаётся внутри `features`.

Пример:

```text
features/support/
├── router.py
├── service.py
├── repository.py
├── callbacks.py
├── keyboards.py
├── texts.py
├── states.py
```

Создавать только нужные файлы.

Например:

Простая страница:

```text
features/start/
├── router.py
├── keyboards.py
└── texts.py
```

Сложная логика:

```text
features/payments/
├── router.py
├── service.py
├── repository.py
├── callbacks.py
├── keyboards.py
├── texts.py
└── states.py
```

---

# Создание нового бота

Клонировать шаблон:

```bash
git clone REPOSITORY_URL my-bot
git clone git@github.com:wawacode200/base-aiogram-bot.git anon-spamer-bot
```

Перейти:

```bash
cd my-bot
```

Удалить старый git:

```bash
rm -rf .git
```

Создать новый:

```bash
git init
```

Создать venv:

```bash
python3 -m venv .venv
```

Активировать:

Mac/Linux:

```bash
python3.12 -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Установить зависимости:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Создать env:

```bash
cp .env.example .env
```

---

# .env

Пример:

```env
BOT_TOKEN=YOUR_TOKEN
ADMINS=123456789
DATABASE_URL=sqlite+aiosqlite:///database/bot.db
```

ADMINS:

```env
ADMINS=123,456,789
```

---

# Локальный запуск

Запуск:

```bash
python main.py
```

---

# База данных

Создать миграцию:

```bash
alembic revision --autogenerate -m "message"
```

Применить:

```bash
alembic upgrade head
```

Откатить:

```bash
alembic downgrade -1
```

Текущая:

```bash
alembic current
```

История:

```bash
alembic history
```

---

# GitHub

Добавить удалённый репозиторий:

SSH:

```bash
git remote add origin git@github.com:USERNAME/REPOSITORY.git
```

Проверить:

```bash
git remote -v
```

Первый пуш:

```bash
git branch -M main
git push -u origin main
```

---

# Первый деплой на сервер

Подключение:

```bash
ssh root@SERVER_IP
```

Создать папку:

```bash
mkdir -p /root/bots
cd /root/bots
```

Клонировать:

```bash
git clone REPOSITORY_URL
```

Перейти:

```bash
cd PROJECT_NAME
```

Создать venv:

```bash
python3 -m venv .venv
```

Активировать:

```bash
source .venv/bin/activate
```

Установить зависимости:

```bash
pip install -r requirements.txt
```

Создать env:

```bash
cp .env.example .env
nano .env
```

Применить миграции:

```bash
alembic upgrade head
```

Проверка:

```bash
python main.py
```

---

# Systemd

Создать:

```bash
nano /etc/systemd/system/bot.service
```

Содержимое:

```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/bots/PROJECT_NAME
ExecStart=/root/bots/PROJECT_NAME/.venv/bin/python main.py

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Обновить:

```bash
systemctl daemon-reload
```

Включить:

```bash
systemctl enable bot
```

Запустить:

```bash
systemctl start bot
```

Статус:

```bash
systemctl status bot
```

Логи:

```bash
journalctl -u bot -f
```

Перезапуск:

```bash
systemctl restart bot
```

Остановить:

```bash
systemctl stop bot
```

---

# Обновление бота

```bash
cd /root/bots/PROJECT_NAME

git pull

source .venv/bin/activate

pip install -r requirements.txt

alembic upgrade head

systemctl restart bot
```

---

# Рекомендации

Не коммитить:

```text
.env
.venv
.idea
*.db
*.sqlite
*.log
__pycache__
```

Коммитить:

```text
migrations/versions
```

Использовать:

```python
from common.time import now_msk
```

Не использовать:

```python
datetime.now()
datetime.utcnow()
```

---

# TODO для нового проекта

- [ ] BOT_TOKEN
- [ ] ADMINS
- [ ] модели БД
- [ ] миграции
- [ ] middleware
- [ ] админка
- [ ] деплой
- [ ] webhook (если нужен)