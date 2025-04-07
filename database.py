import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.settings = None
        self.staff_list = None
        self.created_tickets = None
        self.date_stats = None
        self.fast_commands = None
        self.banned_users = None

    def create_settings_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                user_id INTEGER,
                embed_color TEXT,
                dev_channel_id INTEGER,
                staff_settings_channel_id INTEGER,
                category_id INTEGER,
                ticket_channel_id INTEGER,
                counter_tickets INTEGER DEFAULT 0,
                primetime TEXT,
                status INTEGER DEFAULT 1,
                logging INTEGER DEFAULT 1
            )
        """)
        self.conn.commit()

    def create_price_list_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_list (
                id INTEGER PRIMARY KEY,
                vip_medium_price INTEGER,
                vip_platinum_price INTEGER,
                vip_crystal_price INTEGER,
                vip_crystalplus_price INTEGER,
                admin_1lvl_price INTEGER,
                admin_2lvl_price INTEGER,
                sponsor_price INTEGER
            )
        """)
        self.conn.commit()

    def create_staff_list_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_list (
                id INTEGER PRIMARY KEY,
                username TEXT,
                ticket_name TEXT,
                user_id INTEGER,
                role TEXT,
                closed_tickets INTEGER,
                mention INTEGER
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

    def create_fast_commands_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fast_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_name TEXT NOT NULL,
                description TEXT NOT NULL,
                response TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def create_banned_users_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                ban_time TEXT,
                ban_until TEXT
            )
        """)
        self.conn.commit()

    def get_settings(self, user_id=None, guild_id=None):
        if user_id is not None:
            self.cursor.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
        elif guild_id is not None:
            self.cursor.execute("SELECT * FROM settings WHERE guild_id = ?", (guild_id,))
        else:
            raise ValueError("Необходимо указать user_id или guild_id")
        return self.cursor.fetchone()

    def get_staff_list(self):
        if self.staff_list is None:
            self.cursor.execute("SELECT * FROM staff_list")
            self.staff_list = self.cursor.fetchall()
        return self.staff_list

    def get_created_tickets(self):
        if self.created_tickets is None:
            self.cursor.execute("SELECT * FROM created_tickets")
            self.created_tickets = self.cursor.fetchall()
        return self.created_tickets

    def get_date_stats(self):
        if self.date_stats is None:
            self.cursor.execute("SELECT * FROM date_stats")
            self.date_stats = self.cursor.fetchall()
        return self.date_stats

    def get_fast_commands(self):
        if self.fast_commands is None:
            self.cursor.execute("SELECT * FROM fast_commands")
            self.fast_commands = self.cursor.fetchall()
        return self.fast_commands

    def get_banned_users(self):
        if self.banned_users is None:
            self.cursor.execute("SELECT * FROM banned_users")
            self.banned_users = self.cursor.fetchall()
        return self.banned_users

    def update_settings(self, user_id=None, guild_id=None, **kwargs):
        if user_id is not None:
            self.cursor.execute("UPDATE settings SET {} WHERE user_id = ?".format(", ".join("{} = ?".format(key) for key in kwargs)), (*kwargs.values(), user_id))
        elif guild_id is not None:
            self.cursor.execute("UPDATE settings SET {} WHERE guild_id = ?".format(", ".join("{} = ?".format(key) for key in kwargs)), (*kwargs.values(), guild_id))
        else:
            raise ValueError("Необходимо указать user_id или guild_id")
        self.conn.commit()

    def update_staff_list(self, username, closed_tickets):
        self.cursor.execute("UPDATE staff_list SET closed_tickets = ? WHERE username = ?", (closed_tickets, username))
        self.conn.commit()
        self.staff_list = None

    def update_created_tickets(self, thread_id, taken_username):
        self.cursor.execute("UPDATE created_tickets SET taken_username = ? WHERE thread_id = ?", (taken_username, thread_id))
        self.conn.commit()
        self.created_tickets = None

    def update_date_stats(self, username, date, closed_tickets):
        self.cursor.execute("UPDATE date_stats SET closed_tickets = ? WHERE username = ? AND date = ?", (closed_tickets, username, date))
        self.conn.commit()
        self.date_stats = None

    def insert_fast_commands(self, command_name, description, response):
        self.cursor.execute("INSERT INTO fast_commands (command_name, description, response) VALUES (?, ?, ?)", (command_name, description, response))
        self.conn.commit()
        self.fast_commands = None

    def insert_banned_users(self, user_id, ban_time, ban_until):
        self.cursor.execute("INSERT INTO banned_users (user_id, ban_time, ban_until) VALUES (?, ?, ?)", (user_id, ban_time, ban_until))
        self.conn.commit()
        self.banned_users = None

    def delete_banned_users(self, user_id):
        self.cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        self.conn.commit()
        self.banned_users = None

    def close(self):
        self.conn.close()