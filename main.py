from os import getenv
from bot import Bot
from edutatar import EduTatarModule
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
bot = Bot(getenv("BOT_TOKEN", ""), 100)
bot.load_module(EduTatarModule(bot))
bot.activate()
