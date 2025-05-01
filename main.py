import disnake, datetime, logging
from disnake.ext import commands
from database import Database
from tickets import setuptickets
from commands import setupcommands
from fastcommands import setupfastcommands
from freeze import setupfreeze
from notifications import run_schedule

intents = disnake.Intents.default() 
intents.message_content = True
intents.guilds = True
intents.members = True
version = "3.5.8.1"
bot = commands.Bot(command_prefix="/", intents=intents, activity=disnake.Activity(type=disnake.ActivityType.listening, name=f"yooma.su | v{version}"))

db = Database("database.db")

@bot.event
async def on_ready():
    print(f"{bot.user} запущен\n Версия: {version}\n Пользователей: {len(bot.users)}\n Время запуска: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n_________________")
    db.create_settings_table()
    db.create_price_list_table()
    db.create_staff_list_table()
    db.create_created_tickets_table()
    db.create_date_stats_table()
    db.create_fast_commands_table()
    db.create_banned_users_table()
    db.create_freeze_users_table()
    if not db.cursor.execute("SELECT 1 FROM fast_commands LIMIT 1").fetchone():
        default_commands = [
            ('скинрейв', 'Форма выдачи токенов за регистрацию на скинрейве', 'Что бы мы вам помогли, уточните.\n1) Как давно вы зарегистрировались на SkinRave?\n2) Авторизировались ли вы под своим Steam аккаунтом?\n3) Ссылка на ваш аккаунт на сайте (yooma.su)\n4) Скриншот профиля на SkinRave. \n\n-# Отправил - {author}'),
            ('админчат', 'Форма о кратком гайде по отправлению сообщения в админчат кс2', 'Чтобы написать сообщение в админ-чат.\n1) Откройте командный чат в игре (по умолчанию клавиша "U").\n2) Начните своё сообщение с символа @\nНапример: @Привет \n\n-# Отправил - {author}'),
            ('ссылкасайт', 'Форма о кратком гайде по отправлению личной ссылки на профиль сайта', 'Чтобы получить ссылку на ваш профиль на сайте, выполните следующие шаги:\n1) Справа вверху нажмите на свой ник и аватарку (находится справа от баланса).\n2) В появившемся меню нажмите кнопку "Мой профиль".\n3) Скопируйте ссылку из адресной строки. \n\n-# Отправил - {author}'),
            ('обнова', 'Форма о том, что вышла обнова в кс и сервера не доступны', 'Последнее обновление CS2 сломало работу серверов. Нужно время, чтобы решить проблемы и баги. Спасибо за понимание 💕 \n\n-# Отправил - {author}'),
            ('жалоба', 'Форма о том, что жалоба передана в админ чат', 'Спасибо! Передали ваше обращение Администрации! \n\n-# Отправил - {author}'),
            ('баг', 'Форма о том, что информация о баге - передана разработчику', 'Спасибо! Передали информацию разработчику! \n\n-# Отправил - {author}'),
            ('коины', 'Форма о том, что делать с коинами', 'Коины используются на серверах для покупки различных игровых ценностей\nДля того чтобы их потратить используйте команду !shop на любом сервере нашего проекта\n\nЗа коины вы также можете покупать различные привилегии и артефакты, договариваясь с другими игроками в соответствии с правилами.\n[Ознакомьтесь с ними по следующей ссылке](https://yooma.su/ru/rules) \n\n-# Отправил - {author}'),
            ('соцсети', 'Форма о наших соцсетях', 'Все ссылки на наши актуальные соц. сети:\n\nDiscord: <https://ds.yooma.su>\nTelegram: <https://t.me/yoomasu>\nВКонтакте: <https://vk.com/yoomasu>\n\n-# Отправил - {author}'),
            ('промоввод', 'Форма о том, как ввести промокод.', 'Чтобы активировать промокод, вам нужно нажать на свою аватарку в правом верхнем углу сайта и выбрать "ввести промокод".\n\n-# Отправил - {author}'),
            ('блекджек', 'Форма о том, как играть в блекджек.', 'Чтобы открыть игру, вам нужно написать команду !bj в чат игры на сервере\nПоcле этого в чате появится ссылка на игру. Вам необходимо выделить ее мышкой и нажать ПКМ, затем "Копировать выделенный текст".\nДалее зайти в обычный браузер (или в Steam браузер) и ввести эту ссылку туда, откроется игра\n\n-# Отправил - {author}'),
            ('скины', 'Форма о том, как поставить скины на сервере.', 'Для настройки скинов на нашем сервере, вам необходимо выполнить несколько шагов:\n\n1) Авторизуйтесь через свой стим профиль на нашем сайте.\n2) В правом верхнем углу нажмите на иконку своего профиля.\n3) Перейдите в раздел скинченджер, тут вы как раз и можете настроить скины на все оружия!\n\nНе забывайте, что все функции скинченджера раскрываются с вип-привилегиями.\nПодробнее узнавайте здесь: https://yooma.su/ru/shop/0 \n\n-# Отправил - {author}'),
            ('заявкамодер', 'Форма о том, как подать заявку на модератора.', 'Для того чтобы подать заявку на модератора, вам нужно выполнить следующие шаги:\n1) Авторизуйтесь на нашем сайте через свой стим профиль.\n2) В правом верхнем углу нажмите на иконку своего профиля.\n3) Перейдите в раздел модерация, где и сможете подать заявку на модератора проекта.\n\nЕсли вы уже являетесь администратором нашего проекта, то перейдите в раздел модерирование, и вы увидите: "заявка на модератора".\n\nНеобходимые условия для становления модератором:\n1) Вы должны быть не младше 16 лет.\n2) На вашем аккаунте должно быть наиграно не менее 50 часов. \n\n-# Отправил - {author}'),
            ('репортгайд', 'Форма о том, как смотреть репорты имея права администратора','Для просмотра репортов, отправляемых игроками на сервере, вам необходим сделать следующее:\n\n1) Справа сверху нажмите на иконку своего профиля.\n2) Перейдите в "Модерирование".\n3) Затем слева у вас будет раздел "тикеты", где вы и сможете просматривать их. \n\n-# Отправил - {author}'),
            ('пополнение', 'Форма о дополнительных способах оплаты через Telegram-бота YoomaPay', 'Помимо стандартных способов оплаты, вы можете пополнить баланс через нашего Telegram-бота с помощью альтернативных методов:\n\n1) Telegram Stars - оплата внутренней валютой Telegram\n2) Криптовалюта (через CryptoBot) - Bitcoin, USDT и другие\n3) FunPay - популярная площадка для игровых платежей\n\nДля оплаты перейдите в нашего бота: https://t.me/yoomapay_bot\n\n-# Отправил - {author}'),
            ('тикеты', 'Форма о том, как посмотреть меню тикетов на сайте', 'Для просмотра репортов, отправляемых игроками на сервере, вам необходим сделать следующее:\n\n1) Справа сверху нажмите на иконку своего профиля.\n2) Перейдите в "Модерирование".\n3) Затем слева у вас будет раздел "тикеты", где вы и сможете просматривать их\n\n-# Отправил - {author}'),
        ]
        db.cursor.executemany(
            "INSERT INTO fast_commands (command_name, description, response) VALUES (?, ?, ?)",
            default_commands
        )
        db.conn.commit()
        print("Импортед дефаулт фаст коммандс епта")
    db.cursor.execute("SELECT dev_channel_id FROM settings")
    dev_channel_id = db.cursor.fetchone()
    if dev_channel_id is not None:
        dev_channel_id = dev_channel_id[0]
        channel = await bot.fetch_channel(dev_channel_id)
        await channel.send(f"(re)started!")

if __name__ == "__main__":
    logger = logging.getLogger('bot')
    logger.setLevel(logging.ERROR)
    logger.disabled = False # True or False
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('yoologger.log', encoding='cp1251'), # encoding='utf-8' (if u run from your pc) | encoding='cp1251' (if u run from vps)
            logging.StreamHandler()
        ]
    )
    setuptickets(bot)
    setupcommands(bot)
    setupfastcommands(bot)
    setupfreeze(bot)
    with open('yootoken.txt', 'r') as file:
        lines = file.readlines()
        token = lines[0].strip()
    bot.loop.create_task(run_schedule(bot))
    bot.run(token)