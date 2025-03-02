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
                ticket_channel_id INTEGER,
                counter_tickets INTEGER DEFAULT 0,
                primetime TEXT
            )
        """)
        self.conn.commit()

    def create_staff_list_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_list (
                id INTEGER PRIMARY KEY,
                username TEXT,
                user_id INTEGER,
                role TEXT,
                closed_tickets INTEGER,
                likes INTEGER,
                dislikes INTEGER
            )
        """)
        self.conn.commit()

    def create_created_tickets_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS created_tickets (
                id INTEGER PRIMARY KEY,
                thread_id INTEGER,
                creator_id INTEGER,
                creator_username TEXT,
                taken_username TEXT,
                thread_number INTEGER
            )
        """)
        self.conn.commit()

    def create_date_stats_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS date_stats (
                id INTEGER PRIMARY KEY,
                username TEXT,
                date TEXT,
                closed_tickets INTEGER
            )
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()