import disnake, random, logging
from datetime import datetime as dt
from disnake.ext import commands
from database import Database

logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

class FastCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        def calculate_marriage_time():
            start_date = dt(2024, 8, 17, 0, 41)
            current_date = dt.now()
            delta = current_date - start_date
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds // 60) % 60
            seconds = delta.seconds % 60
            return f"{days} дней {hours} часов {minutes} минут {seconds} секунд"
        
        if message.author.id == 444574234564362250 and message.content.startswith(f"a.marry {message.guild.get_member(self.bot.user.id).mention}"):
            marriage_time = calculate_marriage_time()
            embed = disnake.Embed(title="Отношения", description=f"Твоя вторая половинка: **{self.bot.user.name}**\nВ браке: **{marriage_time}**", color=None)
            embed.set_thumbnail(url=message.author.avatar.url)
            embed.set_footer(text=f"{message.guild.name} • {dt.now().strftime('%d.%m.%Y %H:%M')}")
            await message.channel.send(embed=embed)
        elif message.content.startswith(f"a.marry {message.guild.get_member(self.bot.user.id).mention}"):
            answers = [
                "Это так сложно... прости я вынуждена отказаться 😔",
                "Я занята так-то эмм... 😒",
                "Наша любовь не взаимна... прости.. 💔",
                "Я не готова к такому большому шагу... 😟",
                "Мне нужно время подумать... 🤔",
                "Я не уверена, что мы готовы к браку...  😕",
                "Ты слишком милый, но я не готова к браку 😊",
                "Я люблю тебя, но не в этом смысле :worried: 😳",
                "Мы можем быть друзьями, но не мужем и женой 👫",
                "Я не готова к такой ответственности 😬",
                "Мне нужно время подумать о нашей будущем 🤝",
                "Я не уверена, что мы совместимы 🤔"
            ]
            await message.reply(random.choice(answers))
        if message.content.startswith('.'):
            command = message.content.split()[0][1:].lower()
            
            self.db.cursor.execute("SELECT response FROM fast_commands WHERE command_name = ?", (command,))
            result = self.db.cursor.fetchone()
            
            if result:
                await message.delete()
                response = result[0].replace("{author}", message.author.name)
                await message.channel.send(response)
                logger.info(f"[FCOMMAND] Быстрая команда - '{command}' использована пользователем {message.author.name}")
            else:
                logger.info(f"[FCOMMAND] Неизвестная команда '{command}' использована пользователем {message.author.name}")

def setupfastcommands(bot):
    bot.add_cog(FastCommand(bot))
