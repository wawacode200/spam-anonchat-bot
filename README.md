# Base Aiogram Bot Template

Базовый шаблон для Telegram-ботов на aiogram 3.

Стек:

* aiogram 3
* SQLAlchemy + SQLite
* Alembic
* Middleware
* Feature-based архитектура
* Systemd
* GitHub Actions
* MSK timezone helpers

---

# Используемые версии

```txt
aiogram==3.20.0.post0
python-dotenv==1.1.0
SQLAlchemy==2.0.41
aiosqlite==0.21.0
greenlet==3.2.1
alembic==1.16.5
watchdog==6.0.0
```

---

# Python версия

Шаблон рассчитан на:

```text
Python 3.12.x
```

Проверка:

```bash
python --version
```

Должно быть:

```text
Python 3.12.x
```

---

# Структура проекта

```text
project/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
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
    └── versions/
```

---

# Архитектура

Каждая фича живёт отдельно.

Пример:

```text
features/support/
├── router.py
├── service.py
├── repository.py
├── callbacks.py
├── keyboards.py
├── texts.py
└── states.py
```

Создавать только нужные файлы.

Простая фича:

```text
features/start/
├── router.py
├── keyboards.py
└── texts.py
```

Сложная:

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

Не плодить:

```text
handlers/
keyboards/
texts/
```

---

# Создание нового бота

Клонировать шаблон:

```bash
git clone git@github.com:wawacode200/base-aiogram-bot.git my-bot
```

Перейти:

```bash
cd my-bot
```

Удалить старый git:

```bash
rm -rf .git
git init
```

Создать venv:

Mac/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Проверить:

```bash
python --version
```

Установить зависимости:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Создать `.env`:

```bash
cp .env.example .env
```

---

# .env

```env
BOT_TOKEN=
ADMINS=
DATABASE_URL=sqlite+aiosqlite:///database/bot.db
```

Пример:

```env
BOT_TOKEN=123456:ABC
ADMINS=123456789,987654321
DATABASE_URL=sqlite+aiosqlite:///database/bot.db
```

---

# Локальный запуск

```bash
python main.py
```

---

# База данных

Создание миграции:

```bash
alembic revision --autogenerate -m "create users table"
```

После создания открыть:

```text
migrations/versions/
```

Проверить файл:

Плохо:

```python
def upgrade():
    pass
```

Нормально:

```python
def upgrade():
    op.create_table(...)
```

Применить:

```bash
alembic upgrade head
```

Текущая версия:

```bash
alembic current
```

История:

```bash
alembic history
```

Откат:

```bash
alembic downgrade -1
```

---

# Изменение БД

Изменить модель:

```python
balance: Mapped[int] = mapped_column(
    Integer,
    default=0,
)
```

Рабочий цикл:

```text
1. Изменил models.py
2. alembic revision --autogenerate
3. Проверил миграцию
4. alembic upgrade head
```

Создать:

```bash
alembic revision --autogenerate -m "add balance"
```

Применить:

```bash
alembic upgrade head
```

---

# Если миграция пустая

Если получил:

```python
def upgrade():
    pass
```

Проверить:

```python
from database.base import Base
import database.models

target_metadata = Base.metadata
```

Не менять:

```python
target_metadata = User.metadata
```

Не удалять:

```python
import database.models
```

---

# Полный сброс Alembic

Удалить миграции:

```bash
rm migrations/versions/*.py
```

Удалить базу:

```bash
rm database/bot.db
```

Создать заново:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

---

# GitHub

Добавить удалённый репозиторий:

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
git add .
git commit -m "init"
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
git clone git@github.com:USERNAME/PROJECT_NAME.git
```

Перейти:

```bash
cd PROJECT_NAME
```

Создать venv:

```bash
python3.12 -m venv .venv
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

Проверить:

```bash
python main.py
```

---

# Systemd

Создать:

```bash
nano /etc/systemd/system/PROJECT_NAME.service
```

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

Запуск:

```bash
systemctl daemon-reload
systemctl enable PROJECT_NAME
systemctl broadcast PROJECT_NAME
```

Логи:

```bash
journalctl -u PROJECT_NAME -f
```

Рестарт:

```bash
systemctl restart PROJECT_NAME
```

---

# GitHub Actions автодеплой

Создать:

```bash
mkdir -p .github/workflows
```

Создать:

```text
.github/workflows/deploy.yml
```

```yaml
name: Deploy

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Deploy
        uses: appleboy/ssh-action@master

        with:
          host: ${{ secrets.SERVER_HOST }}
          username: root
          key: ${{ secrets.SERVER_SSH_KEY }}

          script: |
            cd /root/bots/PROJECT_NAME

            git pull
            source .venv/bin/activate
            pip install -r requirements.txt
            alembic upgrade head
            systemctl restart PROJECT_NAME
```

---

# GitHub Secrets

Открыть:

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
```

Создать:

```text
SERVER_HOST
SERVER_SSH_KEY
```

---

# Рабочий цикл

```text
1. Пишешь код
2. git add .
3. git commit -m "update"
4. git push

Дальше автоматически:

5. GitHub Actions
6. SSH на сервер
7. git pull
8. pip install
9. alembic upgrade
10. systemctl restart
```

---

# Время

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

# Не коммитить

```text
.env
.venv
.idea
*.db
*.sqlite
*.session
*.log
__pycache__/
```
