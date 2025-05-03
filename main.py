import disnake, datetime, logging
from disnake.ext import commands
from database import Database
from tickets import setuptickets
from commands import setupcommands
from fastcommands import setupfastcommands
from freeze import setupfreeze
from notifications import run_schedule
from moderator import setupmoderator

intents = disnake.Intents.default() 
intents.message_content = True
intents.guilds = True
intents.members = True
version = "3.5.8.4"
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
    setupmoderator(bot)
    with open('yootoken.txt', 'r') as file:
        lines = file.readlines()
        token = lines[0].strip()
    bot.loop.create_task(run_schedule(bot))
    bot.run(token)