import disnake
from disnake.ext import commands
from database import Database
from commands import setup

intents = disnake.Intents.default() 
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

db = Database("database.db")

@bot.event
async def on_ready():
    print(f"Бот запущен /|\ {bot.user}\n_________________")
    db.create_settings_table()
    db.create_staff_list_table()
    db.create_created_tickets_table()

if __name__ == "__main__":
    setup(bot)
    bot.run("MTI3Mzk1NzgzNTI1MTc4MTY0Mg.GgCwOB.0z4FATO1eYK1d7uoDQxTI6ZBrbfS85x-rCghrc")