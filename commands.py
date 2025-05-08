import disnake, datetime, logging, random, asyncio
from disnake.ext import commands
from database import Database

from openai import OpenAI

logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

with open('yootoken.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()
    apikey = lines[1].strip()

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
        self.page = 1
        self.stats_message = None
        self.embed_color = disnake.Colour.from_rgb(119, 137, 253)
        self.month_str = None
        self.protected_roles = [
        "💫", "yooma.su", "YooTick",
        "Akemi", "VK Music Bot", "Разработчик",
        "Администратор Discord", "Куратор", "Гл. Администратор", 
        "Ст. Администратор", "Ст. Модератор", "ServerStats",
        "Игрок", "Буст сервера", ""
        ]
    
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
    
    def is_protected_role(self, role):
        if role.name.lower() in [str(x).lower() for x in self.protected_roles]:
            return True
        return False

    def get_completion(self, question: str):
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=apikey,
        )
        try:
            completion = client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{question}. На русском языке"
                            }
                        ]
                    },
                ],
            )
            return completion
        except Exception as e:
            error_data = e.error
            error_message = f"Error {error_data['code']}: {error_data['message']}"
            logger.error(f"[COMMANDS] Ошибка при получении ответа от нейросети: {error_message}")
            return None

    @commands.slash_command(description="Получить ответ от нейросети!")
    async def ai(self, inter, question: str):
        await inter.response.defer()
        db = Database("database.db")
        settings = db.get_settings(guild_id=inter.guild.id)
        aichat_channel_id = settings[6]

        if inter.channel.id != aichat_channel_id:
            await inter.followup.send(f"⚠️ \ Использовать данную команду можно **только в <#{aichat_channel_id}>**")
            return

        loop = asyncio.get_event_loop()
        completion = await loop.run_in_executor(None, self.get_completion, question)

        if hasattr(completion, 'error'):
            await inter.edit_original_response(content="Ошибка: не удалось получить ответ от нейросети")
            logger.error(f"[COMMANDS] Ошибка при получении ответа от нейросети: {completion.error}")
            return

        if len(completion.choices[0].message.content) > 4095:
            chunks = [completion.choices[0].message.content[i:i+4095] for i in range(0, len(completion.choices[0].message.content), 4095)]
            for i, chunk in enumerate(chunks):
                embed = disnake.Embed(
                    title=f"`{question}`",
                    description=f"> Ответ нейросети:\n {chunk}",
                    color=self.embed_color
                )
                embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
                embed.set_footer(text=f"Сгенерированно: Deepseek-V3-0324")
                if i == 0:
                    await inter.edit_original_response(embed=embed)
                else:
                    await inter.followup.send(embed=embed)
        else:
            embed = disnake.Embed(
                title=f"`{question}`",
                description=f"> Ответ нейросети:\n {completion.choices[0].message.content}",
                color=self.embed_color
            )
            embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
            embed.set_footer(text=f"Сгенерированно: Deepseek-V3-0324")
            await inter.edit_original_response(embed=embed)


    @commands.slash_command(description="[STAFF] - Попросить пользователя написать тикет")
    async def proofs(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /fastcommands, но не имеет прав")
            return
        await inter.response.send_message(f"Написал {user.mention} в личные сообщение о просьбе создать тикет.", ephemeral=True)
        embed = disnake.Embed(
            title="Уведомление",
            description=f"Пожалуйста, **напишите тикет** в нашем дискорд сервере.\nИгнорируя данное сообщение вы можете получить **наказание**.",
            color=self.embed_color
        )
        embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
        embed.set_footer(text=f"Отправил: {inter.author.name}")
        view = disnake.ui.View()
        button = disnake.ui.Button(label="Создать тикет", url="https://discord.com/channels/1090281117740961922/1185623131747004446/1359596457115779214")
        view.add_item(button)
        await user.send(embed=embed, view=view)

        
    @commands.slash_command(description="Помощник в выборе. Использование: /choicehelper <вариант1> <вариант2>.. - выберите один из вариантов")
    async def choicehelper(self, inter, *, options: str):
        try:
            options_list = options.split()
            if len(options_list) < 2:
                await inter.response.send_message("Нужно указать хотя бы 2 варианта", ephemeral=True)
                return
            
            animation = [
                "🎲 Выбираем вариант...\n",
                "🔄 Варианты перемешиваются...\n",
                "😈 Подкручиваем самый ужасный исход для вас!\n",
                "🎉 Выбор сделан!\n",
            ]
            
            await inter.response.send_message(animation[0])
            message = await inter.original_response()
            for i in range(1, len(animation)):
                await asyncio.sleep(0.65)
                await message.edit(content=animation[i])
            
            chosen_option = random.choice(options_list)
            chance = 100 / len(options_list)
            await message.edit(content=f"🎉 Выбрано: **{chosen_option}** 🎊\nШанс выпадения: **{chance}%**")
        except Exception as e:
            await inter.followup.send("Ошибка при выборе варианта", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при выборе варианта: {e}")

    @commands.slash_command(description="Показать пинг обработки бота")
    async def ping(self, inter):
        try:
            await inter.response.send_message(f"Pong: {self.bot.latency * 1000:.2f}ms")
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /ping")
        except Exception as e:
            await inter.response.send_message("Ошибка при получении пинга", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при получении пинга: {e}")

    @commands.slash_command(description="[DEV] - yootick msg")
    async def staffsettingsmsg(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return

        self.db.cursor.execute("SELECT staff_settings_channel_id FROM settings WHERE guild_id = ?", (inter.guild.id,))
        staff_settings_channel_id = self.db.cursor.fetchone()
        if staff_settings_channel_id is None:
            await inter.response.send_message("Канал для настроек сотрудников не найден!", ephemeral=True)
            return

        staff_settings_channel_id = staff_settings_channel_id[0]
        staff_settings_channel = inter.guild.get_channel(staff_settings_channel_id)
        if staff_settings_channel is None:
            await inter.response.send_message("Канал для настроек сотрудников не найден!", ephemeral=True)
            return

        self.db.cursor.execute("SELECT * FROM created_tickets")
        all_tickets = self.db.cursor.fetchall()
        self.db.cursor.execute("SELECT * FROM created_tickets WHERE taken_username IS NULL")
        free_tickets = self.db.cursor.fetchall()

        embed = disnake.Embed(
            title="Помощник по тикетам",
            description=f"Активные: **{len(all_tickets)}**\nСвободные тикеты: **{len(free_tickets)}**\n\n"
                        f"🔄 - Обновить информацию по тикетам\n"
                        f"🔔 - Пинг при создании тикета\n"
                        f"📝 - Изменить ник в заголовке тикета\n"
                        f"📊 - Просмотреть активные тикеты\n\n"
                        f"⚠️ - Уведомления о норме\n"
                        f"👥 - Управление ролями пользователя",
            color=self.embed_color
        )
        embed.set_author(name='Yooma Support', icon_url="https://static2.tgstat.ru/channels/_0/a1/a1f39d6ec06f314bb9ae1958342ec5fd.jpg")
        
        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(emoji="🔄", custom_id="update_staff_settings", style=disnake.ButtonStyle.gray))
        view.add_item(disnake.ui.Button(emoji="🔔", custom_id="ping", style=disnake.ButtonStyle.gray))
        view.add_item(disnake.ui.Button(emoji="📝", custom_id="ticket_name", style=disnake.ButtonStyle.gray))
        view.add_item(disnake.ui.Button(emoji="📊", custom_id="active_tickets", style=disnake.ButtonStyle.gray))
        view.add_item(disnake.ui.Button(emoji="⚠️", custom_id="daily_quota", style=disnake.ButtonStyle.gray, row=1))
        view.add_item(disnake.ui.Button(emoji="👥", custom_id="manage_roles", style=disnake.ButtonStyle.gray, row=1))
        
        await staff_settings_channel.send(embed=embed, view=view)
        await inter.response.send_message("Сообщение отправлено!", ephemeral=True)

    @commands.slash_command(description="[DEV] - workshopmsg")
    async def workshopmsg(self, inter: disnake.ApplicationCommandInteraction):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return

        embed = disnake.Embed(
            title="📝 Форма обращения",
            description="Пожалуйста, выберите уровень важности вашей проблемы:",
            color=self.embed_color
        )
        embed.add_field(
            name="Уровни важности",
            value="📣 Низкий - мелкие проблемы, не срочные вопросы\n"
                "⚠️ Средний - важные вопросы, требующие внимания\n"
                "🚨 Высокий - критические проблемы, требующие скорейшего решения",
            inline=False
        )
        
        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(emoji="📣", style=disnake.ButtonStyle.gray, custom_id="low_priority"))
        view.add_item(disnake.ui.Button(emoji="⚠️", style=disnake.ButtonStyle.gray, custom_id="medium_priority"))
        view.add_item(disnake.ui.Button(emoji="🚨", style=disnake.ButtonStyle.gray, custom_id="high_priority"))
        
        await inter.response.send_message(embed=embed, view=view)
        

    @commands.slash_command(description="[LIMITED-ROLES] Показать доступные быстрые команды")
    async def fastcommands(self, inter):
        try:
            allowed_roles = {"спонсор", "модератор серверов", "юмабой", "юмагерл"}
            has_allowed_role = any(role.name.lower() in allowed_roles for role in inter.author.roles)
            if not (self.check_staff_permissions(inter, "staff") or 
                self.check_staff_permissions(inter, "dev") or 
                has_allowed_role):
                await inter.response.send_message(
                    "У вас нет прав для использования этой команды", 
                    ephemeral=True
                )
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /fastcommands, но не имеет прав")
                return
            self.db.cursor.execute("SELECT command_name, description FROM fast_commands")
            fast_commands = self.db.cursor.fetchall()
            embed = disnake.Embed(title="Доступные быстрые команды", color=self.embed_color)
            for command in fast_commands:
                embed.add_field(name=f".{command[0]}", value=command[1], inline=False)
                
            await inter.response.send_message(embed=embed)
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} успешно использовал команду /fastcommands")
            
        except Exception as e:
            await inter.response.send_message(
                "Ошибка при получении списка быстрых команд", 
                ephemeral=True
            )
            logger.error(f"[COMMANDS] Ошибка при получении списка быстрых команд: {e}")
            

    @commands.slash_command(description="[DEV] - Установить статус тех.работ")
    async def status(self, inter, value: int):
        try:
            if not self.check_staff_permissions(inter, "dev"):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            if value not in [0, 1]:
                await inter.response.send_message("Неправильное значение. Должно быть 0 или 1", ephemeral=True)
                return
            self.db.cursor.execute("SELECT * FROM settings WHERE guild_id = ?", (inter.guild.id,))
            existing_settings = self.db.cursor.fetchone()
            if existing_settings is not None:
                self.db.cursor.execute("UPDATE settings SET status = ? WHERE guild_id = ?", (value, inter.guild.id))
            else:
                self.db.cursor.execute("INSERT INTO settings (guild_id, status) VALUES (?, ?)", (inter.guild.id, value))
            self.db.conn.commit()
            if value == 0:
                await inter.response.send_message("Статус тех.работ изменен на False.")
            elif value == 1:
                await inter.response.send_message("Статус тех.работ изменен на True.")
        except Exception as e:
            await inter.followup.send("Ошибка при установке статуса тех.работ")


    @commands.slash_command(description="[STAFF] - Удалить обращение из базы данных")
    async def ticket_fix(self, inter, username: str):
        try:
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /ticket_fix, но не имеет прав")
                return
            self.db.cursor.execute("SELECT * FROM created_tickets WHERE creator_username = ?", (username,))
            existing_ticket = self.db.cursor.fetchone()
            if existing_ticket is None:
                await inter.response.send_message("Обращение не найдено!", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /ticket_fix, но обращение не найдено")
                return
            self.db.cursor.execute("DELETE FROM created_tickets WHERE creator_username = ?", (username,))
            self.db.conn.commit()
            await inter.response.send_message(f"Обращение пользователя {username} удалено из базы данных", ephemeral=True)
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} успешно использовал команду /ticket_fix")
        except Exception as e:
            await inter.response.send_message("Ошибка при удалении обращения", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при удалении обращения: {e}")

    @commands.slash_command(description="[STAFF] - Просмотр цен")
    async def price(self, inter):
        try:
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /price, но не имеет прав")
                return
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите пункт",
                custom_id="price_select",
                options=[
                    disnake.SelectOption(label="Докупка", value="докупка"),
                    disnake.SelectOption(label="Дополнительные услуги", value="дополнительные услуги"),
                    disnake.SelectOption(label="Авто-подсчет возврата", value="авто-подсчет возврата"),
                ]
            )
            select_menu.callback = self.price_callback
            view.add_item(select_menu)
            await inter.response.send_message("", view=view)
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} успешно использовал команду /price")
        except Exception as e:
            await inter.response.send_message("Ошибка при получении списка цен", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при получении списка цен: {e}")

    async def price_callback(self, inter):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        if inter.data.values[0] == "докупка":
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите тип",
                custom_id="type_select",
                options=[
                    disnake.SelectOption(label="Админ", value="admin"),
                    disnake.SelectOption(label="Вип", value="vip"),
                    disnake.SelectOption(label="Назад", value="назад")
                ]
            )
            select_menu.callback = self.type_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="", view=view)
        elif inter.data.values[0] == "дополнительные услуги":
            embed = disnake.Embed(title="Дополнительные услуги", color=self.embed_color)
            embed.add_field(name="Перенос админ/вип привилегии", value="150р", inline=False)
            embed.add_field(name="Размут на сайте", value="200р", inline=False)
            embed.add_field(name="Разморозка прав для админов", value="350р", inline=False)
            embed.add_field(name="Разморозка прав для спонсора", value="750р", inline=False)
            await inter.response.edit_message(embed=embed)
        elif inter.data.values[0] == "авто-подсчет возврата":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            modal = disnake.ui.Modal(
                title="Авто-подсчет возврата",
                custom_id="refund_modal",
                components=[
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Цена покупки админки",
                            placeholder="1337",
                            custom_id="price_input",
                            style=disnake.TextInputStyle.short,
                        )
                    ),
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Дата покупки админки (дд.мм.гггг)",
                            placeholder="12.09.2024",
                            custom_id="date_input",
                            style=disnake.TextInputStyle.short,
                        )
                    ),
                ],
            )

            await inter.response.send_modal(modal)

    async def type_callback(self, inter):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return

        if inter.data.values[0] == "назад":
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите пункт",
                custom_id="price_select",
                options=[
                    disnake.SelectOption(label="Докупка", value="докупка"),
                    disnake.SelectOption(label="Дополнительные услуги", value="дополнительные услуги"),
                    disnake.SelectOption(label="Авто-подсчет возврата", value="авто-подсчет возврата"),
                ]
            )
            select_menu.callback = self.price_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="", view=view)
        elif inter.data.values[0] == "admin":
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите уровень",
                custom_id="admin_level_select",
                options=[
                    disnake.SelectOption(label="1lvl", value="1lvl"),
                    disnake.SelectOption(label="2lvl", value="2lvl"),
                    disnake.SelectOption(label="Назад", value="назад")
                ]
            )
            select_menu.callback = self.admin_level_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="", view=view)
        elif inter.data.values[0] == "vip":
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите уровень",
                custom_id="vip_level_select",
                options=[
                    disnake.SelectOption(label="Medium", value="medium"),
                    disnake.SelectOption(label="Platinum", value="platinum"),
                    disnake.SelectOption(label="Crystal", value="crystal"),
                    disnake.SelectOption(label="Назад", value="назад")
                ]
            )
            select_menu.callback = self.vip_level_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="", view=view)

    async def vip_level_callback(self, inter):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return

        if inter.data.values[0] == "назад":
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите тип",
                custom_id="type_select",
                options=[
                    disnake.SelectOption(label="Админ", value="admin"),
                    disnake.SelectOption(label="Вип", value="vip"),
                    disnake.SelectOption(label="Назад", value="назад")
                ]
            )
            select_menu.callback = self.type_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="", view=view)
        else:
            self.db.cursor.execute("SELECT vip_medium_price, vip_platinum_price, vip_crystal_price, vip_crystalplus_price FROM price_list")
            prices = self.db.cursor.fetchone()
            if prices is None:
                await inter.response.send_message("Цены не найдены!", ephemeral=True)
                return
            vip_medium_price = prices[0]
            vip_platinum_price = prices[1]
            vip_crystal_price = prices[2]
            vip_crystalplus_price = prices[3]
            embed = disnake.Embed(title="Докупка випа", color=self.embed_color)
            if inter.data.values[0] == "medium":
                embed.add_field(name="С Medium на Platinum", value=f"{vip_platinum_price - vip_medium_price}р", inline=False)
                embed.add_field(name="С Medium на Crystal", value=f"{vip_crystal_price - vip_medium_price}р", inline=False)
                embed.add_field(name="С Medium на Crystal+", value=f"{vip_crystalplus_price - vip_medium_price}р", inline=False)
            elif inter.data.values[0] == "platinum":
                embed.add_field(name="С Platinum на Crystal", value=f"{vip_crystal_price - vip_platinum_price}р", inline=False)
                embed.add_field(name="С Platinum на Crystal+", value=f"{vip_crystalplus_price - vip_platinum_price}р", inline=False)
            elif inter.data.values[0] == "crystal":
                embed.add_field(name="С Crystal на Crystal+", value=f"{vip_crystalplus_price - vip_crystal_price}р", inline=False)
            await inter.response.edit_message(embed=embed)

    async def admin_level_callback(self, inter):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return

        if inter.data.values[0] == "назад":
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите тип",
                custom_id="type_select",
                options=[
                    disnake.SelectOption(label="Админ", value="admin"),
                    disnake.SelectOption(label="Вип", value="vip"),
                    disnake.SelectOption(label="Назад", value="назад")
                ]
            )
            select_menu.callback = self.type_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="", view=view)
        else:
            self.db.cursor.execute("SELECT admin_1lvl_price, admin_2lvl_price, sponsor_price FROM price_list")
            prices = self.db.cursor.fetchone()
            if prices is None:
                await inter.response.send_message("Цены не найдены!", ephemeral=True)
                return
            admin_1lvl_price = prices[0]
            admin_2lvl_price = prices[1]
            sponsor_price = prices[2]
            embed = disnake.Embed(title="Докупка админки", color=self.embed_color)
            if inter.data.values[0] == "1lvl":
                price_diff_2lvl = admin_2lvl_price - admin_1lvl_price
                price_diff_sponsor = sponsor_price - admin_1lvl_price
                embed.add_field(name="С 1lvl на 2lvl", value=f"{price_diff_2lvl}р", inline=False)
                embed.add_field(name="С 1lvl на Sponsor", value=f"{price_diff_sponsor}р", inline=False)
            elif inter.data.values[0] == "2lvl":
                price_diff_sponsor = sponsor_price - admin_2lvl_price
                embed.add_field(name="С 2lvl на Sponsor", value=f"{price_diff_sponsor}р", inline=False)
            await inter.response.edit_message(embed=embed)
    

    @commands.slash_command(description="[DEV] - Просмотр статистики по дате")
    async def date_stats(self, inter):
        try:
            if not self.check_staff_permissions(inter, "dev"):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /date_stats, но не имеет прав")
                return

            modal = disnake.ui.Modal(
                title="Просмотр статистики",
                custom_id="date_stats_modal",
                components=[
                    disnake.ui.TextInput(
                        label="Введите дату (ДД.ММ.ГГГГ)",
                        placeholder="Например: 23.05.2025",
                        custom_id="date_input",
                        style=disnake.TextInputStyle.short,
                        max_length=10
                    )
                ]
            )
            await inter.response.send_modal(modal)
            
        except Exception as e:
            await inter.response.send_message("Ошибка при открытии модального окна", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при открытии модального окна: {e}")

    @commands.slash_command(description="[DEV] - Статистика сотрудников")
    async def stats(self, inter):
        try:
            if not self.check_staff_permissions(inter, "dev"):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /stats, но не имеет прав")
                return
            self.page = 1
            self.db.cursor.execute("SELECT * FROM staff_list")
            staff_members = self.db.cursor.fetchall()
            staff_members.sort(key=lambda x: x[5], reverse=True)
            embed = disnake.Embed(
                title="Статистика сотрудников",
                description=f"Открыта страница: {self.page} из {len(staff_members) // 5 + 1}",
                color=self.embed_color
            )
            start = (self.page - 1) * 5
            end = self.page * 5
            for i, staff_member in enumerate(staff_members[start:end], start=1):
                username = staff_member[1]
                role = staff_member[4]
                embed.add_field(
                    name=f"{i}. {username}",
                    value=f"🪪 Роль: {role}\n🎫 Закрытых тикетов: **Секрет**",
                    inline=False
                )
            view = disnake.ui.View()
            left_button = disnake.ui.Button(label="⬅️", custom_id="left", style=disnake.ButtonStyle.gray)
            right_button = disnake.ui.Button(label="➡️", custom_id="right", style=disnake.ButtonStyle.gray)
            secret_button = disnake.ui.Button(label="Открыть секрет", custom_id="secret", style=disnake.ButtonStyle.red)
            view.add_item(left_button)
            view.add_item(right_button)
            view.add_item(secret_button)
            self.stats_message = await inter.response.send_message(embed=embed, view=view)
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} успешно использовал команду /stats")
        except Exception as e:
            await inter.response.send_message("Ошибка при получении статистики сотрудников", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при получении статистики сотрудников: {e}")

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        if inter.data.custom_id.startswith("workshop_approve_"):
            await inter.message.delete()
            await inter.response.send_message(
                f"Обращение - принято, удалил",
                ephemeral=True
            )
        if inter.data.custom_id.startswith("workshop_reject_"):
            await inter.message.delete()
            await inter.response.send_message(
                f"Обращение - хуйня, удалил",
                ephemeral=True
            )

        if inter.data.custom_id in ["low_priority", "medium_priority", "high_priority"]:
            priority_level = inter.data.custom_id.split("_")[0]
            
            modal = disnake.ui.Modal(
                title=f"Обращение ({priority_level} приоритет)",
                custom_id=f"workshop_modal_{priority_level}",
                components=[
                    disnake.ui.TextInput(
                        label="Тема проблемы",
                        placeholder="К примеру: маркет скинов",
                        custom_id="problem_title",
                        style=disnake.TextInputStyle.short,
                        max_length=100,
                        required=True
                    ),
                    disnake.ui.TextInput(
                        label="Описание проблемы",
                        placeholder="К примеру: ошибка - недостаточно средств, нужен додеп",
                        custom_id="problem_description",
                        style=disnake.TextInputStyle.paragraph,
                        max_length=2000,
                        required=True
                    ),
                    disnake.ui.TextInput(
                        label="Ссылка на изображение (необязательно)",
                        placeholder="https://example.com/image.png",
                        custom_id="image_url",
                        style=disnake.TextInputStyle.long,
                        required=False
                    )
                ]
            )
            await inter.response.send_modal(modal)

        if inter.data.custom_id == "manage_roles":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("❌ Недостаточно прав", ephemeral=True)
                return
            
            modal = disnake.ui.Modal(
                title="Управление ролями",
                custom_id="role_management_modal",
                components=[
                    disnake.ui.TextInput(
                        label="Введите юзернейм участника",
                        placeholder="Введите юзернейм (e.g anarchowitz)",
                        custom_id="target_username",
                        style=disnake.TextInputStyle.short,
                        max_length=32
                    )
                ]
            )
            await inter.response.send_modal(modal)
        if inter.data.custom_id == "update_staff_settings":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            self.db.cursor.execute("SELECT * FROM created_tickets")
            all_tickets = self.db.cursor.fetchall()
            self.db.cursor.execute("SELECT * FROM created_tickets WHERE taken_username IS NULL")
            free_tickets = self.db.cursor.fetchall()

            embed = disnake.Embed(
                title="Помощник по тикетам",
                description=f"Активные: **{len(all_tickets)}**\nСвободные тикеты: **{len(free_tickets)}**\n\n"
                            f"🔄 - Обновить информацию по тикетам\n"
                            f"🔔 - Пинг при создании тикета\n"
                            f"📝 - Изменить ник в заголовке тикета\n"
                            f"📊 - Просмотреть активные тикеты\n\n"
                            f"⚠️ - Уведомления о норме\n"
                            f"👥 - Управление ролями пользователя",
                color=self.embed_color
            )
            await inter.message.edit(embed=embed)
            await inter.response.defer()
        elif inter.data.custom_id == "ping":
            self.db.cursor.execute("SELECT mention FROM staff_list WHERE username = ?", (inter.author.name,))
            mention = self.db.cursor.fetchone()
            if mention is not None:
                mention = mention[0]
                if mention == 0:
                    self.db.cursor.execute("UPDATE staff_list SET mention = 1 WHERE username = ?", (inter.author.name,))
                else:
                    self.db.cursor.execute("UPDATE staff_list SET mention = 0 WHERE username = ?", (inter.author.name,))
                self.db.conn.commit()
                await inter.response.send_message(f"Пинг при создании тикета включен для {inter.author.mention}" if mention == 0 else f"Пинг при создании тикета выключен для {inter.author.mention}", ephemeral=True)
        elif inter.data.custom_id == "ticket_name":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            modal = disnake.ui.Modal(
                title="Изменить ник тикета",
                custom_id="ticket_name_modal",
                components=[
                    disnake.ui.ActionRow(
                        disnake.ui.TextInput(
                            label="Новый ник в заголовке тикета",
                            placeholder="К примеру: anarcho",
                            custom_id="ticket_name_input",
                            style=disnake.TextInputStyle.short,
                        )
                    ),
                ],
            )
            await inter.response.send_modal(modal)
            self.bot.add_modal_handler(self.ticket_name_modal_callback)
        elif inter.data.custom_id == "ping":
            self.db.cursor.execute("SELECT mention FROM staff_list WHERE username = ?", (inter.author.name,))
            mention = self.db.cursor.fetchone()
            if mention is not None:
                mention = mention[0]
                if mention == 0:
                    self.db.cursor.execute("UPDATE staff_list SET mention = 1 WHERE username = ?", (inter.author.name,))
                else:
                    self.db.cursor.execute("UPDATE staff_list SET mention = 0 WHERE username = ?", (inter.author.name,))
                self.db.conn.commit()
                await inter.response.send_message(f"Пинг при создании тикета включен для {inter.author.mention}" if mention == 0 else f"Пинг при создании тикета выключен для {inter.author.mention}", ephemeral=True)
        elif inter.data.custom_id == "daily_quota":
            self.db.cursor.execute("SELECT daily_quota FROM staff_list WHERE username = ?", (inter.author.name,))
            daily_quota = self.db.cursor.fetchone()
            if daily_quota is not None:
                daily_quota = daily_quota[0]
                if daily_quota == 0:
                    self.db.cursor.execute("UPDATE staff_list SET daily_quota = 1 WHERE username = ?", (inter.author.name,))
                else:
                    self.db.cursor.execute("UPDATE staff_list SET daily_quota = 0 WHERE username = ?", (inter.author.name,))
                self.db.conn.commit()
                await inter.response.send_message(f"Пинг в 18:00 (MSK) при невыполненнии нормы включен для {inter.author.mention}" if daily_quota == 0 else f"Пинг в 18:00 (MSK) при невыполненнии нормы выключен для {inter.author.mention}", ephemeral=True)

        elif inter.data.custom_id == "active_tickets":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            self.db.cursor.execute("SELECT thread_id FROM created_tickets WHERE taken_username = ?", (inter.author.name,))
            active_tickets = self.db.cursor.fetchall()
            if active_tickets:
                embed = disnake.Embed(
                    title="Активные тикеты",
                    description="Список активных тикетов, которые вы взяли:",
                    color=self.embed_color
                )
                for ticket in active_tickets:
                    embed.add_field(name=f"Тикет", value=f"<#{ticket[0]}>", inline=False)
                await inter.response.send_message(embed=embed, ephemeral=True)
            else:
                await inter.response.send_message("У вас нет активных тикетов", ephemeral=True)

        if inter.data.custom_id == "left":
            if not self.check_staff_permissions(inter, "dev"):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            if self.page > 1:
                self.page -= 1
                self.db.cursor.execute("SELECT * FROM staff_list")
                staff_members = self.db.cursor.fetchall()
                staff_members.sort(key=lambda x: x[5], reverse=True)

                embed = disnake.Embed(
                    title="Статистика сотрудников",
                    description=f"Открыта страница: {self.page} из {len(staff_members) // 5 + 1}",
                    color=self.embed_color
                )

                start = (self.page - 1) * 5
                end = self.page * 5

                for i, staff_member in enumerate(staff_members[start:end], start=1):
                    username = staff_member[1]
                    role = staff_member[4]
                    closed_tickets = staff_member[5]

                    embed.add_field(
                        name=f"{(self.page - 1) * 5 + i}. {username}",
                        value=f"🪪 Роль: {role}\n🎫 Закрытых тикетов: **Секрет**",
                        inline=False
                    )

                await inter.message.edit(embed=embed)
                await inter.response.defer()

        elif inter.data.custom_id == "right":
            if not self.check_staff_permissions(inter, "dev"):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            self.page += 1
            self.db.cursor.execute("SELECT * FROM staff_list")
            staff_members = self.db.cursor.fetchall()
            staff_members.sort(key=lambda x: x[5], reverse=True)

            embed = disnake.Embed(
                title="Статистика сотрудников",
                description=f"Открыта страница: {self.page} из {len(staff_members) // 5 + 1}",
                color=self.embed_color
            )

            start = (self.page - 1) * 5
            end = self.page * 5

            for i, staff_member in enumerate(staff_members[start:end], start=1):
                username = staff_member[1]
                role = staff_member[4]
                closed_tickets = staff_member[5]

                embed.add_field(
                    name=f"{(self.page - 1) * 5 + i}. {username}",
                    value=f"🪪 Роль: {role}\n🎫 Закрытых тикетов: **Секрет**",
                    inline=False
                )

            await inter.message.edit(embed=embed)
            await inter.response.defer()

        elif inter.data.custom_id == "secret":
            if not self.check_staff_permissions(inter, "dev"):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            self.db.cursor.execute("SELECT * FROM staff_list")
            staff_members = self.db.cursor.fetchall()
            staff_members.sort(key=lambda x: x[5], reverse=True)

            embed = disnake.Embed(
                title="Статистика сотрудников",
                description=f"Открыта страница: {self.page} из {len(staff_members) // 5 + 1}",
                color=self.embed_color
            )

            start = (self.page - 1) * 5
            end = self.page * 5

            for i, staff_member in enumerate(staff_members[start:end], start=1):
                username = staff_member[1]
                role = staff_member[4]
                closed_tickets = staff_member[5]

                embed.add_field(
                    name=f"{(self.page - 1) * 5 + i}. {username}",
                    value=f"🪪 Роль: {role}\n🎫 Закрытых тикетов: {closed_tickets}",
                    inline=False
                )

            if self.stats_message is not None:
                await self.stats_message.edit(embed=embed)
            else:
                await inter.message.edit(embed=embed)
            await inter.response.defer()



    @commands.slash_command(description="[DEV] - Настроить бота")
    async def settings(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        if inter.guild is None:
            await inter.response.send_message("Эта команда может быть использована только на сервере", ephemeral=True)
            return
        modal = disnake.ui.Modal(
            title="Настройки",
            custom_id="settings_modal",
            components=[
                disnake.ui.ActionRow(
                    disnake.ui.TextInput(
                        label="Цвет боковой полоски (В HEX)",
                        placeholder="#7789fd",
                        custom_id="color",
                        style=disnake.TextInputStyle.short,
                    )
                ),
                disnake.ui.ActionRow(
                    disnake.ui.TextInput(
                        label="Айди категории тикетов",
                        placeholder="1234567890",
                        custom_id="category_id",
                        style=disnake.TextInputStyle.short,
                    )
                ),
                disnake.ui.ActionRow(
                    disnake.ui.TextInput(
                        label="Айди канала для разработчиков",
                        placeholder="1234567890",
                        custom_id="dev_channel_id",
                        style=disnake.TextInputStyle.short,
                    )
                ),
                disnake.ui.ActionRow(
                    disnake.ui.TextInput(
                        label="Айди канала тикетов",
                        placeholder="1234567890",
                        custom_id="channel_id",
                        style=disnake.TextInputStyle.short,
                    )
                ),
                disnake.ui.ActionRow(
                    disnake.ui.TextInput(
                        label="Рабочее время",
                        placeholder="10:00 - 20:00",
                        custom_id="primetime",
                        style=disnake.TextInputStyle.short,
                    )
                ),
            ],
        )

        await inter.response.send_modal(modal)

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.data.custom_id == "refund_modal":
            try:
                price = int(inter.text_values['price_input'])
                date_str = inter.text_values['date_input']
                
                try:
                    purchase_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                except ValueError:
                    await inter.response.send_message("⚠ Неверный формат даты! Используйте ДД.ММ.ГГГГ", ephemeral=True)
                    return
                current_date = datetime.date.today()
                days_used = (current_date - purchase_date).days
                if days_used < 0:
                    await inter.response.send_message("⚠ Дата покупки не может быть в будущем!", ephemeral=True)
                    return
                guaranteed_deduction = price / 3 
                
                daily_deduction_rate = 100 / 30  # 3.33 руб в день
                time_deduction = daily_deduction_rate * days_used
                refund = max(0, (price - guaranteed_deduction) - time_deduction)

                await inter.response.edit_message(
                    f"💸 **Авто-подсчет возврата**:\n"
                    f"Цена покупки: `{price}₽`\n"
                    f"Вычет за использование: `{int(time_deduction)}₽`\n\n"
                    f"Итого к возврату: `{int(refund)}₽`",
                    view=None
                )
                
            except ValueError:
                await inter.response.send_message("⚠ Ошибка в данных! Убедитесь что цена - число, а дата в формате ДД.ММ.ГГГГ", ephemeral=True)

        if inter.data.custom_id.startswith("workshop_modal_"):
            priority_level = inter.data.custom_id.split("_")[2]
            priority_colors = {
                "low": disnake.Colour.blue(),
                "medium": disnake.Colour.gold(),
                "high": disnake.Colour.red()
            }
            
            title = inter.text_values["problem_title"]
            description = inter.text_values["problem_description"]
            image_url = inter.text_values.get("image_url", "").strip()
            
            embed = disnake.Embed(
                title=f"Тема: {title}",
                description=description,
                color=priority_colors[priority_level]
            )
            embed.set_author(name=f"Приоритет: {priority_level.capitalize()}")
            embed.set_footer(text=f"Отправил: {inter.author.display_name}")
            
            view = disnake.ui.View()
            view.add_item(disnake.ui.Button(emoji="✅", custom_id=f"workshop_approve_{inter.author.id}", style=disnake.ButtonStyle.gray))
            view.add_item(disnake.ui.Button(emoji="💩", custom_id=f"workshop_reject_{inter.author.id}", style=disnake.ButtonStyle.gray))
            
            if priority_level == "high":
                high_priority_user_id = 296675294092197889
                try:
                    user = await self.bot.fetch_user(high_priority_user_id)
                    dm_channel = await user.create_dm()
                    
                    if image_url:
                        await dm_channel.send(
                            content=f"Изображение: {image_url}",
                            embed=embed,
                            view=view
                        )
                    else:
                        await dm_channel.send(
                            embed=embed,
                            view=view
                        )
                        
                    await inter.response.send_message(
                        "Ваше обращение было отправлено в личные сообщения разработчику!",
                        ephemeral=True
                    )
                except Exception as e:
                    await inter.response.send_message(
                        "Не удалось отправить обращение. Пожалуйста, сообщите администратору.",
                        ephemeral=True
                    )
                    logger.error(f"Ошибка отправки high priority сообщения: {e}")
            else:
                if image_url:
                    await inter.channel.send(
                        content=f"Изображение: {image_url}",
                        embed=embed,
                        view=view
                    )
                else:
                    await inter.channel.send(
                        embed=embed,
                        view=view
                    )
                    
                await inter.response.send_message(
                    "Ваше обращение отправлено!",
                    ephemeral=True
                )
                
        if inter.data.custom_id == "role_management_modal":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("❌ Недостаточно прав", ephemeral=True)
                return
                
            target_username = inter.text_values["target_username"].strip()
            member = None
            for guild_member in inter.guild.members:
                if guild_member.name.lower() == target_username.lower():
                    member = guild_member
                    break
            
            if not member:
                await inter.response.send_message(
                    f"❌ Пользователь с ником '{target_username}' не найден на сервере",
                    ephemeral=True
                )
                return
                
            roles = [
                role for role in member.roles 
                if role != inter.guild.default_role and not self.is_protected_role(role)
            ]
            
            if not roles:
                await inter.response.send_message(
                    f"❌ У пользователя {target_username} нет ролей, которые можно удалить",
                    ephemeral=True
                )
                return
                
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите роль для удаления",
                custom_id=f"remove_role_{member.id}"
            )
            
            for role in roles:
                select_menu.add_option(
                    label=role.name,
                    value=str(role.id),
                    description=f"Удалить роль {role.name}"
                )
                
            view.add_item(select_menu)
            select_menu.callback = self.remove_role_callback
            
            await inter.response.send_message(
                f"Выберите роль для удаления у пользователя {member.mention}",
                view=view,
                ephemeral=True
            )
        if inter.data.custom_id == "date_stats_modal":
            try:
                date = inter.text_values['date_input']
                try:
                    day, month, year = map(int, date.split('.'))
                    datetime.datetime.strptime(date, "%d.%m.%Y")
                except ValueError:
                    await inter.response.send_message("⚠ Неверный формат даты! Используйте ДД.ММ.ГГГГ (например 23.05.2025)", ephemeral=True)
                    return
                self.db.cursor.execute("""
                    SELECT username, closed_tickets 
                    FROM date_stats 
                    WHERE date = ?
                    ORDER BY closed_tickets DESC
                """, (date,))
                
                stats = self.db.cursor.fetchall()
                if not stats:
                    await inter.response.send_message(f"Статистика за {date} не найдена!", ephemeral=True)
                    return
                embed = disnake.Embed(
                    title=f"📊 Статистика за {date}",
                    color=self.embed_color
                )
                total_closed = 0
                for username, closed_tickets in stats:
                    embed.add_field(
                        name=f"👤 {username}",
                        value=f"Закрыто тикетов: {closed_tickets}",
                        inline=False
                    )
                    total_closed += closed_tickets
                
                embed.set_footer(text=f"Всего закрыто тикетов: {total_closed}")
                
                await inter.response.send_message(embed=embed)
                
            except Exception as e:
                await inter.response.send_message("Ошибка при получении статистики", ephemeral=True)
                logger.error(f"[COMMANDS] Ошибка при обработке статистики: {e}")
        if inter.data.custom_id == "ticket_name_modal":
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            new_ticket_name = inter.text_values['ticket_name_input']
            self.db.cursor.execute("UPDATE staff_list SET ticket_name = ? WHERE username = ?", (new_ticket_name, inter.author.name))
            self.db.conn.commit()
            await inter.response.send_message(f"Ник в заголовке тикета изменен на {new_ticket_name}", ephemeral=True)

        if inter.data.custom_id == "settings_modal":
            color = inter.text_values['color']
            category_id = int(inter.text_values['category_id'])
            channel_id = int(inter.text_values['channel_id'])
            primetime = str(inter.text_values['primetime'])

            category = inter.guild.get_channel(category_id)
            channel = inter.guild.get_channel(channel_id)

            if category is None:
                await inter.response.send_message("Категория с таким ID введённом не найдена на сервере!")
                return

            if channel is None:
                await inter.response.send_message("Канал с таким ID введённом не найден на сервере!")
                return

            self.db.cursor.execute(""" 
                SELECT * FROM settings WHERE guild_id = ?
            """, (inter.guild.id,))
            existing_settings = self.db.cursor.fetchone()

            if existing_settings is not None:
                self.db.cursor.execute(""" 
                    UPDATE settings SET embed_color = ?, category_id = ?, ticket_channel_id = ?, primetime = ?, logging = ?
                    WHERE guild_id = ?
                """, (color, category_id, channel_id, primetime, inter.guild.id))
            else:
                self.db.cursor.execute(""" 
                    INSERT INTO settings (guild_id, embed_color, category_id, ticket_channel_id, primetime, logging)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (inter.guild.id, color, category_id, channel_id, primetime))

            self.db.conn.commit()

            await inter.response.send_message(
                embed=disnake.Embed(title="Настройки сохранены", description=f"Цвет боковой полоски: {color}\n"
                f"Айди категории тикетов: {category_id}\n"
                f"Айди канала тикетов: {channel_id}\n"
                f"Рабочее время: {primetime}\n",
                color=self.embed_color),
                ephemeral=True
            )
    async def remove_role_callback(self, inter: disnake.MessageInteraction):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("❌ Недостаточно прав", ephemeral=True)
            return
            
        custom_id_parts = inter.data.custom_id.split("_")
        if len(custom_id_parts) != 3:
            await inter.response.send_message("❌ Ошибка обработки запроса", ephemeral=True)
            return
            
        target_user_id = int(custom_id_parts[2])
        role_id = int(inter.data.values[0])
        
        member = inter.guild.get_member(target_user_id)
        role = inter.guild.get_role(role_id)
        
        if not member or not role:
            await inter.response.send_message("❌ Пользователь или роль не найдены", ephemeral=True)
            return
        
        # Проверяем, является ли роль защищенной
        if self.is_protected_role(role):
            await inter.response.send_message(
                f"❌ Роль {role.name} защищена и не может быть удалена!",
                ephemeral=True
            )
            return
            
        try:
            await member.remove_roles(role)
            await inter.response.send_message(
                f"✅ Роль {role.name} успешно удалена у пользователя {member.mention}",
                ephemeral=True
            )
            logger.info(f"[ROLE] {inter.author} удалил роль {role.name} у {member}")
        except Exception as e:
            await inter.response.send_message(
                f"❌ Ошибка при удалении роли: {str(e)}",
                ephemeral=True
            )

def setupcommands(bot):
    bot.add_cog(Settings(bot))