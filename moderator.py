import re, disnake
from database import Database

class Moderator:
    def __init__(self):
        self.db = Database("database.db")
        self.keywords = [
            "free cheat",
            "join server",
            "discord invite",
            "free gift",
            "steam gift",
            "steam free",
            "free discord nitro",
            "free steam",
            "discord link",
            "server invite",
            "join now"
        ]
        self.allowed_domains = [
            "discord.gg",
            "yooma.su"
        ]
        self.patterns = [re.compile(keyword, re.IGNORECASE) for keyword in self.keywords]

    def check_message(self, message):
        if isinstance(message.channel, disnake.VoiceChannel) or message.channel.nsfw:
            self.db.cursor.execute("SELECT * FROM staff_list WHERE user_id = ?", (message.author.id,))
            staff_member = self.db.cursor.fetchone()
            if staff_member is not None:
                return False

            for pattern in self.patterns:
                if pattern.search(message.content):
                    for domain in self.allowed_domains:
                        if domain in message.content:
                            return False
                    return True
            return False