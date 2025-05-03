import disnake, asyncio, datetime, logging
from disnake.ext import commands
from database import Database


logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

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

    @commands.slash_command(description="[DEV] - ticket msg")
    async def ticketmsg(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return

        settings = self.db.get_settings(guild_id=inter.guild.id)
        if settings is None:
            await inter.response.send_message("Настройки не найдены!", ephemeral=True)
            return

        embed_color = disnake.Color(int(settings[3].lstrip('#'), 16))
        category_id = settings[4]
        channel_id = settings[5]

        if inter.guild is not None:
            category = inter.guild.get_channel(category_id)
            channel = inter.guild.get_channel(channel_id)
        else:
            category = None
            channel = None

        if category is None or channel is None:
            await inter.response.send_message("Категория или канал не найдены!")
            return

        self.db.cursor.execute("SELECT primetime FROM settings WHERE guild_id = ?", (inter.guild.id,))
        primetime = self.db.cursor.fetchone()

        embed = disnake.Embed(
            title="🎫 Обращение в поддержку",
            description="> 📌 Пожалуйста, опишите вашу проблему **максимально подробно**, прикрепите скриншоты (если нужно) и укажите все важные детали. Это ускорит решение вашего запроса.\n\n"
                        "**▸ Среднее время ответа:** 1–3 часа\n"
                        f"**▸ Рабочее время поддержки:** {primetime[0]}\n"
                        "**▸ При нарушении правил:** ограничение доступа к тикетам/мут/бан",
            color=embed_color
        )
        embed.add_field(name="\u200b", value="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", inline=False)
        rules = [
            "• **Будьте вежливы** — неадекватное поведение приведёт к блокировке",
            "• **Пишите по делу** — не отклоняйтесь от темы",
            "• **Прикладывайте доказательства** (скриншоты, логи и т.д.)",
            "В тикетах действует прецедентная система правил."
        ]
        embed.add_field(name="📜 **Правила подачи обращения**",value="\n".join(rules),inline=False)
        embed.set_author(name="Yooma Support",icon_url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
        embed.set_footer(text="При ошибке системы тикетов напишите в дискорд -> @traquillionz")

        view = disnake.ui.View(timeout=None)
        select_menu = disnake.ui.Select(
            placeholder="Выберите тему обращения",
            options=[
                disnake.SelectOption(label="Вопрос", description="Задайте свой вопрос", emoji="❓"),
                disnake.SelectOption(label="Жалоба", description="Жалоба на нарушение игрока/администратора", emoji="⚠️"),
                disnake.SelectOption(label="Обжалование", description="Обжалование наказания", emoji="⚖️"),
                disnake.SelectOption(label="Предложение", description="Предложите вашу идею или улучшение", emoji="💼"),
                disnake.SelectOption(label="Доп. услуги", description="Докупка/Перенос и другие услуги", emoji="💡"),
                disnake.SelectOption(label="Другое", description="Остальные вопросы", emoji="🤔")
            ]
        )

        async def select_callback(inter):
            theme = inter.data.values[0]
            self.db.cursor.execute("SELECT * FROM staff_list WHERE user_id = ?", (inter.author.id,))
            staff = self.db.cursor.fetchone()
            if staff is not None:
                self.db.cursor.execute("SELECT closed_tickets FROM staff_list WHERE username = ?", (staff[1],))
                closed_tickets = self.db.cursor.fetchone()
                if closed_tickets is not None:
                    closed_tickets = closed_tickets[0]
                    self.db.cursor.execute("UPDATE staff_list SET closed_tickets = ? WHERE username = ?", (closed_tickets + 1, staff[1]))
                    self.db.conn.commit()

                date = datetime.date.today()
                self.db.cursor.execute(""" 
                    SELECT * FROM date_stats
                    WHERE username = ? AND date = ?
                """, (staff[1], date.strftime("%d.%m.%Y")))
                existing_stat = self.db.cursor.fetchone()
                if existing_stat is not None:
                    self.db.cursor.execute(""" 
                        UPDATE date_stats SET closed_tickets = ?
                        WHERE username = ? AND date = ?
                    """, (existing_stat[3] + 1, staff[1], date.strftime("%d.%m.%Y")))
                else:
                    self.db.cursor.execute(""" 
                        INSERT INTO date_stats (username, date, closed_tickets)
                        VALUES (?, ?, 1)
                    """, (staff[1], date.strftime("%d.%m.%Y")))
                self.db.conn.commit()
            await inter.response.send_modal(Tickets.CreateTicketModal(self.bot, theme))

        select_menu.callback = select_callback
        view.add_item(select_menu)

        if inter.guild is not None:
            await inter.channel.send(embed=embed, view=view)
        else:
            await inter.response.send_message("Эта команда может быть использована только на сервере", ephemeral=True)
            return
        await inter.response.send_message("Отправил сообщение.", ephemeral=True)

    class CreateTicketModal(disnake.ui.Modal):
        def __init__(self, bot, theme):
            self.bot = bot
            self.db = Database("database.db")
            self.theme = theme
            super().__init__(title="Создание обращения", components=[
                disnake.ui.ActionRow(
                    disnake.ui.TextInput(
                        label="Краткое описание обращения",
                        placeholder="Введите краткое описание обращения",
                        style=disnake.TextInputStyle.short,
                        custom_id="description_input",
                        min_length=5,
                        max_length=350
                    )
                )
            ])

            if self.theme in ["Доп. услуги", "Обжалование"]:
                self.components.append(
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Ссылка на профиль",
                            placeholder="Введите ссылку на профиль",
                            style=disnake.TextInputStyle.short,
                            custom_id="profile_link_input",
                            min_length=28,
                            max_length=350
                        )
                    )
                )

        async def callback(self, inter):
            self.db.cursor.execute("SELECT status FROM settings WHERE guild_id = ?", (inter.guild.id,))
            status = self.db.cursor.fetchone()
            if status is not None and status[0] == 1:
                await inter.response.send_message("⛔ \ **Технические работы**. Пожалуйста, попробуйте создать обращение **позже**. ⚠️", ephemeral=True)
                return

            await inter.response.defer(ephemeral=True)
            description = inter.text_values['description_input']

            if self.theme in ["Доп. услуги", "Обжалование"]:
                profile_link = inter.text_values['profile_link_input']

                profiles_links = [
                    "https://yooma.su/ru/profile/",
                    "https://yooma.su/en/profile/",
                    "https://steamcommunity.com/profiles/",
                    "https://steamcommunity.com/id/"
                ]

                for profile in profiles_links:
                    if profile_link.startswith(profile):
                        break
                else:
                    await inter.followup.send("⛔ \ **Неправильно** введена ссылка на профиль. Пример: https://yooma.su/ru/profile/admin", ephemeral=True)
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

            self.db.cursor.execute("SELECT embed_color FROM settings WHERE guild_id = ?", (inter.guild.id,))
            embed_color = self.db.cursor.fetchone()[0]
            embed_color = disnake.Color(int(embed_color.lstrip('#'), 16))

            ticket_embed = disnake.Embed(
                title="🎫 Спасибо за обращение в Yooma Support",
                description=(
                    "**Пожалуйста, опишите вашу проблему как можно подробнее**, чтобы мы могли помочь вам **быстрее и эффективнее**.\n\n"
                    
                    "🔹 **Важные моменты:**\n"
                    "- Расскажите более подробнее вашу проблему и её тему.\n"
                    "- Укажите все необходимые данные (никнеймы, ссылка на профиль, скриншоты и т.д.).\n"
                    "- Соблюдайте правила общения, чтобы избежать ограничений.\n\n"
                ),
                color=embed_color
            )
            ticket_embed.add_field(name="", value="*При нарушении правил: тикет может быть досрочно закрыт, а пользователь получит наказания.*")
            ticket_embed.set_author(name="Yooma Support", icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
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

            info_embed = disnake.Embed(title=f"Краткая суть обращения: {self.theme}", description=description, color=0xF0C43F)
            if self.theme in ["Доп. услуги", "Обжалование"]:
                info_embed.add_field(name="Ссылка на профиль", value=profile_link, inline=False)
            await thread.send(embed=info_embed)

            await inter.followup.send(rf":tickets:  \ **Ваше обращение был создано** - {thread.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        if inter.data.custom_id == "take_ticket":
            async with self.lock:
                try:
                    logger.info(f"[TICKETS] Пользователь {inter.author.name} пытается взять тикет {inter.channel.name}")
                    if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                        await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                        return

                    self.db.cursor.execute("SELECT status FROM settings WHERE guild_id = ?", (inter.guild.id,))
                    status = self.db.cursor.fetchone()
                    if status is not None and status[0] == 1:
                        await inter.response.send_message("⛔ \ **Технические работы**. Пожалуйста, попробуйте взять обращение **позже**. ⚠️", ephemeral=True)
                        return

                    await inter.response.defer()

                    self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                    taken_ticket = self.db.cursor.fetchone()
                    if taken_ticket is not None and taken_ticket[0] is not None:
                        await inter.response.send_message("Это обращение уже взято!", ephemeral=True)
                        return

                    self.db.cursor.execute("SELECT embed_color FROM settings WHERE guild_id = ?", (inter.guild.id,))
                    embed_color = self.db.cursor.fetchone()[0]
                    embed_color = disnake.Color(int(embed_color.lstrip('#'), 16))

                    ticket_embed = disnake.Embed(
                        title="🎫 Спасибо за обращение в Yooma Support",
                        description=(
                            "**Пожалуйста, опишите вашу проблему как можно подробнее**, чтобы мы могли помочь вам **быстрее и эффективнее**.\n\n"
                            
                            "🔹 **Важные моменты:**\n"
                            "- Расскажите более подробнее вашу проблему и её тему.\n"
                            "- Укажите все необходимые данные (никнеймы, ссылка на профиль, скриншоты и т.д.).\n"
                            "- Соблюдайте правила общения, чтобы избежать ограничений.\n\n"
                        ),
                        color=embed_color
                    )
                    ticket_embed.add_field(name="", value="*При нарушении правил: тикет может быть досрочно закрыт, а пользователь получит наказания.*")
                    ticket_embed.set_author(name="Yooma Support", icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                    ticket_embed.set_thumbnail(url="https://static1.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                    ticket_embed.add_field(name=f"", value=f"🔍 Взял обращение - {inter.author.mention}", inline=False)

                    view = disnake.ui.View(timeout=None)
                    close_button = disnake.ui.Button(label="Закрыть обращение", emoji="🔒", custom_id="close_ticket", style=disnake.ButtonStyle.danger)
                    transfer_button = disnake.ui.Button(label="Передать обращение", emoji="📝", custom_id="transfer_ticket", style=disnake.ButtonStyle.primary)
                    view.add_item(close_button)
                    view.add_item(transfer_button)

                    await inter.edit_original_response(embed=ticket_embed, view=view)

                    self.db.cursor.execute("SELECT thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                    thread_number = self.db.cursor.fetchone()[0]

                    embed = disnake.Embed(title="", description=f"Успешно взялся за обращение - {inter.author.mention}", color=0xF0C43F)
                    await inter.followup.send(embed=embed)

                    self.db.cursor.execute("UPDATE created_tickets SET taken_username = ? WHERE thread_id = ?", (inter.author.name, inter.channel.id))
                    self.db.conn.commit()

                    self.db.cursor.execute("SELECT ticket_name FROM staff_list WHERE username = ?", (inter.author.name,))
                    ticket_name = self.db.cursor.fetchone()
                    if ticket_name is not None:
                        ticket_name = ticket_name[0]
                    else:
                        ticket_name = taken_username
                    new_name = f"{ticket_name}-ticket-{thread_number}"
                    await inter.channel.edit(name=new_name)

                except Exception as e:
                    logger.error(f"Ошибка при взятии тикета {inter.channel.name}: {e}")

        if inter.data.custom_id == "close_ticket":
            try:
                self.db.cursor.execute("SELECT status FROM settings WHERE guild_id = ?", (inter.guild.id,))
                status = self.db.cursor.fetchone()
                if status is not None and status[0] == 1:
                    await inter.response.send_message("⛔ \ **Технические работы**. Пожалуйста, попробуйте закрыть обращение **позже**. ⚠️", ephemeral=True)
                    return
                logger.info(f"[TICKETS] Пользователь {inter.author.name} пытается закрыть тикет {inter.channel.name}")
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
            except Exception as e:
                logger.error(f"Ошибка при взятии тикета {inter.channel.name}: {e}")

        if inter.data.custom_id == "cancel_close_ticket":
            await inter.message.delete()

        if inter.data.custom_id == "confirm_close_ticket":
            try:
                self.db.cursor.execute("SELECT status FROM settings WHERE guild_id = ?", (inter.guild.id,))
                status = self.db.cursor.fetchone()
                if status is not None and status[0] == 1:
                    await inter.response.send_message("⛔ \ **Технические работы**. Пожалуйста, попробуйте закрыть обращение **позже**. ⚠️", ephemeral=True)
                    return
                
                await inter.message.delete()
                logger.info(f"[TICKETS] Пользователь {inter.author.name} подтвердил закрытие тикета {inter.channel.name}")
                self.db.cursor.execute("SELECT embed_color FROM settings WHERE guild_id = ?", (inter.guild.id,))
                embed_color = self.db.cursor.fetchone()[0]
                embed_color = disnake.Color(int(embed_color.lstrip('#'), 16))
                self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                taken_username = self.db.cursor.fetchone()
                if taken_username is None or taken_username[0] is None:
                    embed1 = disnake.Embed(
                        description=f"Обращение было закрыто - {inter.user.mention}",
                        color=0xF0C43F,
                    )
                    embed2 = disnake.Embed(
                        description=f"Обращение будет удалено через несколько секунд",
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
                        description=f"Обращение будет удалено через несколько секунд",
                        color=0xF0C43F,
                    )
                    await inter.response.defer()
                    await inter.channel.send(embed=embed1)
                    await inter.channel.send(embed=embed2)
                    self.db.cursor.execute("SELECT creator_id, thread_number FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                    creator_id, thread_number = self.db.cursor.fetchone()
                    creator = await self.bot.fetch_user(creator_id)
                    if creator is not None:
                        embed = disnake.Embed(title="Ваш обращение было закрыто", timestamp=datetime.datetime.now(), color=embed_color)
                        embed.add_field(name=":id: Ticket ID", value=thread_number, inline=True)
                        embed.add_field(name=":unlock: Открыл", value=creator.mention, inline=True)
                        embed.add_field(name=":lock: Закрыл", value=inter.author.mention, inline=True)
                        embed.add_field(name="", value="", inline=False)
                        staff_member = self.db.cursor.execute("SELECT username FROM staff_list WHERE username = ?", (inter.author.name,)).fetchone()
                        if staff_member is not None:
                            self.db.cursor.execute("SELECT user_id FROM staff_list WHERE username = ?", (taken_username,))
                            staff_member_id = self.db.cursor.fetchone()[0]
                            embed.add_field(name=":mag_right: Взял обращение", value=f"<@{staff_member_id}>", inline=True)
                        # embed.add_field(name="Пожалуйста оцените работу сотрудника", value="", inline=False)
                        embed.set_author(name="Yooma Support", icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                        try:
                            await creator.send(embed=embed)
                        except disnake.HTTPException as e:
                            if e.status == 403:
                                pass
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
            except Exception as e:
                logger.error(f"Ошибка при закрытии тикета {inter.channel.name}: {e}")

        if inter.data.custom_id == "confirm_close_with_reason_ticket":
            try:
                
                logger.info(f"[TICKETS] Пользователь {inter.author.name} подтвердил закрытие тикета с причиной {inter.channel.name}")
                if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                    await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                    return

                self.db.cursor.execute("SELECT status FROM settings WHERE guild_id = ?", (inter.guild.id,))
                status = self.db.cursor.fetchone()
                if status is not None and status[0] == 1:
                    await inter.response.send_message("⛔ \ **Технические работы**. Пожалуйста, попробуйте закрыть с причиной обращение **позже**. ⚠️", ephemeral=True)
                    return

                self.db.cursor.execute("SELECT taken_username FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                taken_username = self.db.cursor.fetchone()
                if taken_username is not None:
                    taken_username = taken_username[0]

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
                        self.db.cursor.execute("SELECT embed_color FROM settings WHERE guild_id = ?", (inter.guild.id,))
                        embed_color = self.db.cursor.fetchone()[0]
                        embed_color = disnake.Color(int(embed_color.lstrip('#'), 16))
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
                            embed.add_field(name=":unlock: Открыл", value=creator.mention, inline=True)
                            embed.add_field(name=":lock: Закрыл", value=inter.author.mention, inline=True)
                            embed.add_field(name="", value="", inline=False)
                            staff_member = self.db.cursor.execute("SELECT username FROM staff_list WHERE username = ?", (inter.author.name,)).fetchone()
                            if staff_member is not None:
                                embed.add_field(name=":mag_right: Взял обращение", value=f"<@{inter.author.id}>", inline=True)
                            # embed.add_field(name="Пожалуйста оцените работу сотрудника", value="", inline=False)
                            embed.add_field(name=":pencil: Сообщение", value=reason, inline=False)
                            embed.set_author(name="Yooma Support", icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                            try:
                                await creator.send(embed=embed)
                            except disnake.HTTPException as e:
                                if e.status == 403:
                                    pass

                        if self.taken_username is not None:
                            self.db.cursor.execute("SELECT closed_tickets FROM staff_list WHERE username = ?", (self.taken_username,))
                            closed_tickets = self.db.cursor.fetchone()
                            if closed_tickets is not None:
                                closed_tickets = closed_tickets[0]
                                self.db.cursor.execute("UPDATE staff_list SET closed_tickets = ? WHERE username = ?", (closed_tickets + 1, self.taken_username))
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
                        """, (self.taken_username, date.strftime("%d.%m.%Y")))
                        existing_stat = self.db.cursor.fetchone()
                        if existing_stat is not None:
                            self.db.cursor.execute(""" 
                                UPDATE date_stats SET closed_tickets = ?
                                WHERE username = ? AND date = ?
                            """, (existing_stat[3] + 1, self.taken_username, date.strftime("%d.%m.%Y")))
                        else:
                            self.db.cursor.execute(""" 
                                INSERT INTO date_stats (username, date, closed_tickets)
                                VALUES (?, ?, 1)
                            """, (self.taken_username, date.strftime("%d.%m.%Y")))

                        self.db.conn.commit()
                        self.db.cursor.execute("DELETE FROM created_tickets WHERE thread_id = ?", (inter.channel.id,))
                        self.db.conn.commit()
                        await asyncio.sleep(5)
                        await inter.channel.delete()

                await inter.response.send_modal(CloseTicketModal(taken_username, self.bot))
            except Exception as e:
                logger.error(f"Ошибка при закрытии тикета с причиной {inter.channel.name}: {e}")

        if inter.data.custom_id == "transfer_ticket":

            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            
            self.db.cursor.execute("SELECT status FROM settings WHERE guild_id = ?", (inter.guild.id,))
            status = self.db.cursor.fetchone()
            if status is not None and status[0] == 1:
                await inter.response.send_message("⛔ \ **Технические работы**. Пожалуйста, попробуйте передать обращение **позже**. ⚠️", ephemeral=True)
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