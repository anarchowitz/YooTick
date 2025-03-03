import disnake, asyncio, datetime
from disnake.ext import commands
from database import Database

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
    
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
    
    @commands.slash_command(description="[DEV] - Сообщение создания тикетов")
    async def ticketmsg(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        self.db.cursor.execute("""
            SELECT embed_color, category_id, ticket_channel_id 
            FROM settings 
            WHERE guild_id = ?
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
        self.db.cursor.execute("""
            SELECT embed_color, category_id, ticket_channel_id FROM settings WHERE guild_id = ?
        """, (inter.guild.id,))
        settings = self.db.cursor.fetchone()

        if settings is None:
            await inter.response.send_message("Настройки не найдены!")
            return

        embed_color = disnake.Color(int(settings[0].lstrip('#'), 16))
        if inter.data.custom_id == "create_ticket":
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
            thread_number = int(thread.name.split("-")[1])
            self.db.cursor.execute("INSERT INTO created_tickets (thread_id, creator_username, creator_id, thread_number) VALUES (?, ?, ?, ?)", 
                                (thread.id, inter.author.name, inter.author.id, thread_number))
            self.db.conn.commit()

            embed = disnake.Embed(
                title="Спасибо за обращение в клиенсткую поддержку",
                description="Спасибо за ваше обращение. Пожалуйста, **опишите суть вашей проблемы подробнее**, чтобы мы могли оказать вам **наилучшее решение**.\n\n"
                "▎Важные моменты:\n"
                "- Не открывайте тикеты, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
                "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
                "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
                "**Несоблюдение этих правил может привести к наказанию**.",
                color=embed_color)
            embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
            embed.set_thumbnail(url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
            view = disnake.ui.View(timeout=None)
            take_button = disnake.ui.Button(label="Взять обращение", emoji="📝", custom_id="take_ticket", style=disnake.ButtonStyle.primary)
            close_button = disnake.ui.Button(label="Закрыть обращение", emoji="🔒", custom_id="close_ticket", style=disnake.ButtonStyle.danger)
            view.add_item(take_button)
            view.add_item(close_button)

            await thread.send(embed=embed, view=view)
            await thread.add_user(inter.author)
            
            self.db.cursor.execute("SELECT primetime FROM settings WHERE guild_id = ?", (inter.guild.id,))
            primetime = self.db.cursor.fetchone()[0]

            if primetime:
                start_time, end_time = primetime.split(" - ")
                start_hour, start_minute = map(int, start_time.split(":"))
                end_hour, end_minute = map(int, end_time.split(":"))

                current_time = datetime.datetime.now()
                current_hour = current_time.hour
                current_minute = current_time.minute

                if not (start_hour <= current_hour < end_hour or (start_hour == current_hour and start_minute <= current_minute) or (end_hour == current_hour and current_minute < end_minute)):
                    await thread.send(f"<@{inter.author.id}>, В данный момент нерабочее время, и время ответа может занять больше времени, чем обычно.\n Пожалуйста, оставайтесь на связи, и мы ответим вам, как только сможем.")

            await inter.response.send_message(f":tickets:  \ **Ваше обращение был создано** - {thread.mention}", ephemeral=True) # type: ignore

        if inter.data.custom_id == "take_ticket":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return

            self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            taken_ticket = self.db.cursor.fetchone()
            if taken_ticket is not None and taken_ticket[0] is not None:
                await inter.response.send_message("Этот тикет уже взят!", ephemeral=True)
                return

            self.db.cursor.execute("SELECT creator_username, thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            creator_username, thread_number = self.db.cursor.fetchone()
            
            embed = disnake.Embed(title="", description=f"Успешно взялся за тикет - {inter.author.mention}", color=0xF0C43F,)
            await inter.response.send_message(embed=embed)

            self.db.cursor.execute("UPDATE created_tickets SET taken_username = ? WHERE thread_id = ?", 
                                (inter.author.name, inter.channel.id))
            self.db.conn.commit()

            new_name = f"{inter.author.name}-ticket-{thread_number}"
            await inter.channel.edit(name=new_name)
        
        if inter.data.custom_id == "close_ticket":
            confirmation_embed = disnake.Embed(
                title="Подтверждение",
                description="Вы уверены что хотите закрыть тикет?",
                color=0xF0C43F,
            )
            view = disnake.ui.View(timeout=30)
            close_button = disnake.ui.Button(label="Закрыть", emoji='🔒', custom_id="confirm_close_ticket", style=disnake.ButtonStyle.red)
            close_with_reason_button = disnake.ui.Button(label='Закрыть с причиной', custom_id="confirm_close_with_reason_ticket", style=disnake.ButtonStyle.red, emoji='🔒')
            cancel_button = disnake.ui.Button(label="Отмена", emoji='🚫', custom_id="cancel_close_ticket", style=disnake.ButtonStyle.gray)
            view.add_item(close_button)
            view.add_item(close_with_reason_button)
            view.add_item(cancel_button)

            await inter.response.send_message(embed=confirmation_embed, view=view, ephemeral=True)
        
        if inter.data.custom_id == "confirm_close_ticket":
            self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            taken_username = self.db.cursor.fetchone()[0]
            user = inter.guild.get_member_named(taken_username)
            embed1 = disnake.Embed(
                description=f"Тикет был закрыт - {inter.user.mention}",
                color=0xF0C43F,
            )
            embed2 = disnake.Embed(
                description=f"Тикет будет удален через несколько секунд",
                color=0xF0C43F,
            )
            await inter.response.defer()
            await inter.channel.send(embed=embed1)
            await inter.channel.send(embed=embed2)

            self.db.cursor.execute("SELECT creator_id, creator_username, thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            creator_id, creator_username, thread_number = self.db.cursor.fetchone()
            creator = await self.bot.fetch_user(creator_id)
            if creator is not None:
                date_str = datetime.date.today().strftime("%d.%m.%Y")
                embed = disnake.Embed(title="Ваш тикет был закрыт",timestamp=datetime.datetime.now(),color=embed_color)
                embed.add_field(name=":id: Ticket ID", value=thread_number, inline=True)
                embed.add_field(name=":unlock: Открыл", value=creator.name, inline=True)
                embed.add_field(name=":lock: Закрыл", value=inter.author.name, inline=True)
                embed.add_field(name="", value="", inline=False)
                staff_member = self.db.cursor.execute("SELECT username FROM staff_list WHERE username = ?", (inter.author.name,)).fetchone()
                if staff_member is not None:
                    embed.add_field(name=":mag_right: Взял тикет", value=f"<@{inter.author.id}>", inline=True)
                #embed.add_field(name="Пожалуйста оцените работу сотрудника", value="", inline=False)
                embed.set_author(name="Yooma Support", icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                await creator.send(embed=embed)


            self.db.cursor.execute("SELECT closed_tickets FROM staff_list WHERE username = ?", (taken_username,))
            closed_tickets = self.db.cursor.fetchone()[0]
            self.db.cursor.execute("UPDATE staff_list SET closed_tickets = ? WHERE username = ?", (closed_tickets + 1, taken_username))
            self.db.conn.commit()
            date = datetime.date.today()
            self.db.cursor.execute(""" 
                SELECT * FROM date_stats
                WHERE username = ? AND date = ?
            """, (taken_username, date.strftime("%d.%m.%Y")))
            existing_stat = self.db.cursor.fetchone()
            if existing_stat is None:
                self.db.cursor.execute(""" 
                    INSERT INTO date_stats (username, date, closed_tickets)
                    VALUES (?, ?, 1)
                """, (taken_username, date.strftime("%d.%m.%Y")))
            else:
                self.db.cursor.execute(""" 
                    UPDATE date_stats SET closed_tickets = ?
                    WHERE username = ? AND date = ?
                """, (existing_stat[3] + 1, taken_username, date.strftime("%d.%m.%Y")))
            self.db.conn.commit()
            self.db.cursor.execute("DELETE FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            self.db.conn.commit()
            await asyncio.sleep(5)
            await inter.channel.delete()
        
        if inter.data.custom_id == "confirm_close_with_reason_ticket":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            taken_username = self.db.cursor.fetchone()[0]
            self.db.cursor.execute("SELECT closed_tickets FROM staff_list WHERE username = ?", (taken_username,))
            closed_tickets = self.db.cursor.fetchone()[0]
            self.db.cursor.execute("UPDATE staff_list SET closed_tickets = ? WHERE username = ?", (closed_tickets + 1, taken_username))
            self.db.conn.commit()
            date = datetime.date.today()
            self.db.cursor.execute(""" 
                SELECT * FROM date_stats
                WHERE username = ? AND date = ?
            """, (taken_username, date.strftime("%d.%m.%Y")))
            existing_stat = self.db.cursor.fetchone()
            if existing_stat is None:
                self.db.cursor.execute(""" 
                    INSERT INTO date_stats (username, date, closed_tickets)
                    VALUES (?, ?, 1)
                """, (taken_username, date.strftime("%d.%m.%Y")))
            else:
                self.db.cursor.execute(""" 
                    UPDATE date_stats SET closed_tickets = ?
                    WHERE username = ? AND date = ?
                """, (existing_stat[3] + 1, taken_username, date.strftime("%d.%m.%Y")))
            self.db.conn.commit()
            class CloseTicketModal(disnake.ui.Modal):
                def __init__(self, taken_username, bot):
                    self.taken_username = taken_username
                    self.bot = bot
                    self.db = Database("database.db")
                    super().__init__(title="Причина закрытия тикета", components=[
                        disnake.ui.ActionRow(
                            disnake.ui.TextInput(
                                label="Причина",
                                placeholder="Введите причину закрытия тикета",
                                style=disnake.TextInputStyle.short,
                                custom_id="reason_input"
                            )
                        )
                    ])

                async def callback(self, inter):
                    embed1 = disnake.Embed(
                        description=f"Тикет был закрыт - {inter.user.mention}",
                        color=embed_color
                    )
                    embed2 = disnake.Embed(
                        description=f"Тикет будет удален через несколько секунд",
                        color=embed_color
                    )
                    await inter.response.send_message(embeds=[embed1, embed2])
                    reason = inter.text_values['reason_input']
                    self.db.cursor.execute("SELECT creator_id, thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                    creator_id, thread_number = self.db.cursor.fetchone()
                    creator = await self.bot.fetch_user(creator_id)
                    if creator is not None:
                        date_str = datetime.date.today().strftime("%d.%m.%Y")
                        embed = disnake.Embed(title="Ваш тикет был закрыт",timestamp=datetime.datetime.now(),color=embed_color)
                        embed.add_field(name=":id: Ticket ID", value=thread_number, inline=True)
                        embed.add_field(name=":unlock: Открыл", value=creator.name, inline=True)
                        embed.add_field(name=":lock: Закрыл", value=inter.author.name, inline=True)
                        embed.add_field(name="", value="", inline=False)
                        staff_member = self.db.cursor.execute("SELECT username FROM staff_list WHERE username = ?", (inter.author.name,)).fetchone()
                        if staff_member is not None:
                            embed.add_field(name=":mag_right: Взял тикет", value=f"<@{inter.author.id}>", inline=True)
                        embed.add_field(name=":pencil: Сообщение", value=reason, inline=False)
                        #embed.add_field(name="Пожалуйста оцените работу сотрудника", value="", inline=False)
                        embed.set_author(name="Yooma Support", icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                        await creator.send(embed=embed)

                    self.db.cursor.execute("DELETE FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                    self.db.conn.commit()
                    await asyncio.sleep(5)
                    await inter.channel.delete()

            await inter.response.send_modal(CloseTicketModal(taken_username, self.bot))


def setuptickets(bot):
    bot.add_cog(Tickets(bot))