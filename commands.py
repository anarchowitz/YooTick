import disnake
from disnake.ext import commands
from database import Database

watermark = "Author : @anarchowitz"

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")

    @commands.slash_command(description="[DEV] - Настроить бота")
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

    @commands.Cog.listener()
    async def on_modal_submit(self, inter):
        if inter.data.custom_id == "settings_modal":
            color = inter.text_values['color']
            category_id = int(inter.text_values['category_id'])
            channel_id = int(inter.text_values['channel_id'])

            # Проверка существования category_id и channel_id на сервере
            category = inter.guild.get_channel(category_id)
            channel = inter.guild.get_channel(channel_id)

            if category is None:
                await inter.response.send_message("Категория с таким ID введённом не найдена на сервере!")
                return

            if channel is None:
                await inter.response.send_message("Канал с таким ID введённом не найден на сервере!")
                return

            # Проверка существования записи в базе данных
            self.db.cursor.execute("""
                SELECT * FROM settings WHERE guild_id = ?
            """, (inter.guild.id,))
            existing_settings = self.db.cursor.fetchone()

            if existing_settings is not None:
                # Обновление существующих данных
                self.db.cursor.execute("""
                    UPDATE settings SET embed_color = ?, category_id = ?, ticket_channel_id = ?
                    WHERE guild_id = ?
                """, (color, category_id, channel_id, inter.guild.id))
            else:
                # Создание новых данных
                self.db.cursor.execute("""
                    INSERT INTO settings (guild_id, embed_color, category_id, ticket_channel_id)
                    VALUES (?, ?, ?, ?)
                """, (inter.guild.id, color, category_id, channel_id))

            self.db.conn.commit()

            await inter.response.send_message(
                f"Цвет боковой полоски: {color}\n"
                f"Айди категории тикетов: {category_id}\n"
                f"Айди канала тикетов: {channel_id}\n"
                f"Данные сохранены в базу данных!"
            )
        

def setup(bot):
    bot.add_cog(Settings(bot))