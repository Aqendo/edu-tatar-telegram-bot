import logging
from os import getenv

from dotenv import find_dotenv, load_dotenv

from bot import Bot
from edutatar import EduTatarModule

logging.basicConfig(level=logging.ERROR)
load_dotenv(find_dotenv())
bot = Bot(getenv("BOT_TOKEN", ""), 100)
bot.load_module(EduTatarModule(bot))
bot.activate()
