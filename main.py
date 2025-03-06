import disnake
from disnake.ext import commands
from database import Database
from tickets import setuptickets
from commands import setupcommands
from fastcommands import setupfastcommands

intents = disnake.Intents.default() 
intents.message_content = True
version = "3.0"
bot = commands.Bot(command_prefix="/", intents=intents, activity=disnake.Activity(type=disnake.ActivityType.streaming, name=f"yooma.su | v{version}"))

db = Database("database.db")


@bot.event
async def on_ready():
    print(f"Бот запущен / {bot.user}\n_________________")
    db.create_price_list_table()
    db.create_settings_table()
    db.create_staff_list_table()
    db.create_created_tickets_table()
    db.create_date_stats_table()
    db.create_fast_commands_table()
    db.create_banned_users_table()
    db.cursor.execute("SELECT 1 FROM fast_commands LIMIT 1")
    if not db.cursor.fetchone():
        default_commands = [
    ('скинрейв', 'Форма выдачи токенов за регистрацию на скинрейве', 'Что бы мы вам помогли, уточните.\n1) Как давно вы зарегистрировались на SkinRave?\n2) Авторизировались ли вы под своим Steam аккаунтом?\n3) Ссылка на ваш аккаунт на сайте (yooma.su)\n4) Скриншот профиля на SkinRave. \n\n-# Отправил - {author}'),
    ('админчат', 'Форма о кратком гайде по отправлению сообщения в админчат кс2', 'Чтобы написать сообщение в админ-чат.\n1) Откройте командный чат в игре (по умолчанию клавиша "U").\n2) Начните своё сообщение с символа @\nНапример: @Привет \n\n-# Отправил - {author}'),
    ('ссылкасайт', 'Форма о кратком гайде по отправлению личной ссылки на профиль сайта', 'Чтобы получить ссылку на ваш профиль на сайте, выполните следующие шаги:\n1) Справа вверху нажмите на свой ник и аватарку (находится справа от баланса).\n2) В появившемся меню нажмите кнопку "Мой профиль".\n3) Скопируйте ссылку из адресной строки. \n\n-# Отправил - {author}'),
    ('обнова', 'Форма о том, что вышла обнова в кс и сервера не доступны', 'Последнее обновление CS2 сломало работу серверов. Нужно время, чтобы решить проблемы и баги. Спасибо за понимание 💕 \n\n-# Отправил - {author}'),
    ('жалоба', 'Форма о том, что жалоба передана в админ чат', 'Спасибо! Передали ваше обращение Администрации! \n\n-# Отправил - {author}'),
    ('баг', 'Форма о том, что информация о баге - передана разработчику', 'Спасибо! Передали информацию разработчику! \n\n-# Отправил - {author}'),
    ('коины', 'Форма о том, что делать с коинами', 'Коины используются на серверах.\nДля того чтобы их потратить используйте команду !shop на любом сервере проекта. \n\n-# Отправил - {author}'),
    ('соцсети', 'Форма о наших соцсетях', 'Все ссылки на наши актуальные соц. сети:\n\nDiscord: <https://ds.yooma.su>\nTelegram: <https://t.me/yoomasu>\nВКонтакте: <https://vk.com/yoomasu>\n\n-# Отправил - {author}'),
    ('промоввод', 'Форма о том, как ввести промокод.', 'Чтобы активировать промокод, вам нужно нажать на свою аватарку в правом верхнем углу сайта и выбрать "ввести промокод".\n\n-# Отправил - {author}'),
    ('блекджек', 'Форма о том, как играть в блекджек.', 'Чтобы открыть игру, вам нужно написать команду !bj в чат игры на сервере\nПоcле этого в чате появится ссылка на игру. Вам необходимо выделить ее мышкой и нажать ПКМ, затем "Копировать выделенный текст".\nДалее зайти в обычный браузер (или в Steam браузер) и ввести эту ссылку туда, откроется игра\n\n-# Отправил - {author}')
]
        db.cursor.executemany(
            "INSERT INTO fast_commands (command_name, description, response) VALUES (?, ?, ?)",
            default_commands
        )
        db.conn.commit()
        print("Импортед дефаулт фаст коммандс епта")

if __name__ == "__main__":
    setuptickets(bot)
    setupcommands(bot)
    setupfastcommands(bot)
    bot.run("MTI3Mzk1NzgzNTI1MTc4MTY0Mg.GgCwOB.0z4FATO1eYK1d7uoDQxTI6ZBrbfS85x-rCghrc") 