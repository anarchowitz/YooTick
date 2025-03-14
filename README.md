# 🎟️ YooTick - Discord Ticket Bot

**Лучшая бесплатная замена платным Akemi (обращение) и TicketTool (тикеты)**  
*Полностью настраиваемый бот для управления тикетами на вашем Discord-сервере*

[![Telegram Contact](https://img.shields.io/badge/Contact-Telegram-blue?logo=telegram)](https://t.me/anarchowitz)
[![RU/EU Support](https://img.shields.io/badge/Support-RU%2FEU-orange)](https://yooma.su)

[![SQLite](https://img.shields.io/badge/-SQLite-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)](https://python.org)
[![Disnake](https://img.shields.io/badge/-Disnake-5865F2?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAYFJREFUeNqkk79KA0EQxr9bE4u0FkGCBHJgo4WIjUdqYWNnI/gGUuQNtE6lrxALQbC1sxAsBAtBEA8sBAtB0gCBnJwhV4jZ/c3s3t0m5g4Cf9idmW++/5mdUc45/LLKfA5jDCilwFoLWmsuM5TneZ6HsiyRpil4nscF0zR5nGXZbwDvYIxBFEVwOBxgt9tBHMdQFAV0XQd934Pv+6C1hiRJYLlcwnq9htVq9QpQSh3HMYRhCLvdjjsNwwDn8xmOx6MEmqYBpRREUQSbzQbSNH0FjOOYJUkC+/0euq6Duq6hqiooy5KDfd9D0zQwDAPEcQxpmvI3yLLsBTCO4yiE4M5lWfKOQgh+kyzL+BvM8xxCCJ5zu91ClmXPAKXUyTAMsN/vuTMpCAKYpgm6roPz+QyXy4XHp9MJhBA85/F4hMPh8AxQSj0HwzBwZ1mWvLOiKGCeZx6TAgpSQApoTl3XzwD6nF3X8WakgBQQhBQ0TcMKSAG9AVJACmjO6XSCy+UCt9vtGaCUOtM0cWdSQJtO08QKSAG9ASkgBTSHFFyvV7jf788ApdTzPMN2u+XOpIA2JQWkgBSQAprz8fEBTdPA4/F4BiilXkII/nWpgBSQAlJACkgBKaA5t9uN53x9fb0CDnwv/AN8CzAAG5pLZRsaN0EAAAAASUVORK5CYII=)](https://docs.disnake.dev)


## 🌟 Особенности
- 🛠️ Полная кастомизация под ваш сервер
- 📊 Встроенная система тикетов и управления обращениями
- 👨💻 Поддержка персонала через таблицу staff_list
- ⚡ Быстрые команды для администрирования
- 📁 SQLite база данных с простым управлением

## 📥 Установка

### Требования
- Python 3.8+
- [Discord Bot Token](https://discord.com/developers/applications)
- SQLite Browser (рекомендуется [DB Browser](https://sqlitebrowser.org/))

### Пошаговая инструкция
1. **Установите зависимости**:
  ```pip install -r requirements.txt```
2. **Настройте токен бота:**
  Вставьте ваш Discord токен в файл yootoken.txt
3. **Запустите бота:**
  ```python main.py```

## ⚙️ Конфигурация

**База данных**
1. Откройте `database.db` в SQLite Browser
2. Настройте таблицы:
   **settings** - основные параметры сервера
   **staff_list** - список сотрудников (формат: username | ticket_name | user_id | role | closed_tickets | mention)
   
**Быстрые команды**

Отредактируйте `fastcommands.py` или обновите список `default_commands`:
```
default_commands = [
    {"command": "!help", "response": "Список доступных команд..."},
    # Добавьте свои команды
]
```

## 🔧 Кастомизация

*Для глубокой настройки функционала требуется правка исходного кода.
Мы можем помочь с индивидуальной настройкой!*

**📬 Контакты для заказа кастомизации:**
[**Telegram: @anarchowitz**](https://t.me/anarchowitz)

## 🛠️ Управление через Discord
Разработчики могут использовать: (с указаной role = dev в базе данных)
```
/settings
/date_stats
/stats
/status
/sum
/ticket_msg
```
и команды сотрудников.
Сотрудники могут использовать: (с указаной role = staff в базе данных)
```
/ticket_fix
/ticket_ping
/ticket_ban
/ticket_unban
/fastcommands
```
## 📄 Лицензия

Проект распространяется под лицензией MIT License.
При поддержке [yooma.su](https://yooma.su/ru)

# [![Star on GitHub](https://img.shields.io/github/stars/anarchowitz/YooTick.svg?style=social)](https://github.com/anarchowitz/YooTick/stargazers)

