# 🎟️ YooTick - Discord Ticket Bot

**Лучшая бесплатная замена платным Akemi (обращение) и TicketTool (тикеты)**  
*Полностью настраиваемый бот для управления тикетами на вашем Discord-сервере*

[![Sponsored By](https://img.shields.io/badge/Sponsored_By-yooma.su-FF6F61?logo=github-sponsors)](https://yooma.su)

[![Telegram Contact](https://img.shields.io/badge/Contact-Telegram-blue?logo=telegram)](https://t.me/anarchowitz)
[![RU Language](https://img.shields.io/badge/Language-RU-red)](https://yooma.su)
[![Open Source](https://img.shields.io/badge/License-MIT-yellow?logo=open-source-initiative)](https://opensource.org/licenses/MIT)

[![SQLite](https://img.shields.io/badge/SQLite-✓-003B57?logo=sqlite)](https://sqlite.org)
[![Python](https://img.shields.io/badge/Python-✓-3776AB?logo=python)](https://python.org)
[![Disnake](https://img.shields.io/badge/Disnake-✓-5865F2?logo=discord)](https://docs.disnake.dev)

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
и команды для всех
```
/ping
```
## 📄 Лицензия

Проект распространяется под лицензией [MIT License](https://github.com/Anarchowitz/YooTick/blob/main/LICENSE).
При поддержке [yooma.su](https://yooma.su/ru)

# [![Star on GitHub](https://img.shields.io/github/stars/anarchowitz/YooTick.svg?style=social)](https://github.com/anarchowitz/YooTick/stargazers)

