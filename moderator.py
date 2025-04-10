import re
import disnake
from database import Database

class Moderator:
    def __init__(self):
        self.db = Database("database.db")
        self.keywords = [
            r"cybershoke\.net", # ad
            r"cs2red\.ru", # ad
            r"onetake-cs2\.ru", # ad
            r"discord\.com\/invite\/", # spam
            r"discord\.com\/invites\/", # spam
            r"discord\.io\/", # spam
            r"discord\.me\/", # spam
            r"youtude\.net\/", # scam
            r"onlyfans", # spam
            r"free", # spam
            r"gift", # spam
            r"giveaway", # spam
            r"join", # spam
            r"server", # spam
            r"invite", # spam
            r"link", # spam
            r"nsfw", # spam
            r"porn", # spam
            r"leaks", # spam
            r"qr code", # spam
            r"exclusive", # spam
            r"personal", # spam
            r"wet", # spam
            r"fire", # spam
            r"com server" # spam
        ]
        self.whitelist = [
            r"tenor\.com"
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
                    for whitelist_pattern in self.whitelist:
                        if re.compile(whitelist_pattern, re.IGNORECASE).search(message.content):
                            return False
                    return True

            return False