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
            answers = [
                "Это так сложно... прости я вынуждена отказаться 😔",
                "Я занята так-то эмм... 😒",
                "Наша любовь не взаимна... прости.. 💔",
                "Я не готова к такому большому шагу... 😟",
                "Мне нужно время подумать... 🤔",
                "Я не уверена, что мы готовы к браку...  😕",
                "Ты слишком милый, но я не готова к браку 😊",
                "Я люблю тебя, но не в этом смысле :worried: 😳",
                "Мы можем быть друзьями, но не мужем и женой 👫",
                "Я не готова к такой ответственности 😬",
                "Мне нужно время подумать о нашей будущем 🤝",
                "Я не уверена, что мы совместимы 🤔"
            ]
            await message.reply(random.choice(answers))
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
