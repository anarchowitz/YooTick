import disnake
from disnake.ext import commands

class LikeButtons(disnake.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @disnake.ui.button(label="", custom_id="like", emoji="👍", style=disnake.ButtonStyle.green)
    async def like_button(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.like_callback(inter)

    @disnake.ui.button(label="", custom_id="dislike", emoji="👎", style=disnake.ButtonStyle.red)
    async def dislike_button(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await self.dislike_callback(inter)

    async def like_callback(self, inter: disnake.Interaction):
        # Код для лайка
        await inter.response.send_message("Лайк!", ephemeral=True)

    async def dislike_callback(self, inter: disnake.Interaction):
        # Код для дизлайка
        await inter.response.send_message("Дизлайк!", ephemeral=True)