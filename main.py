import json
from dotenv import load_dotenv, find_dotenv
import logging
from os import getenv
from database import DataBase
from bot import Bot
from bot import types
from languages import get_text
from parser_edu_tatar import EduTatarParser

load_dotenv(find_dotenv())
db = DataBase(getenv("DB_PATH", "db.db"))
bot = Bot(getenv("BOT_TOKEN", ""), 100)
parser = EduTatarParser()
logging.basicConfig(level=logging.DEBUG)

change = {
    "ru": "tr",
    "tr": "ru"
}


async def set_language_from_callback(update: types.CallbackQuery):
    language = ""
    if update.data == "set_russian":
        language = "ru"
        await bot.answer_callback_query(update.id)
        await db.set_language(update.from_user["id"], "ru")
        await bot.edit_message_text(chat_id=update.message.chat.id, message_id=update.message.message_id,
                                    text=get_text("ru", "language_applied"))
    elif update.data == "set_tatar":
        language = "tr"
        await bot.answer_callback_query(update.id)
        await db.set_language(update.from_user["id"], "tr")
        await bot.edit_message_text(chat_id=update.message.chat.id, message_id=update.message.message_id,
                                    text=get_text("tr", "language_applied"))
    await bot.send_message(chat_id=update.from_user["id"],
                           text=get_text(language, "enter_login"))
    db.set_value(update.from_user["id"], "state", "login")


async def main_menu_message(update: types.Message):
    user_id = update.from_user["id"]
    language = await db.get_language(user_id)
    await bot.send_message(user_id,
                           get_text(language, "choose_option"),
                           reply_markup={
                               "inline_keyboard": [
                                   [
                                       {
                                           "text": get_text(language, "daily_grades"),
                                           "callback_data": "daily_grades"
                                       },
                                       {
                                           "text": get_text(language, "quarter_grades"),
                                           "callback_data": "quarter_grades"
                                       }
                                   ],
                                   [
                                       {
                                           "text": get_text(language, "settings"),
                                           "callback_data": "settings"
                                       }
                                   ]
                               ]
                           })


async def settings_menu(update: types.CallbackQuery):
    language = await db.get_language(update.from_user["id"])
    await bot.edit_message_text(
        chat_id=update.from_user["id"],
        message_id=update.message.message_id,
        text=get_text(language, "here_you_can_change_settings"),
        reply_markup={
            "inline_keyboard": [
                [
                    {
                        "text": "%s: %s" % (
                            get_text(language, "language"), get_text(language, language)
                        ),
                        "callback_data": "set_%s" % change[language]
                    }
                ],
                [
                    {
                        "text": get_text(language, "back"),
                        "callback_data": "back"
                    }
                ]
            ]
        }

    )


async def send_message_choose_language(update: types.Message):
    message = await bot.send_message(update.chat.id, "Привет, выбери свой язык:",
                                     reply_markup={
                                         "inline_keyboard": [[
                                             {
                                                 "text": "Русский",
                                                 "callback_data": "set_russian"
                                             },
                                             {
                                                 "text": "Татарча",
                                                 "callback_data": "set_tatar"
                                             }
                                         ]]
                                     })
    db.set_value(update.from_user["id"], "message_language", message.message_id)


async def check_login_and_password(user_id: int):
    login = db.get_value(user_id, "login")
    password = db.get_value(user_id, "password")
    DNSID = await parser.get_DNSID(
        login=login,
        password=password
    )
    if DNSID is None:
        return False
    else:
        db.set_value(user_id, "DNSID", DNSID)
        return True


