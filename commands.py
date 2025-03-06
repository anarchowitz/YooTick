import disnake, datetime
from disnake.ext import commands
from database import Database

watermark = "Author : @anarchowitz"

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")
        self.page = 1
        self.stats_message = None
        self.embed_color = None
    
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

    @commands.slash_command(description="[STAFF] - Просмотр цен")
    async def price(self, inter):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        self.db.cursor.execute("SELECT embed_color FROM settings WHERE guild_id = ?", (inter.guild.id,))
        settings = self.db.cursor.fetchone()
        if settings is not None:
            self.embed_color = disnake.Color(int(settings[0].lstrip('#'), 16))

        view = disnake.ui.View()
        select_menu = disnake.ui.Select(
            placeholder="Выберите пункт",
            custom_id="price_select",
            options=[
                disnake.SelectOption(label="Докупка", value="докупка"),
                disnake.SelectOption(label="Дополнительные услуги", value="дополнительные услуги")
            ]
        )
        select_menu.callback = self.price_callback
        view.add_item(select_menu)
        await inter.response.send_message("", view=view)

    async def price_callback(self, inter):
        if not (self.check_staff_permissions(inter, "staff") or self.check_staff_permissions(inter, "dev")):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        if inter.data.values[0] == "докупка":
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите привилегию",
                custom_id="privilege_select",
                options=[
                    disnake.SelectOption(label="Medium VIP", value="medium_vip"),
                    disnake.SelectOption(label="Platinum VIP", value="platinum_vip"),
                    disnake.SelectOption(label="Crystal VIP", value="crystal_vip"),
                    disnake.SelectOption(label="Crystal+ VIP", value="crystal_plus_vip"),
                    disnake.SelectOption(label="Назад", value="назад")
                ]
            )
            select_menu.callback = self.privilege_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="", view=view)
        elif inter.data.values[0] == "дополнительные услуги":
            embed = disnake.Embed(title="Дополнительные услуги", color=self.embed_color)
            embed.add_field(name="Перенос админ/вип привилегии", value="150р", inline=False)
            embed.add_field(name="Размут на сайте", value="200р", inline=False)
            embed.add_field(name="Разморозка прав для админов", value="350р", inline=False)
            embed.add_field(name="Разморозка прав для спонсора", value="750р", inline=False)

            await inter.response.edit_message(embed=embed)

    async def privilege_callback(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        if inter.data.values[0] == "назад":
            view = disnake.ui.View()
            select_menu = disnake.ui.Select(
                placeholder="Выберите пункт",
                custom_id="price_select",
                options=[
                    disnake.SelectOption(label="Докупка", value="докупка"),
                    disnake.SelectOption(label="Дополнительные услуги", value="дополнительные услуги")
                ]
            )
            select_menu.callback = self.price_callback
            view.add_item(select_menu)
            await inter.response.edit_message(content="Выберите пункт", view=view)
        else:
            self.db.cursor.execute("SELECT vip_medium_price, vip_platinum_price, vip_crystal_price, vip_crystalplus_price FROM price_list")
            prices = self.db.cursor.fetchone()

            if prices is None:
                await inter.response.edit_message(content="Цены не найдены")
                return

            embed = disnake.Embed(title="Докупка", color=self.embed_color)

            if inter.data.values[0] == "medium_vip":
                embed.add_field(name="С Medium VIP на Platinum VIP", value=f"{prices[1] - prices[0]}р", inline=False)
                embed.add_field(name="С Medium VIP на Crystal VIP", value=f"{prices[2] - prices[0]}р", inline=False)
                embed.add_field(name="С Medium VIP на Crystal+ VIP", value=f"{prices[3] - prices[0]}р", inline=False)
            elif inter.data.values[0] == "platinum_vip":
                embed.add_field(name="С Platinum VIP на Crystal VIP", value=f"{prices[2] - prices[1]}р", inline=False)
                embed.add_field(name="С Platinum VIP на Crystal+ VIP", value=f"{prices[3] - prices[1]}р", inline=False)
            elif inter.data.values[0] == "crystal_vip":
                embed.add_field(name="С Crystal VIP на Crystal+ VIP", value=f"{prices[3] - prices[2]}р", inline=False)
            elif inter.data.values[0] == "crystal_plus_vip":
                await inter.response.edit_message(content="Вы уже имеете максимальную привилегию")
                return

            await inter.response.edit_message(embed=embed)

    @commands.slash_command(description="[DEV] - Просмотр статистики по датам")
    async def date_stats(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        self.db.cursor.execute("SELECT embed_color FROM settings WHERE guild_id = ?", (inter.guild.id,))
        settings = self.db.cursor.fetchone()
        if settings is not None:
            self.embed_color = disnake.Color(int(settings[0].lstrip('#'), 16))

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

    async def date_stats_callback(self, inter):
        date_str = inter.data.values[0]
        date_str = date_str.replace('-', '.')
        date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

        self.db.cursor.execute(""" 
            SELECT username, SUM(closed_tickets) FROM date_stats
            WHERE date = ?
            GROUP BY username
        """, (date.strftime("%d.%m.%Y"),))
        stats = self.db.cursor.fetchall()

        embed = disnake.Embed(title=f"Статистика по датам ({date_str})", color=self.embed_color)
        for username, closed_tickets in stats:
            embed.add_field(name=username, value=str(closed_tickets), inline=False)

        await inter.response.send_message(embed=embed)

    @commands.slash_command(description="[DEV] - Статистика сотрудников")
    async def stats(self, inter):
        if not self.check_staff_permissions(inter, "dev"):
            await inter.response.send_message("У вас нет прав для использования этой команды", ephemeral=True)
            return
        self.db.cursor.execute("SELECT embed_color FROM settings WHERE guild_id = ?", (inter.guild.id,))
        settings = self.db.cursor.fetchone()
        if settings is not None:
            self.embed_color = disnake.Color(int(settings[0].lstrip('#'), 16))

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

        for i, staff_member in enumerate(staff_members[start:end]):
            username = staff_member[1]
            shortname = staff_member[2]
            role = staff_member[4]
            closed_tickets = staff_member[5]

            embed.add_field(
                name=f"{i+1}. {username}",
                value=f"🪪 Роль: {role}\n🎫 Имя в тикетах: {shortname}\n🎫 Закрытых тикетов: **Секрет**",
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

                for i, staff_member in enumerate(staff_members[start:end]):
                    username = staff_member[1]
                    shortname = staff_member[2]
                    role = staff_member[4]
                    closed_tickets = staff_member[5]

                    embed.add_field(
                        name=f"{i+1}. {username}",
                        value=f"🪪 Роль: {role}\n🎫 Имя в тикетах: {shortname}\n🎫 Закрытых тикетов: **Секрет**",
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

            for i, staff_member in enumerate(staff_members[start:end]):
                username = staff_member[1]
                shortname = staff_member[2]
                role = staff_member[4]
                closed_tickets = staff_member[5]

                embed.add_field(
                    name=f"{i+1}. {username}",
                    value=f"🪪 Роль: {role}\n🎫 Имя в тикетах: {shortname}\n🎫 Закрытых тикетов: **Секрет**",
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

            for i, staff_member in enumerate(staff_members[start:end]):
                username = staff_member[1]
                shortname = staff_member[2]
                role = staff_member[4]
                closed_tickets = staff_member[5]

                embed.add_field(
                    name=f"{i+1}. {username}",
                    value=f"🪪 Роль: {role}\n🎫 Имя в тикетах: {shortname}\n🎫 Закрытых тикетов: {closed_tickets}",
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
                    UPDATE settings SET embed_color = ?, category_id = ?, ticket_channel_id = ?, primetime = ?
                    WHERE guild_id = ?
                """, (color, category_id, channel_id, primetime, inter.guild.id))
            else:
                self.db.cursor.execute(""" 
                    INSERT INTO settings (guild_id, embed_color, category_id, ticket_channel_id, primetime = ?)
                    VALUES (?, ?, ?, ?)
                """, (inter.guild.id, color, category_id, channel_id, primetime))

            self.db.conn.commit()

            await inter.response.send_message(
                embed=disnake.Embed(title="Настройки сохранены", description=f"Цвет боковой полоски: {color}\n"
                f"Айди категории тикетов: {category_id}\n"
                f"Айди канала тикетов: {channel_id}\n"
                f"Рабочее время: {primetime}", color=self.embed_color),
                ephemeral=True
            )

def setupcommands(bot):
    bot.add_cog(Settings(bot))