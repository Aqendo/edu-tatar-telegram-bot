from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import asyncio
from sqlalchemy import Integer, insert
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import mapped_column
import sqlite3
import aiosqlite
import os
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
Based = declarative_base()
class Info(Based):
    __tablename__ = 'info'
    user_id = mapped_column(Integer(), primary_key=True)
    login = mapped_column(String())
    password = mapped_column(String())
    
class Settings(Based):
    __tablename__ = 'settings'
    user_id = mapped_column(Integer(), primary_key=True)
    language = mapped_column(String(), default="ru")
    rounding_rule = mapped_column(Integer(), default=50)
    quarter = mapped_column(Integer(), default=1)




# async_session.add(User(name="Yes"))
# await async_session.commit()
# print("COMMITED")
# result = await async_session.execute(select(User).filter_by(name="sdf"))
# result = result.fetchall()
# if result != []:
#     print(result[0][0].name)
# await async_session.close()

# if __name__ == "__main__":
#     asyncio.run(init_models())
#     asyncio.run(main())
class DataBase:
    _states = {}

    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Info.metadata.create_all)
            await conn.run_sync(Settings.metadata.create_all)

    def __init__(self, dbname: str = "sqldb.db"):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///" + dbname,
            echo=True,
        )
        self.async_session = AsyncSession(self.engine, expire_on_commit=False)

    def __del__(self):
        asyncio.shield(self.async_session.close())
        asyncio.shield(self.engine.dispose())

        #asyncio.get_event_loop().run_until_complete(asyncio.shield(self.engine.close()))
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
        logging.debug("GETLOGIN")
        if userid not in self._states:
            self._states[userid] = {}
        elif "password" not in self._states[userid]:
            pass
        else:
            return self._states[userid]["login"], self._states[userid]["password"]
        result = await self.async_session.execute(select(Info).filter_by(user_id=userid))
        result = result.fetchone()
        if result is None:
            return None
        logging.debug(result)
        return result[0].login, result[0].password
    
    async def get_language(self, userid):
        logging.debug("GETLANGUAGE")
        if userid not in self._states:
            self._states[userid] = {}
        elif "language" not in self._states[userid]:
            pass
        else:
            return self._states[userid]["language"]
        result = await self.async_session.execute(select(Settings).filter_by(user_id=userid))
        settings_object = result.fetchone()
        if not settings_object:
            return None
        result.close()
        self._states[userid]["language"] = settings_object[0].language
        logging.debug(settings_object[0].language)
        return settings_object[0].language

    async def get_rounding_rule(self, userid):
        logging.debug("GETROUND")
        if userid not in self._states:
            self._states[userid] = {}
        elif "rounding_rule" not in self._states[userid]:
            pass
        else:
            return self._states[userid]["rounding_rule"]
        result = await self.async_session.execute(select(Settings).filter_by(user_id=userid))
        select_query = """
            SELECT rounding_rule from settings where userid=?;
        """
        rounding_rule = result.fetchone()
        if rounding_rule is None:
            return None
        self._states[userid]["rounding_rule"] = rounding_rule[0].rounding_rule
        result.close()
        return rounding_rule[0].rounding_rule
    
    async def get_quarter(self, userid):
        logging.debug("GETQUARTER")
        if userid not in self._states:
            self._states[userid] = {}
        elif "quarter" not in self._states[userid]:
            pass
        else:
            return self._states[userid]["quarter"]
        result = await self.async_session.execute(select(Settings).filter_by(user_id=userid))
        quarter = result.fetchone()
        if quarter is None:
            return None
        self._states[userid]["quarter"] = quarter[0].quarter
        result.close()
        return quarter[0].quarter

    async def set_login_and_password(self, userid, login, password):
        if userid not in self._states:
            self._states[userid] = {}
        self._states[userid]["login"] = login
        self._states[userid]["password"] = password
        select_query = """
            INSERT OR REPLACE INTO info (userid, login, password) VALUES (?,?,?);
        """
        stmt = insert(Info).prefix_with("OR REPLACE").values(user_id=userid, login=login, password=password)
        await self.async_session.execute(stmt)
        await self.async_session.commit()

    async def delete_login_and_password(self, userid):
        if userid in self._states:
            if "login" in self._states[userid]:
                del self._states[userid]["login"]
            if "password" in self._states[userid]:
                del self._states[userid]["password"]
            if "DNSID" in self._states[userid]:
                del self._states[userid]["DNSID"]
        delete_query = """
            DELETE from info where userid=?;
        """
        result = await self.async_session.execute(select(Info).filter_by(user_id=userid))
        result = result.fetchone()
        if len(result) == 0:
            raise RuntimeError("no login 'n pass in db")
        await self.async_session.delete(result[0])
        await self.async_session.commit()

    async def set_language(self, userid, language):
        logging.debug("LANGUAGE SET")
        if userid not in self._states:
            self._states[userid] = {}
        self._states[userid]["language"] = language
        select_query = """
            INSERT OR REPLACE INTO settings (userid, language, rounding_rule) VALUES (?,?, (SELECT rounding_rule FROM settings WHERE userid=?));
        """
        result = await self.async_session.execute(select(Settings).filter_by(user_id=userid))
        languageobject = result.fetchone()
        if languageobject is None:
            self.async_session.add(Settings(user_id=userid, language=language, rounding_rule=50))
            await self.async_session.commit()
        else:
            languageobject = languageobject[0]
            languageobject.language = language
            self.async_session.add(languageobject)
            await self.async_session.commit()
        self._states[userid]["language"] = language

    async def set_rounding_rule(self, userid, rounding_rule):
        if userid not in self._states:
            self._states[userid] = {}
        self._states[userid]["rounding_rule"] = rounding_rule
        select_query = """
            INSERT OR REPLACE INTO settings (userid, language, rounding_rule) VALUES (?,(SELECT language FROM settings WHERE userid=?),?);
        """
        result = await self.async_session.execute(select(Settings).filter_by(user_id=userid))
        rounding_rule_object = result.fetchone()
        if rounding_rule_object is None:
            self.async_session.add(Settings(user_id=userid, language=rounding_rule, rounding_rule=50))
            await self.async_session.commit()
        else:
            rounding_rule_object = rounding_rule_object[0]
            rounding_rule_object.rounding_rule = rounding_rule
            self.async_session.add(rounding_rule_object)
            await self.async_session.commit()

    async def set_quarter(self, userid, quarter):
        if userid not in self._states:
            self._states[userid] = {}
        self._states[userid]["quarter"] = quarter
        result = await self.async_session.execute(select(Settings).filter_by(user_id=userid))
        quarterobject = result.fetchone()
        if quarterobject is None:
            self.async_session.add(Settings(user_id=userid, quarter=quarter))
            await self.async_session.commit()
        else:
            quarterobject = quarterobject[0]
            quarterobject.quarter = quarter
            self.async_session.add(quarterobject)
            await self.async_session.commit()
        self._states[userid]["quarter"] = quarter

