import logging
import re
import time
import traceback
import typing
from datetime import datetime
from os import getenv

import aiohttp
from bs4 import BeautifulSoup
from dotenv import find_dotenv, load_dotenv

from .languages import get_text

load_dotenv(find_dotenv())
if getenv("PROXY", "") == "":
    proxy = ""
else:
    proxy = getenv("PROXY", "")


class EduTatarParser:
    # _backslash = "\n"  # WHY PYTHON HAS A REGEX TO NOT HAVE \ IN THE FSTRING
    _regexDays = re.compile(r"day\?for=(\d+)")
    _logon_page_detector_word = "apastovo"
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0",  # noqa: E501
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",  # noqa: E501
        "Accept-Language": "en-US,en;q=0.5",
        "Origin": "https://edu.tatar.ru",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://edu.tatar.ru/logon",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    def __init__(self):
        self.session = aiohttp.ClientSession(headers=self._headers)
        self.logger = logging.getLogger(__name__)

    months = {
        "Янв": 1,
        "Фев": 2,
        "Мар": 3,
        "Апр": 4,
        "Мая": 5,
        "Июн": 6,
        "Июл": 7,
        "Авг": 8,
        "Сен": 9,
        "Окт": 10,
        "Ноя": 11,
        "Дек": 12,
    }

    days_of_the_week = [
        {"ru": "Понедельник", "tr": "Дүшәмбе"},
        {"ru": "Вторник", "tr": "Сишәмбе"},
        {"ru": "Среда", "tr": "Чәршәмбе"},
        {"ru": "Четверг", "tr": "Пәнҗешәмбе"},
        {"ru": "Пятница", "tr": "Җомга"},
        {"ru": "Суббота", "tr": "Шимбә"},
        {"ru": "Воскресенье", "tr": "Якшәмбе"},
    ]

    def get_count_of_five_to_the_next_mark(
        self, score: str, rounding_rule: int, grades: str
    ):
        assert rounding_rule is not None
        if score == "" or grades == "":
            return ""
        self.logger.debug(
            "Score given: {}, Rounding rule given: {}, Grades given: {}".format(
                score, rounding_rule, grades
            )
        )
        score_float = float(score)
        if score_float >= 4 + rounding_rule / 100:
            return "(+0)"
        elif round(score_float % 1, 2) * 100 < rounding_rule:
            grades = [int(i) for i in list(grades)]
            count_added = 0
            while round(sum(grades) / len(grades) % 1, 2) * 100 < rounding_rule:
                grades.append(5)
                count_added += 1
            return f"(+{count_added})"
        elif round(score_float % 1, 2) * 100 >= rounding_rule:
            grades = [int(i) for i in list(grades)]
            count_added = 0
            next_mark = int(score[0]) + 1
            while round(sum(grades) / len(grades), 2) < next_mark + round(
                rounding_rule / 100, 2
            ):
                grades.append(5)
                count_added += 1
            return f"(+{count_added})"

    def get_day_of_week(self, language: str, string: str):
        self.logger.debug("GET_DAY_OF_THE_WEEK %s %s" % (language, string))
        string = string.split(" ")
        return self.days_of_the_week[
            datetime.weekday(
                datetime(
                    int(string[2]),
                    int(self.months[string[1][0:3]]),
                    int(string[0]),
                )
            )
        ][language]

    async def get_DNSID(self, login, password):
        data = {
            "main_login2": login,
            "main_password2": password,
        }
        print("Login: {}, password: {}".format(login, password))
        try:
            async with aiohttp.ClientSession(headers=self._headers) as session:
                async with session.post(
                    "https://edu.tatar.ru/logon", data=data, proxy=proxy
                ) as response:
                    text = await response.text()
                    if "Мой дневник" in text:
                        self.logger.info(
                            "Response cookies: {}".format(response.cookies)
                        )
                        return response.cookies["DNSID"]
                    else:
                        return None
        except Exception:
            traceback.print_ext()
            return None

    async def getDay(
        self,
        login: str,
        password: str,
        DNSID: str = "",
        delimeter: int = 47,
        changed: bool = False,
        date: int = -1,
        language: str = "ru",
    ) -> typing.Union[typing.Tuple[str, typing.Union[str, None], str, str], None]:
        self.logger.debug(
            "GET_DAY, login: %s, password: %s, DNSID: %s, delimeter: %d, changed: %s, date: %d, language: %s"
            % (login, password, DNSID, delimeter, changed, date, language)
        )
        if date == -1:
            date = time.time()
        result = ""
        async with aiohttp.ClientSession(
            headers=self._headers, cookies={"DNSID": DNSID}
        ) as session:
            async with session.post(
                "https://edu.tatar.ru/user/diary/day",
                params={"for": str(date)},
                proxy=proxy,
            ) as response:
                response_text = await response.text()
                if (
                    self._logon_page_detector_word in response_text
                ):  # some kind of "indicator" for /logon page
                    DNSID = await self.get_DNSID(login, password)
                    if DNSID is None:
                        return None
                    return await self.getDay(
                        login, password, DNSID, delimeter, True, date, language
                    )
                bs4 = BeautifulSoup(response_text, "lxml")
                dates = re.findall(self._regexDays, response_text)
                datee = bs4.find("td", class_="d-date").text.strip()
                result += (
                    "<b>"
                    + self.get_day_of_week(language, datee)
                    + " - "
                    + datee
                    + "</b>\n"
                    + "-" * delimeter
                    + "\n"
                )
                tbody = bs4.find("table", class_="main").tbody
                for tr in tbody.find_all(
                    "tr",
                    style=lambda value: value and "text-align: center;" in value,
                ):
                    tds = tr.find_all("td")
                    result += "<b>" + tds[0].text + "</b>\n"
                    result += tds[1].text + ":\n"
                    result += "<code>" + tds[2].text.strip() + "</code>\n"
                    string_marks = ""
                    marks_tr = tds[4].tr
                    if marks_tr is not None:
                        string_marks += f"\n{get_text(language, 'marks')}: "
                        if "Болел" in tds[3].text:
                            string_marks += "б "
                        for i in marks_tr.find_all("td"):
                            string_marks += i.text + "/"
                        string_marks = string_marks.rstrip("/")
                    result = result.rstrip(" ").rstrip("\n")
                    result += string_marks + "\n" + "-" * delimeter + "\n"
                result = result.rstrip("\n" + "-" * delimeter + "\n")
                return result, (DNSID if changed else None), dates[0], dates[1]

    async def getTerm(
        self,
        login: str,
        password: str,
        termNum: int = 1,
        DNSID: str = "",
        changed: bool = False,
        rounding_rule: int = 50,
    ) -> typing.Union[typing.Tuple[str, typing.Union[str, None]], None]:
        result = ""
        async with aiohttp.ClientSession(
            headers=self._headers, cookies={"DNSID": DNSID}
        ) as session:
            async with session.post(
                "https://edu.tatar.ru/user/diary/term",
                params={"term": str(termNum)},
                proxy=proxy,
            ) as response:
                responseText = await response.text()
                if (
                    self._logon_page_detector_word in responseText
                ):  # some kind of "indicator" for /logon page
                    DNSID = await self.get_DNSID(login, password)
                    if DNSID is None:
                        return None
                    return await self.getTerm(
                        login=login,
                        password=password,
                        termNum=termNum,
                        DNSID=DNSID,
                        changed=True,
                        rounding_rule=rounding_rule,
                    )
                bs4 = BeautifulSoup(responseText, "lxml")
                tbody = bs4.find("table", class_="term-marks").tbody
                trs = tbody.find_all("tr")
                for tr in trs[:-1]:
                    tds = tr.find_all("td")
                    grades = "".join([i.text for i in tds[1:-3]])
                    itog_mark = tds[-1].text.removeprefix("\n").lstrip()
                    result += "%s: %s - %s%s%s\n" % (
                        tds[0].text,
                        grades,
                        tds[-3].text,
                        self.get_count_of_five_to_the_next_mark(
                            score=tds[-3].text,
                            rounding_rule=rounding_rule,
                            grades=grades,
                        ),
                        (f"[{itog_mark}]" if tds[-1].text != "\n" else ""),
                    )
                tds_of_itog = trs[-1].find_all("td")
                result += "Итого {%s} [%s]" % (
                    tds_of_itog[-3].text,
                    tds_of_itog[-1].text,
                )
                return result.replace("Основы безопасности жизнедеятельности", "ОБЖ"), (
                    DNSID if changed else None
                )

    async def getYear(self, login, password, DNSID="", changed=False):
        async with aiohttp.ClientSession(
            headers=self._headers, cookies={"DNSID": DNSID}
        ) as session:
            async with session.post(
                "https://edu.tatar.ru/user/diary/term",
                params={"term": "year"},
                proxy=proxy,
            ) as response:
                response_text = await response.text()
                if (
                    "apastovo" in response_text
                ):  # some kind of "indicator" for /logon page
                    DNSID = await self.get_DNSID(login, password)
                    if DNSID is None:
                        return None
                    return await self.getYear(
                        login=login,
                        password=password,
                        DNSID=DNSID,
                        changed=True,
                    )
                bs4 = BeautifulSoup(response_text, "lxml")
                tbody = bs4.find("table", class_="table").tbody
                trs = tbody.find_all("tr")
                result = ""
                for tr in trs:
                    tds = tr.find_all("td")
                    result += "%s: %s\n" % (
                        tds[0].text.strip(),
                        "".join([i.text.strip() for i in tds[1:-1]]),
                    )
                return result.replace("Основы безопасности жизнедеятельности", "ОБЖ"), (
                    DNSID if changed else None
                )
