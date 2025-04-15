import disnake, asyncio, datetime, logging
from disnake.ext import commands
from database import Database

logger = logging.getLogger('bot')
logger.setLevel(logging.ERROR)

class Freeze(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
        self.embed_color = disnake.Colour.from_rgb(119, 137, 253)
        self.lock = asyncio.Lock()
        self.sender = None
        self.nickname = None
        self.steamid = None
        self.reason = None
        self.comment = None

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
    
    @commands.slash_command(description="[DEV] - freeze msg")
    async def freezemsg(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        
        embed = disnake.Embed(
            title="Заморозка",
            description=f"🔎 - Поиск заморозки по steamid\n❄️ - Заморозить пользователя",
            color=self.embed_color
        )
        embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
        view = disnake.ui.View()
        search_button = disnake.ui.Button(emoji="🔎", custom_id="search", style=disnake.ButtonStyle.gray)
        freeze_button = disnake.ui.Button(emoji="❄️", custom_id="freeze", style=disnake.ButtonStyle.gray)
        view.add_item(search_button)
        view.add_item(freeze_button)
        await inter.channel.send(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_button_click(self, inter):
        if inter.data.custom_id == "take_freeze":
            async with self.lock:
                await inter.message.delete()
                frozen_by = inter.author.name
                self.db.cursor.execute("INSERT INTO freeze_users (sender, frozen_by, nickname, steamid, reason, comment, frozen_at) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (inter.author.name, frozen_by, self.nickname, self.steamid, self.reason, self.comment, datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")))
                self.db.cursor.commit()
                embed = disnake.Embed(
                title="Заморозка",
                description=f"👨🏻‍💼 - Никнейм: {self.nickname}\n🌐 - [Ссылка на профиль](https://yooma.su/ru/profile/{self.steamid})\n❓ - Причина: {self.reason}\n💬 - Комментарий: {self.comment}\n\nПосле успешной заморозки, удалите сообщение для себя ↓",
                color=self.embed_color
                )
                embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                await inter.response.send_message(embed=embed, ephemeral=True)
        if inter.data.custom_id == "search":
            modal = disnake.ui.Modal(
                title="Поиск по steamid",
                custom_id="search_callback",
                components=[
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Стимайди",
                            placeholder="К примеру: 76561199231684717",
                            custom_id="steamid_input",
                            style=disnake.TextInputStyle.short,
                        )
                    ),
                ],
            )
            await inter.response.send_modal(modal)
        
        if inter.data.custom_id == "freeze":
            modal = disnake.ui.Modal(
                title="Заморозка",
                custom_id="freeze_process_callback",
                components=[
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Никнейм",
                            placeholder="К примеру: ivanzolo2004",
                            custom_id="nickname_input",
                            style=disnake.TextInputStyle.short,
                        )
                    ),
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Стимайди",
                            placeholder="К примеру: 76561199231684717",
                            custom_id="steamid_input",
                            style=disnake.TextInputStyle.short,
                        )
                    ),
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Причина",
                            placeholder="К примеру: Неадекватное поведение",
                            custom_id="reason_input",
                            style=disnake.TextInputStyle.long,
                        )
                    ),
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Комментарий",
                            placeholder="К примеру: Платно/Бесплатно/По ситуации",
                            custom_id="comment_input",
                            style=disnake.TextInputStyle.short,
                        )
                    ),
                ],
            )
            await inter.response.send_modal(modal)
        if inter.data.custom_id.startswith("record_"):
            db = Database("database.db")
            record_id = int(inter.data.custom_id.split("_")[1])
            db.cursor.execute("SELECT * FROM freeze_users WHERE id = ?", (record_id,))
            result = db.cursor.fetchone()
            
            embed = disnake.Embed(
                title="Информация по заморозке", 
                description=f"✍🏻 - Отправил форму: {result[1]}\n❄️ - Заморозил: **{result[2]}**\n👨🏻‍💼 - Никнейм: {result[3]}\n🌐 - [Ссылка на профиль](https://yooma.su/ru/profile/{result[4]})\n❓ - Причина: {result[5]}\n💬 - Комментарий: {result[6]}\n🕰️ - Дата заморозки: {result[7]}",
                color=self.embed_color
            )
            embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
            
            await inter.response.send_message(embed=embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.data.custom_id == "search_callback":
            db = Database("database.db")
            steamid = inter.text_values['steamid_input']
            db.cursor.execute("SELECT * FROM freeze_users WHERE steamid = ?", (steamid,))
            results = db.cursor.fetchall()
            
            if results:
                embed = disnake.Embed(
                    title="Результат поиска",
                    description="Список заморозок:\n\n" + "\n".join(f"{i+1}) {result[1]} - {result[7]}" for i, result in enumerate(results)),
                    color=self.embed_color
                )
                embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                
                view = disnake.ui.View()
                for i, result in enumerate(results):
                    button = disnake.ui.Button(label=f"Запись {i+1}", custom_id=f"record_{result[0]}")
                    view.add_item(button)
                
                await inter.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                await inter.response.send_message("Пользователь не найден", ephemeral=True)
        if inter.data.custom_id == "freeze_process_callback":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            self.sender = inter.author.name
            self.nickname = inter.text_values['nickname_input']
            self.steamid = int(inter.text_values['steamid_input'])
            self.reason = inter.text_values['reason_input']
            self.comment = inter.text_values['comment_input']
            
            embed = disnake.Embed(
                title="Заморозка",
                description=f"👨🏻‍💼 - Никнейм: {self.nickname}\n🌐 - [Ссылка на профиль](https://yooma.su/ru/profile/{self.steamid})\n❓ - Причина: {self.reason}\n💬 - Комментарий: {self.comment}",
                color=self.embed_color
            )
            embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")

            view = disnake.ui.View()
            take_freeze_button = disnake.ui.Button(emoji="❄️", label="Взять заморозку", custom_id="take_freeze", style=disnake.ButtonStyle.gray)
            view.add_item(take_freeze_button)

            await inter.response.send_message(embed=embed, view=view)
            
def setupfreeze(bot):
    bot.add_cog(Freeze(bot))