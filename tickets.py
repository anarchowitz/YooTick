import disnake
from disnake.ext import commands
from database import Database

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
        
    @commands.slash_command(description="[DEV] - Сообщение создания тикетов")
    async def ticketmsg(self, inter):
        self.db.cursor.execute("""
            SELECT embed_color, category_id, ticket_channel_id FROM settings WHERE guild_id = ?
        """, (inter.guild.id,))
        settings = self.db.cursor.fetchone()

        if settings is None:
            await inter.response.send_message("Настройки не найдены!")
            return

        embed_color = disnake.Color(int(settings[0].lstrip('#'), 16))
        category_id = settings[1]
        channel_id = settings[2]

        category = inter.guild.get_channel(category_id)
        channel = inter.guild.get_channel(channel_id)

        if category is None or channel is None:
            await inter.response.send_message("Категория или канал не найдены!")
            return

        embed = disnake.Embed(
            title="Создание обращения в клиентскую поддержку",
            description="Мы настоятельно рекомендуем **подробно** описывать ваши просьбы или проблемы. Это поможет нам оказать вам **быструю и эффективную помощь**.\n\n"
            "▎Важные моменты:\n"
            "- Не открывайте тикеты, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
            "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
            "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
            "**Несоблюдение этих правил может привести к наказанию**.",
            color=embed_color)
        embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
        embed.set_thumbnail(url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")

        view = disnake.ui.View()
        button = disnake.ui.Button(label="Создать обращение", emoji="📨", custom_id="create_ticket", style=disnake.ButtonStyle.primary)
        view.add_item(button)

        await channel.send(embed=embed, view=view)
        await inter.response.send_message("Отправил сообщение.", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        if inter.data.custom_id == "create_ticket":
            self.db.cursor.execute("""
                SELECT embed_color, category_id, ticket_channel_id, staff_roles_id FROM settings WHERE guild_id = ?
            """, (inter.guild.id,))
            settings = self.db.cursor.fetchone()
            if settings is None:
                await inter.response.send_message("Настройки не найдены!")
                return

            embed_color = disnake.Color(int(settings[0].lstrip('#'), 16))
            self.db.cursor.execute("SELECT category_id FROM settings WHERE guild_id = ?", (inter.guild.id,))
            category_id = self.db.cursor.fetchone()[0]

            category = inter.guild.get_channel(category_id)

            if category is None:
                await inter.response.send_message("Категория не найдена!")
                return

            self.db.cursor.execute("SELECT counter_tickets FROM settings WHERE guild_id = ?", (inter.guild.id,))
            counter_tickets = self.db.cursor.fetchone()[0]
            self.db.cursor.execute("UPDATE settings SET counter_tickets = ? WHERE guild_id = ?", (counter_tickets + 1, inter.guild.id))
            self.db.conn.commit()
            thread = await inter.channel.create_thread(name=f"ticket-{counter_tickets + 1}", type=disnake.ChannelType.private_thread)
            await thread.edit(invitable=False)
            await inter.response.send_message(f":tickets: \ **Ваше обращение был создано** - {thread.mention}", ephemeral=True)
            embed = disnake.Embed(
                title="Создание обращения в клиентскую поддержку",
                description="Мы настоятельно рекомендуем **подробно** описывать ваши просьбы или проблемы. Это поможет нам оказать вам **быструю и эффективную помощь**.\n\n"
                "▎Важные моменты:\n"
                "- Не открывайте тикеты, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
                "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
                "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
                "**Несоблюдение этих правил может привести к наказанию**.",
                color=embed_color)
            embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
            embed.set_thumbnail(url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
            await thread.send(embed=embed)
            await thread.add_user(inter.author)
            

def setuptickets(bot):
    bot.add_cog(Tickets(bot))