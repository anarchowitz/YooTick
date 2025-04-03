import disnake, random, logging
from datetime import datetime as dt
from disnake.ext import commands
from database import Database
from moderator import Moderator

logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

class FastCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
        self.moderator = Moderator()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        logger.info(f"[FCOMMAND] Сообщение из голосового канала: {message.content}")
        if self.moderator.check_message(message):
            await message.delete()
            await message.channel.send("**[Anti-AD]**  Пользователь был **наказан** из-за подозрения в спаме!", delete_after=5)
            logger.info(f"[FCOMMAND] Сообщение {message.id} удалено из-за подозрения в спаме!")
            embed = disnake.Embed(
                title=" Нарушение правил чата",
                description="Ваше сообщение было распознано как **реклама/спам**.",
                color=0xFF3030
            )
            embed.add_field(
                name=" Принятая мера",
                value="```Вам выдан мут на 1 день (24 часа)```",
                inline=False
            )
            embed.add_field(
                name="ℹ Что делать?",
                value="• Если это ошибка - обратитесь к модерации\n• Ожидайте окончания наказания",
                inline=False
            )
            embed.set_footer(text="Пожалуйста, соблюдайте правила нашего сообщества")
            embed.set_author(name='Yooma Anti-AD', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
            try:
                await message.author.send(embed=embed)
            except disnake.HTTPException as e:
                if e.status == 403:
                    logger.error(f"[FCOMMAND] Не удалось отправить сообщение пользователю {message.author.id} из-за блокировки личных сообщений")
            await message.author.timeout(duration=86400, reason="[Anti-AD] - Detected spamming")
            channel = await self.bot.fetch_channel(1090347336145838242)
            await channel.send(f"Пользователь {message.author.mention} получил таймаут на 1 день за спам!\nСообщение: ```{message.content}```")

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
            embed = disnake.Embed(title="", description=f"Твоя вторая половинка: **{self.bot.user.name}**\nВ браке: **{marriage_time}**", color=None)
            embed.set_author(name="Отношения", icon_url="https://images-ext-1.discordapp.net/external/77lMDVf_aAExffQnk8AypZRzPP7Q4hHVZzMYzRbnnNk/https/cdn.discordapp.com/emojis/928628212437778472.png")
            embed.set_thumbnail(url=message.author.avatar.url)
            embed.set_footer(text=f"{message.guild.name} • {dt.now().strftime('%d.%m.%Y')}")
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
                "Я не уверена, что мы совместимы 🤔",
                "Мне кажется, что мы слишком разные 😳",
                "Я уже занята, мой любимый ревнует.. 😳"
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