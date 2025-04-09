import re
import disnake
from database import Database

class Moderator:
    def __init__(self):
        self.db = Database("database.db")
        self.keywords = [
            r"cybershoke\.net",
            r"cs2red\.ru",
            r"onetake-cs2\.ru",
            r"discord\.com\/invite\/",
            r"discord\.com\/invites\/",
            r"discord\.io\/",
            r"discord\.me\/",
            r"onlyfans",
            r"free",
            r"gift",
            r"giveaway",
            r"join",
            r"server",
            r"invite",
            r"link",
            r"nsfw",
            r"porn",
            r"leaks",
            r"qr code",
            r"exclusive",
            r"personal",
            r"wet",
            r"fire",
            r"com server",
            r"cs2"
        ]
        self.patterns = [re.compile(keyword, re.IGNORECASE) for keyword in self.keywords]

    def check_message(self, message):
        if isinstance(message.channel, (disnake.TextChannel, disnake.VoiceChannel, disnake.Thread)):
            self.db.cursor.execute("SELECT * FROM staff_list WHERE user_id = ?", (message.author.id,))
            staff_member = self.db.cursor.fetchone()
            if staff_member is not None:
                return False

            for pattern in self.patterns:
                if pattern.search(message.content):
                    return True

            return False