@bot.register(types.Handlers.onCallbackQuery)
async def onCallbackQuery(update: types.CallbackQuery):
    user_id = update.from_user["id"]
    language = await db.get_language(user_id)
    if update.data in ("set_russian", "set_tatar"):
        await set_language_from_callback(update)
    elif update.data == "daily_grades":
        login_and_password = await db.get_login_and_password(user_id)
        if login_and_password is None:
            await bot.send_message(chat_id=update.from_user["id"],
                                   text="Something went wrong. We apologise.")  # TODO: do not do like that hehe
            return
        result, DNSID, dates1, dates2 = await parser.getDay(login_and_password[0], login_and_password[1],
                                                            db.get_value(user_id, "DNSID"))
        if DNSID is not None:
            db.set_value(user_id, "DNSID", DNSID)
        await bot.edit_message_text(chat_id=user_id, message_id=update.message.message_id, text=result, reply_markup={
            "inline_keyboard": [[
                {
                    "text": "<--",
                    "callback_data": dates1
                },
                {
                    "text": "-->",
                    "callback_data": dates2
                }],
                [{
                    "text": get_text(language, "copy"),
                    "callback_data": "copy"
                },
                {
                    "text": get_text(language, "back"),
                    "callback_data": "back"
                }],
            ]
        })
    elif update.data == "quarter_grades":
        login_and_password = await db.get_login_and_password(user_id)
        if login_and_password is None:
            await bot.send_message(chat_id=update.from_user["id"],
                                   text="Something went wrong. We apologise.")  # TODO: i shouldn't do that, but i don't know the case when it can be
            return
        result, DNSID = await parser.getTerm(login_and_password[0], login_and_password[1],
                                             termNum=1, DNSID=db.get_value(user_id, "DNSID"))
        if DNSID is not None:
            db.set_value(user_id, "DNSID", DNSID)
        await bot.edit_message_text(chat_id=user_id, message_id=update.message.message_id, text=result, reply_markup={
            "inline_keyboard": [[
                {
                    "text": get_text(language, "first_quarter"),
                    "callback_data": "1"
                }],
                [{
                    "text": get_text(language, "second_quarter"),
                    "callback_data": "2"
                }],
                [{
                    "text": get_text(language, "third_quarter"),
                    "callback_data": "3"
                }],
                [{
                    "text": get_text(language, "fourth_quarter"),
                    "callback_data": "4"
                }],
                [{
                    "text": get_text(language, "year"),
                    "callback_data": "year"
                }],
                [{
                    "text": get_text(language, "copy"),
                    "callback_data": "copy"
                },
                {
                    "text": get_text(language, "back"),
                    "callback_data": "back"
                }],
            ]
        })
    elif update.data in ('1', '2', '3', '4'):
        login_and_password = await db.get_login_and_password(user_id)
        if login_and_password is None:
            await bot.send_message(chat_id=update.from_user["id"],
                                   text="Something went wrong. We apologise.")  # TODO: do not do like that hehe
            return
        result, DNSID = await parser.getTerm(login_and_password[0], login_and_password[1],
                                             termNum=update.data, DNSID=db.get_value(user_id, "DNSID"))
        if DNSID is not None:
            db.set_value(user_id, "DNSID", DNSID)
        await bot.edit_message_text(chat_id=user_id, message_id=update.message.message_id, text=result,
                                    reply_markup={
                                        "inline_keyboard": [[
                                            {
                                                "text": get_text(language, "first_quarter"),
                                                "callback_data": "1" if update.data != "1" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "second_quarter"),
                                                "callback_data": "2" if update.data != "2" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "third_quarter"),
                                                "callback_data": "3" if update.data != "3" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "fourth_quarter"),
                                                "callback_data": "4" if update.data != "4" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "year"),
                                                "callback_data": "year" if update.data != "year" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "copy"),
                                                "callback_data": "copy"
                                            },
                                            {
                                                "text": get_text(language, "back"),
                                                "callback_data": "back"
                                            }],
                                        ]
                                    })
    elif update.data == "year":
        login_and_password = await db.get_login_and_password(user_id)
        if login_and_password is None:
            await bot.send_message(chat_id=update.from_user["id"],
                                   text="Something went wrong. We apologise.")  # TODO: upper to-do
            return
        result, DNSID = await parser.getYear(login_and_password[0], login_and_password[1],
                                             DNSID=db.get_value(user_id, "DNSID"))
        if DNSID is not None:
            db.set_value(user_id, "DNSID", DNSID)
        await bot.edit_message_text(chat_id=user_id, message_id=update.message.message_id, text=result,
                                    reply_markup={
                                        "inline_keyboard": [[
                                            {
                                                "text": get_text(language, "first_quarter"),
                                                "callback_data": "1" if update.data != "1" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "second_quarter"),
                                                "callback_data": "2" if update.data != "2" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "third_quarter"),
                                                "callback_data": "3" if update.data != "3" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "fourth_quarter"),
                                                "callback_data": "4" if update.data != "4" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "year"),
                                                "callback_data": "year" if update.data != "year" else "pass"
                                            }],
                                            [{
                                                "text": get_text(language, "copy"),
                                                "callback_data": "copy"
                                            },
                                            {
                                                "text": get_text(language, "back"),
                                                "callback_data": "back"
                                            }],
                                        ]
                                    })
    elif update.data == "settings":
        await settings_menu(update)
    elif update.data in ("set_ru", "set_tr"):
        if update.data == "set_ru":
            await db.set_language(user_id, "ru")
        elif update.data == "set_tr":
            await db.set_language(user_id, "tr")
        language = await db.get_language(user_id)
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=get_text(language, "here_you_can_change_settings"),
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": "%s: %s" % (
                                get_text(language, "language"), get_text(language, language)
                            ),
                            "callback_data": "set_%s" % change[language]
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "back"),
                            "callback_data": "back"
                        }
                    ]
                ]
            }
        )
    elif update.data == "copy":
        await bot.send_message(user_id, update.message.text)
    elif update.data == "back":
        user_id = update.from_user["id"]
        language = await db.get_language(user_id)
        await bot.edit_message_text(chat_id=user_id, message_id=update.message.message_id,
                                    text=get_text(language, "choose_option"),
                                    reply_markup={
                                        "inline_keyboard": [[
                                            {
                                                "text": get_text(language, "daily_grades"),
                                                "callback_data": "daily_grades"
                                            },
                                            {
                                                "text": get_text(language, "quarter_grades"),
                                                "callback_data": "quarter_grades"
                                            }
                                        ]]
                                    })
    elif update.data.isnumeric():
        login_and_password = await db.get_login_and_password(user_id)
        if login_and_password is None:
            await bot.send_message(chat_id=update.from_user["id"],
                                   text="Something went wrong. We apologise.")  # TODO: do not do like that hehe
            return
        original_DNSID = db.get_value(user_id, "DNSID")
        if original_DNSID is None:
            await bot.answer_callback_query(update.id, "Подождите...")
        result, DNSID, dates1, dates2 = await parser.getDay(login_and_password[0], login_and_password[1],
                                                            original_DNSID, date=int(update.data), language=language)
        if DNSID is not None:
            db.set_value(user_id, "DNSID", DNSID)
        await bot.edit_message_text(message_id=update.message.message_id, chat_id=update.message.chat.id, text=result,
                                    reply_markup={
                                        "inline_keyboard": [[
                                            {
                                                "text": "<--",
                                                "callback_data": dates1
                                            },
                                            {
                                                "text": "-->",
                                                "callback_data": dates2
                                            }],
                                            [{
                                                "text": get_text(language, "copy"),
                                                "callback_data": "copy"
                                            },
                                            {
                                                "text": get_text(language, "back"),
                                                "callback_data": "back"
                                            }],
                                        ]
                                    }, parse_mode="HTML")
    elif update.data == "pass":
        await bot.answer_callback_query(update.id)


