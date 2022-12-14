import asyncio
import logging

from dotenv import find_dotenv, load_dotenv

from bot import Bot, bot_types
from bot.module_logic import BaseModule

from .database import DataBase
from .languages import get_text
from .parser_edu_tatar import EduTatarParser


class EduTatarModule(BaseModule):
    def __init__(self, bot: Bot, db_path: str):
        self.bot = bot
        load_dotenv(find_dotenv())
        self.db = DataBase(db_path)
        asyncio.shield(self.db.initialize())
        self.parser = EduTatarParser()
        self.logger = logging.getLogger(__name__)
        self.change = {"ru": "tr", "tr": "ru"}

    def get_main_menu_markup(self, language: str):
        return {
            "inline_keyboard": [
                [
                    {
                        "text": get_text(language, "daily_grades"),
                        "callback_data": "daily_grades",
                    },
                    {
                        "text": get_text(language, "quarter_grades"),
                        "callback_data": "quarter_grades",
                    },
                ],
                [
                    {
                        "text": get_text(language, "settings"),
                        "callback_data": "settings",
                    }
                ],
            ]
        }

    async def get_settings_markup(self, user_id: int, language: str):
        quarter = await self.db.get_quarter(user_id)
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "%s: %s"
                        % (
                            get_text(language, "language"),
                            get_text(language, language),
                        ),
                        "callback_data": "set_%s" % self.change[language],
                    }
                ],
                [
                    {
                        "text": "%s: %s"
                        % (
                            get_text(language, "rounding_rule"),
                            await self.db.get_rounding_rule(user_id),
                        ),
                        "callback_data": "change_rounding",
                    }
                ],
                [
                    {
                        "text": "%s: %s"
                        % (
                            get_text(language, "quarter"),
                            await self.db.get_quarter(user_id),
                        ),
                        "callback_data": "changeQuarter"
                        + str(quarter + 1 if quarter != 4 else 1),
                    }
                ],
                [
                    {
                        "text": get_text(language, "logout"),
                        "callback_data": "sureDeleteInfo",
                    }
                ],
                [
                    {
                        "text": get_text(language, "back"),
                        "callback_data": "back",
                    }
                ],
            ]
        }

    async def set_language_from_callback(self, update: bot_types.CallbackQuery):
        language = ""
        if update.data == "set_russian":
            language = "ru"
            await self.bot.answer_callback_query(update.id)
            await self.db.set_language(update.from_user.id, "ru")
            await self.bot.edit_message_text(
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                text=get_text(language, "language_applied"),
            )
        elif update.data == "set_tatar":
            language = "tr"
            await self.bot.answer_callback_query(update.id)
            await self.db.set_language(update.from_user.id, "tr")
            await self.bot.edit_message_text(
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                text=get_text(language, "language_applied"),
            )
        await self.bot.send_message(
            chat_id=update.from_user.id,
            text=get_text(language, "enter_login"),
            reply_markup={"remove_keyboard": True},
        )
        self.db.set_value(update.from_user.id, "state", "login")

    async def main_menu_message(self, update: bot_types.Message):
        user_id = update.from_user.id
        language = await self.db.get_language(user_id)
        await self.bot.send_message(
            user_id,
            get_text(language, "choose_option"),
            reply_markup=self.get_main_menu_markup(language),
        )

    async def show_daily_grades(
        self, user_id: int, language: str, update: bot_types.CallbackQuery
    ):
        login_and_password = await self.db.get_login_and_password(user_id)
        if login_and_password is None:
            """Should be unreachable state"""
            await self.bot.send_message(
                chat_id=update.from_user.id,
                text="Something went wrong. We apologise.",
            )  # TODO: do not do like that hehe
            return
        result, DNSID, dates1, dates2 = await self.parser.getDay(
            login_and_password[0],
            login_and_password[1],
            self.db.get_value(user_id, "DNSID"),
        )
        if DNSID is not None:
            self.db.set_value(user_id, "DNSID", DNSID)
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=result,
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "<--", "callback_data": dates1},
                        {"text": "-->", "callback_data": dates2},
                    ],
                    [
                        {
                            "text": get_text(language, "copy"),
                            "callback_data": "copy",
                        },
                        {
                            "text": get_text(language, "back"),
                            "callback_data": "back",
                        },
                    ],
                ]
            },
        )

    async def show_quarter_grades(
        self, user_id: int, language: str, update: bot_types.CallbackQuery
    ):
        login_and_password = await self.db.get_login_and_password(user_id)
        rounding_rule = await self.db.get_rounding_rule(user_id)
        quarter = await self.db.get_quarter(user_id)
        self.logger.debug(f"GOT ROUNDING RULE: {rounding_rule}")
        if login_and_password is None:
            await self.bot.send_message(
                chat_id=update.from_user.id,
                text="Something went wrong. We apologise.",
            )  # TODO: i don't know the case when it can be
            return
        result, DNSID = await self.parser.getTerm(
            login_and_password[0],
            login_and_password[1],
            termNum=quarter,
            DNSID=self.db.get_value(user_id, "DNSID"),
            rounding_rule=rounding_rule,
        )
        if DNSID is not None:
            self.db.set_value(user_id, "DNSID", DNSID)
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=result,
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": get_text(language, "first_quarter"),
                            "callback_data": "1",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "second_quarter"),
                            "callback_data": "2",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "third_quarter"),
                            "callback_data": "3",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "fourth_quarter"),
                            "callback_data": "4",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "year"),
                            "callback_data": "year",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "copy"),
                            "callback_data": "copy",
                        },
                        {
                            "text": get_text(language, "back"),
                            "callback_data": "back",
                        },
                    ],
                ]
            },
        )

    async def update_quarter_grades(
        self, user_id: int, language: str, update: bot_types.CallbackQuery
    ):
        login_and_password = await self.db.get_login_and_password(user_id)
        if login_and_password is None:
            await self.bot.send_message(
                chat_id=update.from_user.id,
                text="Something went wrong. We apologise.",
            )  # TODO: do not do like that hehe
            return
        rounding_rule = await self.db.get_rounding_rule(user_id)
        result, DNSID = await self.parser.getTerm(
            login_and_password[0],
            login_and_password[1],
            termNum=update.data,
            DNSID=self.db.get_value(user_id, "DNSID"),
            rounding_rule=rounding_rule,
        )
        if DNSID is not None:
            self.db.set_value(user_id, "DNSID", DNSID)
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=result,
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": get_text(language, "first_quarter"),
                            "callback_data": "1" if update.data != "1" else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "second_quarter"),
                            "callback_data": "2" if update.data != "2" else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "third_quarter"),
                            "callback_data": "3" if update.data != "3" else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "fourth_quarter"),
                            "callback_data": "4" if update.data != "4" else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "year"),
                            "callback_data": "year"
                            if update.data != "year"
                            else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "copy"),
                            "callback_data": "copy",
                        },
                        {
                            "text": get_text(language, "back"),
                            "callback_data": "back",
                        },
                    ],
                ]
            },
        )

    async def show_year_grades(
        self, user_id: int, language: str, update: bot_types.CallbackQuery
    ):
        login_and_password = await self.db.get_login_and_password(user_id)
        if login_and_password is None:
            await self.bot.send_message(
                chat_id=update.from_user.id,
                text="Something went wrong. We apologise.",
            )  # TODO: upper to-do
            return
        result, DNSID = await self.parser.getYear(
            login_and_password[0],
            login_and_password[1],
            DNSID=self.db.get_value(user_id, "DNSID"),
        )
        if DNSID is not None:
            self.db.set_value(user_id, "DNSID", DNSID)
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=result,
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": get_text(language, "first_quarter"),
                            "callback_data": "1" if update.data != "1" else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "second_quarter"),
                            "callback_data": "2" if update.data != "2" else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "third_quarter"),
                            "callback_data": "3" if update.data != "3" else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "fourth_quarter"),
                            "callback_data": "4" if update.data != "4" else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "year"),
                            "callback_data": "year"
                            if update.data != "year"
                            else "pass",
                        }
                    ],
                    [
                        {
                            "text": get_text(language, "copy"),
                            "callback_data": "copy",
                        },
                        {
                            "text": get_text(language, "back"),
                            "callback_data": "back",
                        },
                    ],
                ]
            },
        )

    async def update_language_and_message_settings(
        self, user_id: int, language: str, update: bot_types.CallbackQuery
    ):
        if update.data == "set_ru":
            await self.db.set_language(user_id, "ru")
        elif update.data == "set_tr":
            await self.db.set_language(user_id, "tr")
        user_id = update.from_user.id
        language = await self.db.get_language(user_id)
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=get_text(language, "here_you_can_change_settings"),
            reply_markup=await self.get_settings_markup(user_id, language),
        )

    async def go_back_callback(
        self, user_id: int, language: str, update: bot_types.CallbackQuery
    ):
        user_id = update.from_user.id
        language = await self.db.get_language(user_id)
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=get_text(language, "choose_option"),
            reply_markup=self.get_main_menu_markup(language),
        )

    async def send_message_change_rounding(
        self, user_id: int, language: str, update: bot_types.CallbackQuery
    ):
        await self.bot.send_message(user_id, get_text(language, "enter_rounding"))
        self.db.set_value(user_id, "state", "enter_rounding")

    async def change_daily_grades(
        self, user_id: int, language: str, update: bot_types.CallbackQuery
    ):
        login_and_password = await self.db.get_login_and_password(user_id)
        if login_and_password is None:
            await self.bot.send_message(
                chat_id=update.from_user.id,
                text="Something went wrong. We apologise.",
            )  # TODO: do not do like that hehe
            return
        original_DNSID = self.db.get_value(user_id, "DNSID")
        if original_DNSID is None:
            await self.bot.answer_callback_query(update.id, "Подождите...")
        result, DNSID, dates1, dates2 = await self.parser.getDay(
            login_and_password[0],
            login_and_password[1],
            original_DNSID,
            date=int(update.data),
            language=language,
        )
        if DNSID is not None:
            self.db.set_value(user_id, "DNSID", DNSID)
        await self.bot.edit_message_text(
            message_id=update.message.message_id,
            chat_id=update.message.chat.id,
            text=result,
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "<--", "callback_data": dates1},
                        {"text": "-->", "callback_data": dates2},
                    ],
                    [
                        {
                            "text": get_text(language, "copy"),
                            "callback_data": "copy",
                        },
                        {
                            "text": get_text(language, "back"),
                            "callback_data": "back",
                        },
                    ],
                ]
            },
            parse_mode="HTML",
        )

    async def settings_menu(self, update: bot_types.CallbackQuery):
        user_id = update.from_user.id
        language = await self.db.get_language(update.from_user.id)
        await self.bot.edit_message_text(
            chat_id=update.from_user.id,
            message_id=update.message.message_id,
            text=get_text(language, "here_you_can_change_settings"),
            reply_markup=await self.get_settings_markup(user_id, language),
        )

    async def send_message_choose_language(self, update: bot_types.Message):
        message = await self.bot.send_message(
            update.from_user.id,
            "✋ Здравствуйте, выберите свой язык:",
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "Русский 🇷🇺", "callback_data": "set_russian"},
                        {"text": "Татарский", "callback_data": "set_tatar"},
                    ]
                ]
            },
        )
        self.db.set_value(update.from_user.id, "message_language", message.message_id)

    async def are_you_sure(self, user_id, language, update):
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=get_text(language, "are_you_sure"),
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": get_text(language, "yes"),
                            "callback_data": "deleteInfo",
                        },
                        {
                            "text": get_text(language, "no"),
                            "callback_data": "back",
                        },
                    ]
                ]
            },
        )

    async def language_configure_start_bot(self, user_id: int, update):
        if isinstance(self.db.get_value(user_id, "message_language"), int):
            # i don't care if it makes an error.
            await self.bot.make_request(
                "deleteMessage",
                {
                    "chat_id": user_id,
                    "message_id": self.db.get_value(user_id, "message_language"),
                },
            )
        await self.send_message_choose_language(update)

    async def update_default_quarter(
        self, user_id, language, update: bot_types.CallbackQuery
    ):
        self.logger.debug(f"QUARTER NOW: {int(update.data[-1])}")
        await self.db.set_quarter(user_id, int(update.data[-1]))
        language = await self.db.get_language(user_id)
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=update.message.message_id,
            text=get_text(language, "here_you_can_change_settings"),
            reply_markup=await self.get_settings_markup(user_id, language),
        )

    async def delete_info(self, user_id, language, update):
        await self.db.delete_login_and_password(user_id)
        await self.bot.send_message(
            chat_id=update.from_user.id,
            text=get_text(language, "enter_login"),
            reply_markup={"remove_keyboard": True},
        )
        self.db.set_value(update.from_user.id, "state", "login")

    async def check_login_and_password(self, user_id: int):
        login = self.db.get_value(user_id, "login")
        password = self.db.get_value(user_id, "password")
        DNSID = await self.parser.get_DNSID(login=login, password=password)
        if DNSID is None:
            return False
        else:
            self.db.set_value(user_id, "DNSID", DNSID)
            return True

    async def onCallbackQuery(self, update: bot_types.CallbackQuery):  # noqa: C901
        user_id = update.from_user.id
        language = await self.db.get_language(user_id)
        login_and_password = await self.db.get_login_and_password(user_id)

        if update.data in ("set_russian", "set_tatar"):
            await self.set_language_from_callback(update)
        elif login_and_password is None:
            # Database was destructed or something and now
            # we don't have this user in database
            self.db.set_value(user_id, "state", "language")
            await self.language_configure_start_bot(user_id, update)
            return
        elif update.data == "daily_grades":
            await self.show_daily_grades(user_id, language, update)
        elif update.data == "quarter_grades":
            await self.show_quarter_grades(user_id, language, update)
        elif update.data in ("1", "2", "3", "4"):
            await self.update_quarter_grades(user_id, language, update)
        elif "changeQuarter" in update.data:
            await self.update_default_quarter(user_id, language, update)
        elif update.data == "year":
            await self.show_year_grades(user_id, language, update)
        elif update.data == "settings":
            await self.settings_menu(update)
        elif update.data in ("set_ru", "set_tr"):
            await self.update_language_and_message_settings(user_id, language, update)
        elif update.data == "change_rounding":
            await self.send_message_change_rounding(user_id, language, update)
        elif update.data == "copy":
            await self.bot.send_message(
                user_id, update.message.text, entities=update.message.entities
            )
        elif update.data == "back":
            await self.go_back_callback(user_id, language, update)
        elif update.data == "sureDeleteInfo":
            await self.are_you_sure(user_id, language, update)
        elif update.data == "deleteInfo":
            await self.delete_info(user_id, language, update)
        elif update.data.isnumeric():
            await self.change_daily_grades(user_id, language, update)
        elif update.data == "pass":
            await self.bot.answer_callback_query(update.id)

    async def onMessageOnly(self, update: bot_types.Message):  # noqa: C901
        user_id = update.from_user.id
        # checking for group message. My bot doesn't support group messages.
        if user_id != update.chat.id:
            return
        state = self.db.get_value(user_id, "state")
        language = await self.db.get_language(user_id)
        login_and_password = await self.db.get_login_and_password(user_id)
        self.logger.debug(f"{state}{language}{login_and_password}")
        if state is None:
            if language is not None:
                if login_and_password is not None:
                    self.db.set_value(user_id, "state", "main")
                    await self.main_menu_message(update)
                    return
                else:
                    await self.bot.send_message(
                        chat_id=update.from_user.id,
                        text=get_text(language, "enter_login"),
                        reply_markup={"remove_keyboard": True},
                    )
                    self.db.set_value(update.from_user.id, "state", "login")
                    return
            self.db.set_value(user_id, "state", "language")
            await self.send_message_choose_language(update)
        elif state == "language":
            await self.language_configure_start_bot(user_id, update)
        elif state == "login":
            if not update.text.isnumeric():
                await self.bot.send_message(
                    chat_id=user_id,
                    text=get_text(language, "incorrect_login_and_password"),
                )
                return
            self.db.set_value(user_id, "login", update.text)
            self.db.set_value(user_id, "state", "password")
            await self.bot.send_message(
                chat_id=user_id, text=get_text(language, "enter_password")
            )
        elif state == "password":
            self.db.set_value(user_id, "password", update.text)
            await self.bot.send_message(
                chat_id=user_id,
                text=get_text(language, "let_me_check_login_and_password"),
            )
            result_checking = await self.check_login_and_password(user_id)
            if not result_checking:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=get_text(language, "incorrect_login_and_password"),
                )
                self.db.set_value(user_id, "state", "login")
            else:
                await self.db.set_login_and_password(
                    user_id,
                    self.db.get_value(user_id, "login"),
                    self.db.get_value(user_id, "password"),
                )
                self.db.set_value(user_id, "state", "main")
                await self.bot.send_message(
                    user_id,
                    get_text(language, "thanks"),
                    reply_markup={
                        "keyboard": [["Меню"]],
                        "one_time_keyboard": False,
                        "resize_keyboard": True,
                    },
                )
                await self.main_menu_message(update)
        elif state == "enter_rounding":
            print("CHECK ROUNDING")
            if (
                update.text is None
                or update.from_user is None
                or not update.text.isnumeric()
                or len(update.text) != 2
                or not (10 <= int(update.text) <= 99)
            ):
                await self.bot.send_message(
                    update.from_user.id,
                    get_text(language, "incorrect_rounding"),
                )
                return
            else:
                rounding_rule = int(update.text)
                assert 10 <= rounding_rule <= 99, "how it is even possible"
                await self.db.set_rounding_rule(user_id, rounding_rule)
                await self.bot.send_message(
                    user_id, get_text(language, "successfully_changed")
                )
                self.db.set_value(user_id, "state", "main")
                await self.main_menu_message(update)
        elif state == "main":
            await self.main_menu_message(update)

    def get_funcs(self):
        return [
            [self.onMessageOnly, bot_types.Handlers.onMessageOnly],
            [self.onCallbackQuery, bot_types.Handlers.onCallbackQuery],
        ]
