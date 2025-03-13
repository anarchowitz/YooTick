import disnake, random
from disnake.ext import commands
from database import Database

class FastCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.startswith('a.marry <@1275300681535983646>'):
            a = random.randint(1,3)
            if a == 1:
                await message.reply("ты адекватная? а ни чо то факт то што я бот???")
            elif a == 2:
                await message.reply("Я занята так-то эмм...")
            elif a == 3:
                await message.reply("Наша любовь не взаимна... прости..")
        if message.content.startswith('.'):
            command = message.content.split()[0][1:].lower()
            
            self.db.cursor.execute("SELECT response FROM fast_commands WHERE command_name = ?", (command,))
            result = self.db.cursor.fetchone()
            
            if result:
                await message.delete()
                response = result[0].replace("{author}", message.author.name)
                await message.channel.send(response)

def setupfastcommands(bot):
    bot.add_cog(FastCommand(bot))