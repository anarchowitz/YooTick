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
        
        if self.moderator.check_message(message):
            await message.delete()
            await message.channel.send("**[Anti-AD]**  Пользователь был **наказан** из-за подозрения в спаме!", delete_after=5)
            logger.info(f"[FCOMMAND] Сообщение {message.id} удалено из-за подозрения в спаме!")
            embed = disnake.Embed(
                title="Нарушение правил чата",
                description="Ваше сообщение было распознано как **реклама/спам**.",
                color=0xFF3030
            )
            embed.add_field(
                name=" Принятая мера",
                value="Вам выдан **мут на 1 день** (24 часа)",
                inline=False
            )
            embed.add_field(
                name="> Что делать?",
                value="• Если это ошибка - обратитесь к <@1352144578395766825> в личные сообщенния с пометкой (#ботмут)\n• Ожидайте ответа",
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
            self.db.cursor.execute("SELECT dev_channel_id FROM settings")
            dev_channel_id = self.db.cursor.fetchone()
            if dev_channel_id is not None:
                dev_channel_id = dev_channel_id[0]
                channel = await self.bot.fetch_channel(dev_channel_id)
                await channel.send(f"Пользователь {message.author.mention} получил таймаут на 1 день за спам!\nКанал: {message.channel.mention}\nСообщение: ```{message.content}```")
        
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