import disnake, logging, re
from disnake.ext import commands
from database import Database

logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
        self.keywords = [
            r"cybershoke\.net", # ad
            r"cs2red\.ru", # ad
            r"onetake-cs2\.ru", # ad
            r"discord\.com\/invite\/", # spam
            r"discord\.com\/invites\/", # spam
            r"discord\.io\/", # spam
            r"discord\.me\/", # spam
            r"youtude\.net\/", # scam link
            r"lllyoutube\.com\/", # scam link
            r"onlyfans", # spam
            r"free", # spam
            r"gift", # spam
            r"giveaway", # spam
            r"join", # spam
            r"server", # spam
            r"link", # spam
            r"leaks", # spam
            r"qr code", # spam
            r"exclusive", # spam
            r"personal", # spam
            r"wet", # spam
            r"com server", # spam
            r"DM me", # spam
            r"@everyone" # spam / mention all
        ]
        self.nsfw_keywords = [
            r"porn", # 18+
            r"sex", # 18+
            r"xxx", # 18+
            r"nsfw", # 18+
            r"порно", # 18+
            r"секс", # 18+
            r"оргазм", # 18+
            r"кримпат", # 18+
            r"кримпатч", # 18+
            r"crim", # 18+
            r"crimpat", # 18+
            r"gayporno", # 18+
            r"lesbian", # 18+
            r"dick", # 18+
            r"vagina", # 18+
            r"crimpatch" # 18+
        ]
        self.whitelist = [
            r"free ping", # keyword
            r"freeping", # keyword
            r"free mirage", # keyword
            r"xone_free", # keyword
            r"xone free", # keyword
            r"freeqn", # keyword
            r"naimfree", # keyword
            r"rawetrip", # keyword
            r"tenor\.com", # link
            r"yooma\.su" # link
        ]
        self.url_pattern = re.compile(r'https?://\S+', re.IGNORECASE)
        self.patterns = [re.compile(keyword, re.IGNORECASE) for keyword in self.keywords]
        self.nsfw_patterns = [re.compile(keyword, re.IGNORECASE) for keyword in self.nsfw_keywords]
        self.whitelist_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.whitelist]

    async def check_message(self, message):
        if not isinstance(message.channel, (disnake.TextChannel, disnake.Thread)):
            return False
        
        self.db.cursor.execute("SELECT dev_channel_id FROM settings")
        dev_channel_id = self.db.cursor.fetchone()

        self.db.cursor.execute("SELECT * FROM staff_list WHERE user_id = ?", (message.author.id,))
        staff_member = self.db.cursor.fetchone()
        if staff_member is not None:
            return False
        if message.author.bot:
            return False
            
        for nsfw_pattern in self.nsfw_patterns:
            if nsfw_pattern.search(message.content):
                try:
                    await message.delete()
                except disnake.NotFound:
                    logger.warning(f"Сообщение {message.id} уже удалено")
                    return True
                except disnake.Forbidden:
                    logger.error(f"Нет прав для удаления сообщения {message.id}")
                    return True
                
                await message.channel.send("**[Anti-NSFW]** Пользователь был **наказан** за 18+ контент!", delete_after=5)
                logger.info(f"[FCOMMAND] Сообщение {message.id} удалено за 18+ контент!")
                
                embed = disnake.Embed(
                    title="Нарушение правил чата",
                    description="Ваше сообщение содержало **18+ контент**.",
                    color=0xFF3030
                )
                embed.add_field(
                    name="Принятая мера",
                    value="Вам выдан **мут на 6 часов**",
                    inline=False
                )
                embed.add_field(
                    name="> Что делать?",
                    value="• Если это ошибка - обратитесь к <@1352144578395766825> в личные сообщения с пометкой (#ботмут)\n• Ожидайте ответа",
                    inline=False
                )
                embed.set_footer(text="Пожалуйста, соблюдайте правила нашего сообщества")
                embed.set_author(name='Yooma Anti-NSFW', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                
                try:
                    await message.author.send(embed=embed)
                except disnake.HTTPException as e:
                    if e.status == 403:
                        logger.error(f"[FCOMMAND] Не удалось отправить сообщение пользователю {message.author.id} из-за блокировки личных сообщений")
                
                try:
                    await message.author.timeout(duration=21600, reason="[Anti-NSFW] - Detected 18+ content")
                except disnake.Forbidden:
                    logger.error(f"Нет прав для выдачи таймаута пользователю {message.author.id}")
                    return True
                
                button = disnake.ui.Button(
                    label="Размутить", 
                    style=disnake.ButtonStyle.green, 
                    custom_id=f"unmute_{message.author.id}_{message.channel.id}"
                )
                view = disnake.ui.View()
                view.add_item(button)
                
                if dev_channel_id is not None:
                    dev_channel_id = dev_channel_id[0]
                    try:
                        channel = await self.bot.fetch_channel(dev_channel_id)
                        await channel.send(
                            f"Пользователь {message.author.mention} получил таймаут на 6 часов за 18+ контент!\n"
                            f"Канал: {message.channel.mention}\n"
                            f"Сообщение: ```{message.content}```",
                            view=view
                        )
                    except disnake.NotFound:
                        logger.error(f"Канал с ID {dev_channel_id} не найден")
                    except disnake.Forbidden:
                        logger.error(f"Нет прав для отправки сообщений в канал {dev_channel_id}")
                
                return True
        
        urls = self.url_pattern.findall(message.content)
        if urls:
            dev_channel_id = dev_channel_id[0]
            try:
                report_channel = await self.bot.fetch_channel(dev_channel_id)
                if report_channel:
                    await report_channel.send(
                        f"Пользователь {message.author.mention} отправил подозрительную ссылку!\n"
                        f"Канал: {message.channel.mention}\n"
                        f"Сообщение: ```{message.content[:1000]}```",
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке ссылок в канал отчетов: {e}")
        
        for whitelist_pattern in self.whitelist_patterns:
            if whitelist_pattern.search(message.content):
                return False

        for pattern in self.patterns:
            if pattern.search(message.content):
                try:
                    await message.delete()
                except disnake.NotFound:
                    logger.warning(f"Сообщение {message.id} уже удалено")
                    return True
                except disnake.Forbidden:
                    logger.error(f"Нет прав для удаления сообщения {message.id}")
                    return True
                
                await message.channel.send("**[Anti-AD]** Пользователь был **наказан** из-за подозрения в спаме!", delete_after=5)
                logger.info(f"[FCOMMAND] Сообщение {message.id} удалено из-за подозрения в спаме!")
                
                embed = disnake.Embed(
                    title="Нарушение правил чата",
                    description="Ваше сообщение было распознано как **реклама/спам**.",
                    color=0xFF3030
                )
                embed.add_field(
                    name="Принятая мера",
                    value="Вам выдан **мут на 1 день** (24 часа)",
                    inline=False
                )
                embed.add_field(
                    name="> Что делать?",
                    value="• Если это ошибка - обратитесь к <@1352144578395766825> в личные сообщения с пометкой (#ботмут)\n• Ожидайте ответа",
                    inline=False
                )
                embed.set_footer(text="Пожалуйста, соблюдайте правила нашего сообщества")
                embed.set_author(name='Yooma Anti-AD', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                
                try:
                    await message.author.send(embed=embed)
                except disnake.HTTPException as e:
                    if e.status == 403:
                        logger.error(f"[FCOMMAND] Не удалось отправить сообщение пользователю {message.author.id} из-за блокировки личных сообщений")
                
                try:
                    await message.author.timeout(duration=86400, reason="[Anti-AD] - Detected spamming")
                except disnake.Forbidden:
                    logger.error(f"Нет прав для выдачи таймаута пользователю {message.author.id}")
                    return True
                
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
                    try:
                        channel = await self.bot.fetch_channel(dev_channel_id)
                        await channel.send(
                            f"Пользователь {message.author.mention} получил таймаут на 1 день за спам!\n"
                            f"Канал: {message.channel.mention}\n"
                            f"Сообщение: ```{message.content}```",
                            view=view
                        )
                    except disnake.NotFound:
                        logger.error(f"Канал с ID {dev_channel_id} не найден")
                    except disnake.Forbidden:
                        logger.error(f"Нет прав для отправки сообщений в канал {dev_channel_id}")
                
                return True
        
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.check_message(message)   

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if interaction.component.custom_id.startswith("unmute_"):
            _, user_id, channel_id = interaction.component.custom_id.split('_')
            user_id = int(user_id)
            channel_id = int(channel_id)
            
            member = interaction.guild.get_member(user_id)
            if member:
                try:
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
                except disnake.Forbidden:
                    await interaction.response.send_message(
                        "У меня нет прав для снятия мута с этого пользователя.",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "Пользователь не найден на сервере.",
                    ephemeral=True
                )

def setupmoderator(bot):
    bot.add_cog(Moderator(bot))