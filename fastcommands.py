import disnake, random, logging
from datetime import datetime as dt
from disnake.ext import commands
from database import Database

logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

class FastCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("database.db")

    async def check_permissions(self, inter):
        db = Database("database.db")
        db.cursor.execute("SELECT * FROM staff_list WHERE username = ? AND user_id = ?", (inter.author.name, inter.author.id))
        staff_member = db.cursor.fetchone()
        
        if staff_member is not None and staff_member[4] in ["staff", "dev"]:
            return True

        allowed_roles = {"спонсор", "модератор серверов", "юмабой", "юмагерл"}

        if isinstance(inter.author, disnake.Member):
            role_names = [role.name.lower() for role in inter.author.roles]
            if any(role in allowed_roles for role in role_names):
                return True
                
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        if message.content.startswith('.'):
            if not await self.check_permissions(message):
                return
                
            command = message.content.split()[0][1:].lower()
            
            self.db.cursor.execute("SELECT response FROM fast_commands WHERE command_name = ?", (command,))
            result = self.db.cursor.fetchone()
            
            if result:
                await message.delete()
                response = result[0].replace("{author}", message.author.name)
                if message.reference and message.reference.message_id:
                    try:
                        replied_message = await message.channel.fetch_message(message.reference.message_id)
                        await replied_message.reply(response)
                    except disnake.NotFound:
                        await message.channel.send(response)
                else:
                    await message.channel.send(response)
                    
                logger.info(f"[FCOMMAND] Быстрая команда - '{command}' использована пользователем {message.author.name}")
            else:
                logger.info(f"[FCOMMAND] Неизвестная команда '{command}' использована пользователем {message.author.name}")

def setupfastcommands(bot):
    bot.add_cog(FastCommand(bot))