# 🎟️ YooTick - Discord Ticket Bot

**Лучшая бесплатная замена платным Akemi (звонки) и TicketTool (тикеты)**  
*Полностью настраиваемый бот для управления тикетами на вашем Discord-сервере*

[![Telegram Contact](https://img.shields.io/badge/Contact-Telegram-blue?logo=telegram)](https://t.me/anarchowitz)
[![RU/EU Support](https://img.shields.io/badge/Support-RU%2FEU-orange)](https://yooma.su)

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