@bot.register(types.Handlers.onMessageOnly)
async def onMessageOnly(update: types.Message):
    user_id = update.from_user["id"]
    if user_id != update.chat.id:
        return
    state = db.get_value(user_id, "state")
    language = await db.get_language(user_id)
    login_and_password = await db.get_login_and_password(user_id)
    if state is None:
        if login_and_password is not None:
            db.set_value(user_id, "state", "main")
            await main_menu_message(update)
            return
        db.set_value(user_id, "state", "language")
        await send_message_choose_language(update)
    elif state == "language":
        if isinstance(db.get_value(user_id, "message_language"), int):
            await bot.make_request(
                "deleteMessage",
                {
                    "chat_id": user_id,
                    "message_id": db.get_value(user_id, "message_language")
                }
            )
            await send_message_choose_language(update)
    elif state == "login":
        db.set_value(user_id, "login", update.text)
        db.set_value(user_id, "state", "password")
        await bot.send_message(chat_id=user_id, text=get_text(language, "enter_password"), reply_markup={
                "remove_keyboard": True
        })
    elif state == "password":
        db.set_value(user_id, "password", update.text)
        await bot.send_message(chat_id=user_id, text=get_text(language, "let_me_check_login_and_password"))
        result_checking = await check_login_and_password(user_id)
        if not result_checking:
            await bot.send_message(chat_id=user_id, text=get_text(language, "incorrect_login_and_password"))
            db.set_value(user_id, "state", "login")
        else:
            await db.set_login_and_password(user_id, db.get_value(user_id, "login"), db.get_value(user_id, "password"))
            db.set_value(user_id, "state", "main")
            await bot.send_message(user_id, get_text(language, "thanks"), reply_markup={
                    'keyboard': [["Показать меню"]],
                    'one_time_keyboard': False,
                    'resize_keyboard': True
            })
            await main_menu_message(update)
    elif state == "main":
        await main_menu_message(update)


bot.activate()
