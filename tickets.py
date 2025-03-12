import disnake, asyncio, datetime
from disnake.ext import commands
from database import Database

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
        self.lock = asyncio.Lock()
    
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
    
    def update_ban_time(self, user_id, time):
        self.db.cursor.execute("SELECT * FROM banned_users WHERE user_id = ?", (user_id,))
        banned_user = self.db.cursor.fetchone()

        if banned_user is not None:
            current_time = datetime.datetime.now()
            ban_until = datetime.datetime.strptime(banned_user[3], "%d.%m.%Y %H:%M")

            if current_time >= ban_until:
                self.db.cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
                self.db.conn.commit()

    @commands.slash_command(description="[DEV] - Изменить количество закрытых тикетов сотрудника")
    async def sum(self, inter, username: str, value: str):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return

        self.db.cursor.execute("SELECT * FROM staff_list WHERE username = ?", (username,))
        staff_member = self.db.cursor.fetchone()

        if staff_member is None:
            await inter.response.send_message("Сотрудник не найден!", ephemeral=True)
            return

        try:
            value = int(value)
        except ValueError:
            await inter.response.send_message("Неправильный формат значения", ephemeral=True)
            return

        new_value = staff_member[5] + value
        if new_value < 0:
            new_value = 0

        self.db.cursor.execute("UPDATE staff_list SET closed_tickets = ? WHERE username = ?", (new_value, username))
        self.db.conn.commit()

        await inter.response.send_message(f"Количество закрытых тикетов сотрудника {username} изменено на {new_value}", ephemeral=True)

    @commands.slash_command(description="[DEV] - Разрешить создавать обращение пользователю")
    async def ticketunban(self, inter, user_id: str):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        self.db.cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        self.db.conn.commit()
        await inter.response.send_message(f"Пользователь с айдишником {user_id} теперь может создавать обращение.", ephemeral=True)

    @commands.slash_command(description="[DEV] - Запретить создавать обращение пользователю на время")
    async def ticketban(self, inter, user_id: str, time: str):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        time_map = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }

        try:
            value = int(time[:-1])
            unit = time[-1]
            if unit not in time_map:
                await inter.response.send_message("Неправильный формат времени", ephemeral=True)
                return
            total_seconds = value * time_map[unit]
            ban_until = datetime.datetime.now() + datetime.timedelta(seconds=total_seconds)
            ban_until_str = ban_until.strftime("%d.%m.%Y %H:%M")

            self.db.cursor.execute("INSERT INTO banned_users (user_id, ban_time, ban_until) VALUES (?, ?, ?)", (user_id, time, ban_until_str))
            self.db.conn.commit()
            await inter.response.send_message(f"Пользователь с айдишником {user_id} запрещен создавать обращение на {time}", ephemeral=True)
        except ValueError:
            await inter.response.send_message("Неправильный формат времени", ephemeral=True)

    @commands.slash_command(description="[DEV] - Сообщение создания обращения")
    async def ticketmsg(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        if inter.guild is not None:
            self.db.cursor.execute(""" 
                SELECT embed_color, category_id, ticket_channel_id 
                FROM settings 
                WHERE guild_id = ?
            """, (inter.guild.id,))
        else:
            self.db.cursor.execute(""" 
                SELECT embed_color, category_id, ticket_channel_id 
                FROM settings 
                WHERE user_id = ?
            """, (inter.author.id,))
        settings = self.db.cursor.fetchone()

        if settings is None:
            await inter.response.send_message("Настройки не найдены!", ephemeral=True)
            return

        embed_color = disnake.Color(int(settings[0].lstrip('#'), 16))
        category_id = settings[1]
        channel_id = settings[2]

        if inter.guild is not None:
            category = inter.guild.get_channel(category_id)
            channel = inter.guild.get_channel(channel_id)
        else:
            category = None
            channel = None

        if category is None or channel is None:
            await inter.response.send_message("Категория или канал не найдены!")
            return

        embed = disnake.Embed(
            title="Создание обращения в клиентскую поддержку",
            description="Мы настоятельно рекомендуем **подробно** описывать ваши просьбы или проблемы. Это поможет нам оказать вам **быструю и эффективную помощь**.\n\n"
            "▎Важные моменты:\n"
            "- Не открывайте обращения, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
            "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
            "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
            "**Несоблюдение этих правил может привести к наказанию**.",
            color=embed_color)
        embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
        embed.set_thumbnail(url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")

        view = disnake.ui.View()
        button = disnake.ui.Button(label="Создать обращение", emoji="📨", custom_id="create_ticket", style=disnake.ButtonStyle.primary)
        view.add_item(button)

        if inter.guild is not None:
            await channel.send(embed=embed, view=view)
        else:
            await inter.response.send_message("Эта команда может быть использована только на сервере", ephemeral=True)
            return
        await inter.response.send_message("Отправил сообщение.", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        self.db.cursor.execute(""" 
            SELECT embed_color, category_id, ticket_channel_id 
            FROM settings 
            WHERE guild_id = ?
        """, (inter.guild.id,))
        settings = self.db.cursor.fetchone()

        if settings is None:
            await inter.response.send_message("Настройки не найдены!", ephemeral=True)
            return

        embed_color = disnake.Color(int(settings[0].lstrip('#'), 16))
        if inter.data.custom_id == "create_ticket":
            self.db.cursor.execute("SELECT status FROM settings WHERE guild_id = ?", (inter.guild.id,))
            status = self.db.cursor.fetchone()

            if status is not None and status[0] == 0:
                await inter.response.send_message("🚧 Техработы. Извините за неудобства! Скоро всё починим! 🔧✨", ephemeral=True)
                return
            self.db.cursor.execute("SELECT * FROM banned_users WHERE user_id = ?", (inter.author.id,))
            banned_user = self.db.cursor.fetchone()
            if banned_user is not None:
                current_time = datetime.datetime.now()
                ban_until = datetime.datetime.strptime(banned_user[3], "%d.%m.%Y %H:%M")

                if current_time >= ban_until:
                    self.db.cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (inter.author.id,))
                    self.db.conn.commit()
                    await inter.response.send_message("✅ / Ваш бан спал. Теперь вы можете создавать обращение.", ephemeral=True)
                    return
                else:
                    await inter.response.send_message(f"🚫 / Вам запрещено создавать обращение до {ban_until.strftime('%d.%m.%Y %H:%M')}.", ephemeral=True)
                    return
            else:
                pass
            self.db.cursor.execute("SELECT * FROM created_tickets WHERE creator_id = ?", (inter.author.id,))
            existing_ticket = self.db.cursor.fetchone()

            if existing_ticket is not None:
                await inter.response.send_message("🔸 / У вас уже **имеется открытое обращение**. Ожидайте ответа", ephemeral=True)
                return
            class CreateTicketModal(disnake.ui.Modal):
                def __init__(self):
                    super().__init__(title="Создание обращения", components=[
                        disnake.ui.ActionRow(
                            disnake.ui.TextInput(
                                label="Краткое описание обращения",
                                placeholder="Введите краткое описание обращения",
                                style=disnake.TextInputStyle.short,
                                custom_id="description_input",
                                min_length=3
                            )
                        )
                    ])
                    self.db = Database("database.db")

                async def callback(self, inter):
                    await inter.response.defer(ephemeral=True)
                    description = inter.text_values['description_input']
                    if len(description) < 3:
                        await inter.response.send_message("Минимальная длина ввода - 3 символа", ephemeral=True)
                        return

                    self.db.cursor.execute("SELECT counter_tickets FROM settings WHERE guild_id = ?", (inter.guild.id,))
                    counter_tickets = self.db.cursor.fetchone()[0]
                    self.db.cursor.execute("UPDATE settings SET counter_tickets = ? WHERE guild_id = ?", (counter_tickets + 1, inter.guild.id))
                    self.db.conn.commit()
                    thread = await inter.channel.create_thread(name=f"ticket-{counter_tickets + 1}", type=disnake.ChannelType.private_thread)
                    await thread.edit(invitable=False, auto_archive_duration=disnake.ThreadArchiveDuration.week)
                    
                    thread_number = int(thread.name.split("-")[1])
                    self.db.cursor.execute("INSERT INTO created_tickets (thread_id, creator_username, creator_id, thread_number) VALUES (?, ?, ?, ?)", 
                                        (thread.id, inter.author.name, inter.author.id, thread_number))
                    self.db.conn.commit()
                    
                    ticket_embed = disnake.Embed(
                        title="Спасибо за обращение в клиенсткую поддержку",
                        description="Пожалуйста, **опишите суть вашей проблемы подробнее**, чтобы мы могли оказать вам **наилучшее решение**.\n\n"
                        "▎Важные моменты:\n"
                        "- Не открывайте обращение, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
                        "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
                        "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
                        "**Несоблюдение этих правил может привести к наказанию**.",
                        color=embed_color
                    )
                    ticket_embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                    ticket_embed.set_thumbnail(url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")

                    view = disnake.ui.View(timeout=None)
                    take_button = disnake.ui.Button(label="Взять обращение", emoji="📝", custom_id="take_ticket", style=disnake.ButtonStyle.primary)
                    close_button = disnake.ui.Button(label="Закрыть обращение", emoji="🔒", custom_id="close_ticket", style=disnake.ButtonStyle.danger)
                    view.add_item(take_button)
                    view.add_item(close_button)

                    self.db.cursor.execute("SELECT mention, user_id FROM staff_list WHERE mention = 1")
                    results = self.db.cursor.fetchall()

                    ping_message = ""
                    for result in results:
                        user_id = result[1]
                        ping_message += f"<@{user_id}> "

                    if ping_message: 
                        mention = await thread.send(ping_message)
                        await mention.delete()
                    else:
                        pass

                    await thread.send(inter.user.mention, embed=ticket_embed, view=view)

                    self.db.cursor.execute("SELECT primetime FROM settings WHERE guild_id = ?", (inter.guild.id,))
                    primetime = self.db.cursor.fetchone()
                    if primetime is not None:
                        primetime = primetime[0]
                        start_time, end_time = primetime.split(" - ")
                        start_hour, start_minute = map(int, start_time.split(":"))
                        end_hour, end_minute = map(int, end_time.split(":"))
                        current_time = datetime.datetime.now()
                        current_hour = current_time.hour
                        current_minute = current_time.minute
                        if not (start_hour <= current_hour < end_hour or (current_hour == end_hour and current_minute <= end_minute)):
                            await thread.send(f"{inter.user.mention}, В данный момент нерабочее время, и время ответа может занять больше времени, чем обычно.\nПожалуйста, оставайтесь на связи, и мы ответим вам, как только сможем.")
                            pass

                    info_embed = disnake.Embed(
                        title="Краткая суть обращения:",
                        description=description,
                        color=0xF0C43F
                    )
                    await thread.send(embed=info_embed)

                    await inter.followup.send(rf":tickets:  \ **Ваше обращение был создано** - {thread.mention}", ephemeral=True)


            await inter.response.send_modal(CreateTicketModal())
        
        if inter.data.custom_id == "take_ticket":
            async with self.lock:
                if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                    await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                    return

                ticket_embed = disnake.Embed(
                    title="Спасибо за обращение в клиенсткую поддержку",
                    description="Спасибо за ваше обращение. Пожалуйста, **опишите суть вашей проблемы подробнее**, чтобы мы могли оказать вам **наилучшее решение**.\n\n"
                    "▎Важные моменты:\n"
                    "- Не открывайте обращение, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
                    "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
                    "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
                    "**Несоблюдение этих правил может привести к наказанию**.",
                    color=embed_color
                )
                ticket_embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                ticket_embed.set_thumbnail(url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                ticket_embed.add_field(name=f"", value=f"🔍 Взял обращение - {inter.author.mention}", inline=False)

                view = disnake.ui.View(timeout=None)
                close_button = disnake.ui.Button(label="Закрыть обращение", emoji="🔒", custom_id="close_ticket", style=disnake.ButtonStyle.danger)
                transfer_button = disnake.ui.Button(label="Передать обращение", emoji="📝", custom_id="transfer_ticket", style=disnake.ButtonStyle.primary)
                view.add_item(close_button)
                view.add_item(transfer_button)

                await inter.message.edit(embed=ticket_embed, view=view)

                self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                taken_ticket = self.db.cursor.fetchone()
                if taken_ticket is not None and taken_ticket[0] is not None:
                    await inter.response.send_message("Этот обращение уже взят!", ephemeral=True)
                    return

                self.db.cursor.execute("SELECT thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                thread_number = self.db.cursor.fetchone()[0]
             
                embed = disnake.Embed(title="", description=f"Успешно взялся за обращение - {inter.author.mention}", color=0xF0C43F,)
                await inter.response.send_message(embed=embed)

                self.db.cursor.execute("UPDATE created_tickets SET taken_username = ? WHERE thread_id = ?", 
                                    (inter.author.name, inter.channel.id))
                self.db.conn.commit()

                self.db.cursor.execute("SELECT ticket_name FROM staff_list WHERE username = ?", (inter.author.name,))
                ticket_name = self.db.cursor.fetchone()
                if ticket_name is not None:
                    ticket_name = ticket_name[0]
                else:
                    ticket_name = taken_username
                new_name = f"{ticket_name}-ticket-{thread_number}"
                await inter.channel.edit(name=new_name)
        
        if inter.data.custom_id == "close_ticket":
            confirmation_embed = disnake.Embed(
                title="Подтверждение",
                description="Вы уверены что хотите закрыть обращение?",
                color=0xF0C43F,
            )
            view = disnake.ui.View(timeout=30)
            close_button = disnake.ui.Button(label="Закрыть", emoji='🔒', custom_id="confirm_close_ticket", style=disnake.ButtonStyle.red)
            close_with_reason_button = disnake.ui.Button(label='Закрыть с причиной', custom_id="confirm_close_with_reason_ticket", style=disnake.ButtonStyle.red, emoji='🔒')
            cancel_button = disnake.ui.Button(label="Отмена", emoji='🚫', custom_id="cancel_close_ticket", style=disnake.ButtonStyle.gray)
            view.add_item(close_button)
            view.add_item(close_with_reason_button)
            view.add_item(cancel_button)

            await inter.response.send_message(embed=confirmation_embed, view=view)
        
        if inter.data.custom_id == "cancel_close_ticket":
            await inter.message.delete()

        if inter.data.custom_id == "confirm_close_ticket":
            await inter.message.delete()
            self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            taken_username = self.db.cursor.fetchone()
            if taken_username is None:
                embed1 = disnake.Embed(
                    description=f"Обращение было закрыто - {inter.user.mention}",
                    color=0xF0C43F,
                )
                embed2 = disnake.Embed(
                    description=f"Обращение будет удален через несколько секунд",
                    color=0xF0C43F,
                )
                await inter.response.defer()
                await inter.channel.send(embed=embed1)
                await inter.channel.send(embed=embed2)
                await asyncio.sleep(5)
                await inter.channel.delete()
                self.db.cursor.execute("DELETE FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                self.db.conn.commit()
                return
            else:
                taken_username = taken_username[0]
                self.db.cursor.execute("SELECT closed_tickets FROM staff_list WHERE username = ?", (taken_username,))
                closed_tickets = self.db.cursor.fetchone()[0]
                self.db.cursor.execute("UPDATE staff_list SET closed_tickets = ? WHERE username = ?", (closed_tickets + 1, taken_username))
                self.db.conn.commit()
                embed1 = disnake.Embed(
                    description=f"Обращение было закрыто - {inter.user.mention}",
                    color=0xF0C43F,
                )
                embed2 = disnake.Embed(
                    description=f"Обращение будет удален через несколько секунд",
                    color=0xF0C43F,
                )
                await inter.response.defer()
                await inter.channel.send(embed=embed1)
                await inter.channel.send(embed=embed2)
                self.db.cursor.execute("SELECT creator_id, thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                creator_id, thread_number = self.db.cursor.fetchone()
                creator = await self.bot.fetch_user(creator_id)
                if creator is not None:
                    embed = disnake.Embed(title="Ваш обращение было закрыт",timestamp=datetime.datetime.now(),color=embed_color)
                    embed.add_field(name=":id: Ticket ID", value=thread_number, inline=True)
                    embed.add_field(name=":unlock: Открыл", value=creator.name, inline=True)
                    embed.add_field(name=":lock: Закрыл", value=inter.author.name, inline=True)
                    embed.add_field(name="", value="", inline=False)
                    staff_member = self.db.cursor.execute("SELECT username FROM staff_list WHERE username = ?", (inter.author.name,)).fetchone()
                    if staff_member is not None:
                        embed.add_field(name=":mag_right: Взял обращение", value=f"<@{inter.author.id}>", inline=True)
                    #embed.add_field(name="Пожалуйста оцените работу сотрудника", value="", inline=False)
                    embed.set_author(name="Yooma Support", icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                    await creator.send(embed=embed)
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
                await asyncio.sleep(5)
                await inter.channel.delete()
                self.db.cursor.execute("DELETE FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                self.db.conn.commit()
                    
        
        if inter.data.custom_id == "confirm_close_with_reason_ticket":
            await inter.message.delete()
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            
            self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            taken_username = self.db.cursor.fetchone()

            if taken_username is not None:
                taken_username = taken_username[0]
                self.db.cursor.execute("SELECT closed_tickets FROM staff_list WHERE username = ?", (taken_username,))
                closed_tickets = self.db.cursor.fetchone()
                if closed_tickets is not None:
                    closed_tickets = closed_tickets[0]
                    self.db.cursor.execute("UPDATE staff_list SET closed_tickets = ? WHERE username = ?", (closed_tickets + 1, taken_username))
                    self.db.conn.commit()
                else:
                    await inter.response.send_message("Сотрудник не найден!", ephemeral=True)
                    return
            else:
                await inter.response.send_message("Обращение не найдено!", ephemeral=True)
                return

            date = datetime.date.today()
            self.db.cursor.execute(""" 
                SELECT * FROM date_stats
                WHERE username = ? AND date = ?
            """, (taken_username, date.strftime("%d.%m.%Y")))
            existing_stat = self.db.cursor.fetchone()
            if existing_stat is not None:
                self.db.cursor.execute(""" 
                    UPDATE date_stats SET closed_tickets = ?
                    WHERE username = ? AND date = ?
                """, (existing_stat[3] + 1, taken_username, date.strftime("%d.%m.%Y")))
            else:
                self.db.cursor.execute(""" 
                    INSERT INTO date_stats (username, date, closed_tickets)
                    VALUES (?, ?, 1)
                """, (taken_username, date.strftime("%d.%m.%Y")))

            self.db.conn.commit()

            class CloseTicketModal(disnake.ui.Modal):
                def __init__(self, taken_username, bot):
                    self.taken_username = taken_username
                    self.bot = bot
                    self.db = Database("database.db")
                    super().__init__(title="Причина закрытия обращения", components=[
                        disnake.ui.ActionRow(
                            disnake.ui.TextInput(
                                label="Причина",
                                placeholder="Введите причину закрытия обращения",
                                style=disnake.TextInputStyle.short,
                                custom_id="reason_input"
                            )
                        )
                    ])
                async def callback(self, inter):
                    embed1 = disnake.Embed(
                        description=f"Обращение было закрыто - {inter.user.mention}",
                        color=0xF0C43F
                    )
                    embed2 = disnake.Embed(
                        description=f"Обращение будет удалено через несколько секунд",
                        color=0xF0C43F
                    )
                    await inter.response.defer()
                    await inter.channel.send(embed=embed1)
                    await inter.channel.send(embed=embed2)
                    reason = inter.text_values['reason_input']
                    self.db.cursor.execute("SELECT creator_id, thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                    creator_id, thread_number = self.db.cursor.fetchone()
                    creator = await self.bot.fetch_user(creator_id)
                    if creator is not None:
                        embed = disnake.Embed(title="Ваш обращение было закрыто", timestamp=datetime.datetime.now(), color=embed_color)
                        embed.add_field(name=":id: Ticket ID", value=thread_number, inline=True)
                        embed.add_field(name=":unlock: Открыл", value=creator.name, inline=True)
                        embed.add_field(name=":lock: Закрыл", value=inter.author.name, inline=True)
                        embed.add_field(name="", value="", inline=False)
                        staff_member = self.db.cursor.execute("SELECT username FROM staff_list WHERE username = ?", (inter.author.name,)).fetchone()
                        if staff_member is not None:
                            embed.add_field(name=":mag_right: Взял обращение", value=f"<@{inter.author.id}>", inline=True)
                        embed.add_field(name=":pencil: Сообщение", value=reason, inline=False)
                        # embed.add_field(name="Пожалуйста оцените работу сотрудника", value="", inline=False)
                        embed.set_author(name="Yooma Support", icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                        await creator.send(embed=embed)
                    self.db.cursor.execute("DELETE FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                    self.db.conn.commit()
                    await asyncio.sleep(5)
                    await inter.channel.delete()

            await inter.response.send_modal(CloseTicketModal(taken_username, self.bot))

        if inter.data.custom_id == "transfer_ticket":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return

            self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
            taken_username = self.db.cursor.fetchone()[0]

            if taken_username is None:
                await inter.response.send_message("Это обращение не взято!", ephemeral=True)
                return

            if taken_username != inter.author.name:
                await inter.response.send_message("Вы не можете передать обращение, который не принадлежит вам!", ephemeral=True)
                return

            class TransferTicketModal(disnake.ui.Modal):
                def __init__(self, bot):
                    self.bot = bot
                    self.db = Database("database.db")
                    super().__init__(title="Передать обращение", components=[
                        disnake.ui.ActionRow(
                            disnake.ui.TextInput(
                                label="Юзернейм сотрудника",
                                placeholder="Введите юзернейм сотрудника",
                                style=disnake.TextInputStyle.short,
                                custom_id="staff_name_input"
                            )
                        )
                    ])

                async def callback(self, inter):
                    staff_name = inter.text_values['staff_name_input']
                    self.db.cursor.execute("SELECT * FROM staff_list WHERE username = ?", (staff_name,))
                    staff_member = self.db.cursor.fetchone()
                    if staff_member is None:
                        await inter.response.send_message("Сотрудник не найден!", ephemeral=True)
                        return

                    self.db.cursor.execute("UPDATE created_tickets SET taken_username = ? WHERE thread_id = ?", (staff_name, inter.channel.id))
                    self.db.conn.commit()

                    thread_number = self.db.cursor.execute("SELECT thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,)).fetchone()[0]
                    
                    self.db.cursor.execute("SELECT ticket_name FROM staff_list WHERE username = ?", (staff_name,))
                    ticket_name = self.db.cursor.fetchone()
                    if ticket_name is not None:
                        ticket_name = ticket_name[0]
                    else:
                        ticket_name = taken_username
                    new_name = f"{ticket_name}-ticket-{thread_number}"
                    await inter.channel.edit(name=new_name)

                    self.db.cursor.execute("SELECT user_id FROM staff_list WHERE username = ?", (staff_name,))
                    staff_member_id = self.db.cursor.fetchone()[0]
                    embed = disnake.Embed(title="", description=f"Обращение было передано - <@{staff_member_id}>", color=0xF0C43F)
                    await inter.response.send_message(embed=embed)
                    ticket_embed = disnake.Embed(
                        title="Спасибо за обращение в клиенсткую поддержку",
                        description="Спасибо за ваше обращение. Пожалуйста, **опишите суть вашей проблемы подробнее**, чтобы мы могли оказать вам **наилучшее решение**.\n\n"
                        "▎Важные моменты:\n"
                        "- Не открывайте обращение, которые не соответствуют указанной теме или не связаны с описанной проблемой.\n"
                        "- Укажите все необходимые данные, чтобы мы могли оперативно решить ваш вопрос.\n"
                        "- Соблюдайте правила общения, чтобы избежать блокировки доступа к созданию запросов.\n\n"
                        "**Несоблюдение этих правил может привести к наказанию**.",
                        color=embed_color
                    )
                    ticket_embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                    ticket_embed.set_thumbnail(url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                    ticket_embed.add_field(name=f"", value=f"🔍 Взял обращение - <@{staff_member_id}>", inline=False)

                    view = disnake.ui.View(timeout=None)
                    close_button = disnake.ui.Button(label="Закрыть обращение", emoji="🔒", custom_id="close_ticket", style=disnake.ButtonStyle.danger)
                    transfer_button = disnake.ui.Button(label="Передать обращение", emoji="📝", custom_id="transfer_ticket", style=disnake.ButtonStyle.primary)
                    view.add_item(close_button)
                    view.add_item(transfer_button)

                    await inter.message.edit(embed=ticket_embed, view=view)

            await inter.response.send_modal(TransferTicketModal(self.bot))


def setuptickets(bot):
    bot.add_cog(Tickets(bot))