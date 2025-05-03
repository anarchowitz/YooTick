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

    @staticmethod
    def check_staff_permissions(inter, required_role):
        db = Database("database.db")
        db.cursor.execute("SELECT * FROM staff_list WHERE username = ? AND user_id = ?", (inter.author.name, inter.author.id))
        staff_member = db.cursor.fetchone()
        
        if staff_member is None:
            return False
        if staff_member[4] != required_role:
            return False
        
        return True

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
            button = disnake.ui.Button(
                label="Размутить", 
                style=disnake.ButtonStyle.green, 
                custom_id=f"unmute_{message.author.id}_{message.channel.id}"
            )
            view = disnake.ui.View()
            view.add_item(button)
            self.db.cursor.execute("SELECT dev_channel_id FROM settings")
            dev_channel_id = self.db.cursor.fetchone()
            if dev_channel_id is not None:
                dev_channel_id = dev_channel_id[0]
                channel = await self.bot.fetch_channel(dev_channel_id)
                await channel.send(f"Пользователь {message.author.mention} получил таймаут на 1 день за спам!\nКанал: {message.channel.mention}\nСообщение: ```{message.content}```", view=view)
        
        if message.content.startswith('.'):
            if not (self.check_staff_permissions(message, "staff") or self.check_staff_permissions(message, "dev")):
                return
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

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if interaction.component.custom_id.startswith("unmute_"):

            _, user_id, channel_id = interaction.component.custom_id.split('_')
            user_id = int(user_id)
            channel_id = int(channel_id)
            
            member = interaction.guild.get_member(user_id)
            if member:
                await member.timeout(duration=None, reason="Ошибочный мут - размучен модератором")
                
                try:
                    embed = disnake.Embed(
                        title="Снятие наказания",
                        description="Ваш мут был снят модератором.",
                        color=0x00FF00
                    )
                    embed.add_field(
                        name="Причина",
                        value="Наказание было выдано ошибочно",
                        inline=False
                    )
                    embed.set_author(name='Yooma Anti-AD', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                    await member.send(embed=embed)
                except disnake.HTTPException:
                    pass

                await interaction.message.delete()
                
                await interaction.response.send_message(
                    f"Пользователь {member.mention} был успешно размучен.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Пользователь не найден на сервере.",
                    ephemeral=True
                )

def setupfastcommands(bot):
    bot.add_cog(FastCommand(bot))