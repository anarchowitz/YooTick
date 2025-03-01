import disnake
from disnake.ext import commands
from database import Database

watermark = "Author : @anarchowitz"

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")

    @commands.slash_command(description="[DEV] - Добавить сотрудника", hidden=True)
    async def add_staff(self, inter):
        await inter.response.send_modal(AddStaffModal(self.bot, self.db))

    @commands.slash_command(description="[DEV] - Настроить бота", hidden=True)
    async def settings(self, inter):
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
            ],
        )

        await inter.response.send_modal(modal)

class AddStaffModal(disnake.ui.Modal):
    def __init__(self, bot, db):
        components = [
            disnake.ui.ActionRow(
                disnake.ui.TextInput(label="Юзернейм", placeholder="anarchowitz", custom_id="nickname", style=disnake.TextInputStyle.short)
            ),
            disnake.ui.ActionRow(
                disnake.ui.TextInput(label="Айди пользователя", placeholder="444574234564362250", custom_id="user_id", style=disnake.TextInputStyle.short)
            ),
            disnake.ui.ActionRow(
                disnake.ui.TextInput(label="Роль", placeholder="staff/dev", custom_id="role", style=disnake.TextInputStyle.short)
            ),
        ]
        super().__init__(title="Добавить сотрудника", custom_id="add_staff_modal", components=components)
        self.bot = bot
        self.db = db

    async def callback(self, inter: disnake.ModalInteraction):
        nickname = inter.text_values['nickname']
        user_id = int(inter.text_values['user_id'])
        role = inter.text_values['role']

        if role not in ["staff", "dev"]:
            await inter.response.send_message("Неправильная роль!")
            return

        self.db.cursor.execute("""
            SELECT * FROM staff_list WHERE nickname = ?
        """, (nickname,))
        existing_staff = self.db.cursor.fetchone()

        if existing_staff is not None:
            view = disnake.ui.View()
            view.add_item(disnake.ui.Button(label="Да", style=disnake.ButtonStyle.green, custom_id="yes"))
            view.add_item(disnake.ui.Button(label="Нет", style=disnake.ButtonStyle.red, custom_id="no"))
            message = await inter.response.send_message("Юзернейм уже используется! Перезаписать данные?", view=view, ephemeral=True)
            def check(inter):
                return inter.data.custom_id in ["yes", "no"]
            inter = await self.bot.wait_for("interaction", check=check, timeout=30)
            if inter.data.custom_id == "yes":
                self.db.cursor.execute("""
                    UPDATE staff_list SET user_id = ?, role = ?, closed_tickets = 0, likes = 0, dislikes = 0
                    WHERE nickname = ?
                """, (user_id, role, nickname))
                self.db.conn.commit()
                await inter.response.send_message(
                    f"Юзернейм: {nickname}\n"
                    f"Айди пользователя: {user_id}\n"
                    f"Роль: {role}\n"
                    f"\nДанные перезаписаны в базу данных!",
                    ephemeral=True
                )
            #дописать удаление текста с кнопкой (юзернейм уже исп..)
        else:
            self.db.cursor.execute("""
                INSERT INTO staff_list (nickname, user_id, role, closed_tickets, likes, dislikes)
                VALUES (?, ?, ?, 0, 0, 0)
            """, (nickname, user_id, role))
            self.db.conn.commit()
            await inter.response.send_message(
                f"Юзернейм: {nickname}\n"
                f"Айди пользователя: {user_id}\n"
                f"Роль: {role}\n"
                f"\nДанные сохранены в базу данных!",
                ephemeral=True
            )

class SettingsModal(disnake.ui.Modal):
    def __init__(self):
        super().__init__(title="Настройки", custom_id="settings_modal")
        self.add_item(disnake.ui.TextInput(label="Цвет боковой полоски (В HEX)", placeholder="#7789fd", custom_id="color", style=disnake.TextInputStyle.short))
        self.add_item(disnake.ui.TextInput(label="Айди категории тикетов", placeholder="1234567890", custom_id="category_id", style=disnake.TextInputStyle.short))
        self.add_item(disnake.ui.TextInput(label="Айди канала тикетов", placeholder="1234567890", custom_id="channel_id", style=disnake.TextInputStyle.short))

    async def callback(self, inter: disnake.ModalInteraction):
        color = inter.text_values['color']
        category_id = int(inter.text_values['category_id'])
        channel_id = int(inter.text_values['channel_id'])

        category = inter.guild.get_channel(category_id)
        channel = inter.guild.get_channel(channel_id)

        if category is None:
            await inter.response.send_message("Категория с таким ID введённом не найдена на сервере!")
            return

        if channel is None:
            await inter.response.send_message("Канал с таким ID введённом не найден на сервере!")
            return

        inter.bot.db.cursor.execute("""
            SELECT * FROM settings WHERE guild_id = ?
        """, (inter.guild.id,))
        existing_settings = inter.bot.db.cursor.fetchone()

        if existing_settings is not None:
            inter.bot.db.cursor.execute("""
                UPDATE settings SET embed_color = ?, category_id = ?, ticket_channel_id = ?
                WHERE guild_id = ?
            """, (color, category_id, channel_id, inter.guild.id))
        else:
            inter.bot.db.cursor.execute("""
                INSERT INTO settings (guild_id, embed_color, category_id, ticket_channel_id)
                VALUES (?, ?, ?, ?)
            """, (inter.guild.id, color, category_id, channel_id))

        inter.bot.db.conn.commit()

        await inter.response.send_message(
            f"Цвет боковой полоски: {color}\n"
            f"Айди категории тикетов: {category_id}\n"
            f"Айди канала тикетов: {channel_id}\n"
            f"\nДанные сохранены в базу данных!",
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(Settings(bot))