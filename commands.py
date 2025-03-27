import disnake, datetime, logging, random, asyncio
from math import ceil
from disnake.ext import commands
from database import Database

logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
        self.page = 1
        self.stats_message = None
        self.embed_color = disnake.Colour.from_rgb(119, 137, 253)

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
            await inter.response.send_message(f"Пинг: {self.bot.latency * 1000:.2f}ms", ephemeral=True)
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /ping")
        except Exception as e:
            await inter.response.send_message("Ошибка при получении пинга", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при получении пинга: {e}")

    @commands.slash_command(description="[STAFF] - Показать доступные быстрые команды")
    async def fastcommands(self, inter):
        try:
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
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
            await inter.response.send_message("Ошибка при получении списка быстрых команд", ephemeral=True)
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
                await inter.response.send_message("Тех.работы завершены. Доступ к некоторым действиям разрешен.")
            elif value == 1:
                await inter.response.send_message("Тех.работы проводятся. Доступ к некоторым действиям запрещен.")
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

    @commands.slash_command(description="[STAFF] - Установить авто-пинг в тикете")
    async def ticket_ping(self, inter, value: int):
        try:
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /ticket_ping, но не имеет прав")
                return
            if value not in [0, 1]:
                await inter.response.send_message("Неправильное значение. Должно быть 0 или 1", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /ticket_ping с неправильным значением")
                return
            self.db.cursor.execute("SELECT * FROM staff_list WHERE username = ?", (inter.author.name,))
            staff_member = self.db.cursor.fetchone()
            if staff_member is None:
                await inter.response.send_message("Сотрудник не найден!", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /ticket_ping, но сотрудник не найден")
                return
            self.db.cursor.execute("UPDATE staff_list SET mention = ? WHERE username = ?", (value, inter.author.name))
            self.db.conn.commit()
            await inter.response.send_message(f"Авто-пинг в тикете установлен на {value}", ephemeral=True)
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} успешно использовал команду /ticket_ping")
        except Exception as e:
            await inter.response.send_message("Ошибка при установке авто-пинга", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при установке авто-пинга: {e}")

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
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите пункт",
                custom_id="admin_level_select",
                options=[
                    disnake.SelectOption(label="Админ 1 уровня", value="admin_1lvl"),
                    disnake.SelectOption(label="Админ 2 уровня", value="admin_2lvl"),
                    disnake.SelectOption(label="Спонсор", value="sponsor"),
                ]
            )
            select_menu.callback = self.refund_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="", view=view)

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

    async def refund_callback(self, inter):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return

        admin_level = inter.data.values[0]

        modal = disnake.ui.Modal(
            title="Авто-подсчет возврата",
            custom_id="refund_modal",
            components=[
                disnake.ui.ActionRow(
                    disnake.ui.TextInput(
                        label="Уровень админки",
                        placeholder="1lvl или 2lvl или sponsor",
                        custom_id="admin_level_input",
                        style=disnake.TextInputStyle.short,
                        value=admin_level
                    )
                ),
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
        self.bot.add_modal_handler(self.refund_modal_callback)
    

    @commands.slash_command(description="[DEV] - Просмотр статистики по датам")
    async def date_stats(self, inter):
        try:
            if not self.check_staff_permissions(inter, "dev"):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                logger.info(f"[COMMANDS] Пользователь {inter.author.name} пытается использовать команду /date_stats, но не имеет прав")
                return
            self.db.cursor.execute("""
                SELECT DISTINCT date FROM date_stats
                ORDER BY date DESC
            """)
            dates = self.db.cursor.fetchall()
            options = []
            for date in dates:
                date_str = date[0]
                date_str = date_str.replace('-', '.')
                options.append(disnake.SelectOption(label=date_str, value=date_str))
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите дату",
                custom_id="date_select",
                options=options
            )
            select_menu.callback = self.date_stats_callback
            view.add_item(select_menu)
            await inter.response.send_message("Выберите дату", view=view)
            logger.info(f"[COMMANDS] Пользователь {inter.author.name} успешно использовал команду /date_stats")
        except Exception as e:
            await inter.response.send_message("Ошибка при получении списка дат", ephemeral=True)
            logger.error(f"[COMMANDS] Ошибка при получении списка дат: {e}")

    async def date_stats_callback(self, inter):
        date_str = inter.data.values[0]
        date_str = date_str.replace('-', '.')
        date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

        self.db.cursor.execute(""" 
            SELECT username, SUM(closed_tickets) AS total_closed
            FROM date_stats
            WHERE date = ?
            GROUP BY username
            ORDER BY total_closed DESC
        """, (date.strftime("%d.%m.%Y"),))
        stats = self.db.cursor.fetchall()

        embed = disnake.Embed(title=f"Статистика по датам ({date_str})", color=self.embed_color)
        for username, total_closed in stats:
            embed.add_field(name=username, value=f"Закрыто тикетов: {total_closed}", inline=False)

        await inter.response.edit_message(embed=embed, content="")

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
                await inter.response.send_message("Страница обновлена", ephemeral=True)

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
            await inter.response.send_message("Страница обновлена", ephemeral=True)

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
            await inter.response.send_message("Показал секретик, уххх <3", ephemeral=True)



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
            if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
                await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
                return
            admin_level = inter.text_values['admin_level_input']
            date_str = inter.text_values['date_input']
            date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            price = int(inter.text_values['price_input'])

            current_date = datetime.date.today()
            days_diff = (current_date - date).days
            percent_diff = days_diff * 0.7

            guaranteed_refund = price / 3
            remaining_price = price - guaranteed_refund
            refund = remaining_price - (remaining_price * percent_diff / 100)

            final_refund = refund + guaranteed_refund

            await inter.response.send_message(f"Авто-подсчет возврата: {int(final_refund)} рублей", ephemeral=True)
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

def setupcommands(bot):
    bot.add_cog(Settings(bot))