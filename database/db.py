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
            create_table = """CREATE TABLE info  
            ( 
              userid       INTEGER PRIMARY KEY, 
              login        TEXT, 
              password     TEXT 
            )"""
            cursor = sqlite_connection.cursor()
            cursor.execute(create_table)
            logging.debug("Database created successfully")

    async def get_login_and_password(self, userid):
        if userid not in self._states:
            self._states[userid] = {}
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

    async def insert_login_and_password(self, userid, login, password):
        if userid not in self._states:
            self._states[userid] = {}
        self._states[userid]["login"] = login
        self._states[userid]["password"] = password
        select_query = """
            INSERT INTO info (userid, login, password) VALUES (?,?,?);
        """
        async with aiosqlite.connect(self._dbname) as db:
            await db.execute(select_query, (userid, login, password))
            await db.commit()
