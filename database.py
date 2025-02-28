import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_settings_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                embed_color TEXT,
                category_id INTEGER,
                ticket_channel_id INTEGER
            )
        """)
        self.conn.commit()

    def create_staff_list_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_list (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                user_id INTEGER,
                role TEXT
            )
        """)
        self.conn.commit()

    def create_created_tickets_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS created_tickets (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                ticket_id INTEGER,
                user_id INTEGER,
                created_at TEXT
            )
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()