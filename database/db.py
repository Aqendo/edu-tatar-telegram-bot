import sqlite3
import aiosqlite
import os
import logging


class DataBase:
    _states = {}

    def __init__(self, dbname: str = "sqldb.db"):
        self._dbname = dbname
        if not os.path.isfile(self._dbname):
            sqlite_connection = sqlite3.connect(self._dbname)
            create_table_info = """CREATE TABLE info  
            ( 
              userid       INTEGER PRIMARY KEY, 
              login        TEXT, 
              password     TEXT 
            );"""

            create_table_settings = """CREATE TABLE settings  
            ( 
              userid       INTEGER PRIMARY KEY, 
              language        TEXT
            )"""
            cursor = sqlite_connection.cursor()
            cursor.execute(create_table_info)
            cursor.execute(create_table_settings)
            logging.debug("Database created successfully")

    # temporary storage get
    def get_value(self, userid, key):
        if userid in self._states:
            if key in self._states[userid]:
                return self._states[userid][key]
        return None

    # temporary storage set
    def set_value(self, userid, key, value):
        if userid in self._states:
            self._states[userid][key] = value
        else:
            self._states[userid] = {}
            self._states[userid][key] = value

    async def get_login_and_password(self, userid):
        if userid not in self._states:
            self._states[userid] = {}
        elif "password" not in self._states[userid]:
            pass
        else:
            return self._states[userid]["login"], self._states[userid]["password"]
        async with aiosqlite.connect(self._dbname) as db:
            select_query = """
                SELECT login, password from info where userid=?;
            """
            async with db.execute(select_query, (userid,)) as cursor:
                login_and_password = await cursor.fetchall()
                if len(login_and_password) == 0:
                    return None
                self._states[userid]["login"] = login_and_password[0][0]
                self._states[userid]["password"] = login_and_password[0][1]
                return login_and_password[0][0], login_and_password[0][1]

    async def get_language(self, userid):
        if userid not in self._states:
            self._states[userid] = {}
        elif "language" not in self._states[userid]:
            pass
        else:
            return self._states[userid]["language"]
        async with aiosqlite.connect(self._dbname) as db:
            select_query = """
                SELECT language from settings where userid=?;
            """
            async with db.execute(select_query, (userid,)) as cursor:
                language = await cursor.fetchall()
                if len(language) == 0:
                    return None
                self._states[userid]["language"] = language[0][0]
                return language[0][0]

    async def set_login_and_password(self, userid, login, password):
        if userid not in self._states:
            self._states[userid] = {}
        self._states[userid]["login"] = login
        self._states[userid]["password"] = password
        select_query = """
            INSERT OR REPLACE INTO info (userid, login, password) VALUES (?,?,?);
        """
        async with aiosqlite.connect(self._dbname) as db:
            await db.execute(select_query, (userid, login, password))
            await db.commit()

    async def set_language(self, userid, language):
        if userid not in self._states:
            self._states[userid] = {}
        self._states[userid]["language"] = language
        select_query = """
            INSERT OR REPLACE INTO settings (userid, language) VALUES (?,?);
        """
        async with aiosqlite.connect(self._dbname) as db:
            await db.execute(select_query, (userid, language))
            await db.commit()
