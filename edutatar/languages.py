import logging
import traceback

__logger = logging.getLogger(__name__)
# flake8: noqa
strings = {
    "ru": {
        "language_applied": "✅ <b>Ваш язык успешно сохранён, изменить вы его сможете в настройках.</b>",
        "enter_login": "Введите ваш <b>логин</b> от edu.tatar.ru",
        "enter_password": "Введите ваш <b>пароль</b> от edu.tatar.ru",
        "let_me_check_login_and_password": "<i>Сейчас проверю данные на правильность, подождите.</i>",
        "incorrect_login_and_password": "Упс, проверка введённых данных не увенчалась успехом. Может быть два варианта:\n"
        + "- Вы ввели неверную пару логина и пароля\n"
        + "- Серверы edu.tatar.ru временно не работают."
        + "Если вы убеждены, что ваши логин и пароль точно корректны, попробуйте через несколько минут.\n\n"
        + "Введите ваш <b>логин</b> от edu.tatar.ru:",
        "choose_option": "<b>Выберите действие:</b>",
        "daily_grades": "Оценки за день",
        "quarter_grades": "Оценки за четверть",
        "first_quarter": "1-ая четверть",
        "second_quarter": "2-ая четверть",
        "third_quarter": "3-ая четверть",
        "fourth_quarter": "4-ая четверть",
        "year": "Год",
        "copy": "⬇ Дублировать️",
        "back": "↩ Назад",
        "thanks": "☺️ Спасибо за регистрацию в боте.",
        "settings": "Настройки ⚙",
        "here_you_can_change_settings": "⚙ В этом разделе вы можете менять настройки бота:",
        "language": "👅 Язык",
        "ru": "Русский 🇷🇺",
        "tr": "Татарский",
        "enter_rounding": "Введите число - правило округления оценок в вашей школе(9&lt;x&lt;100). Пример:\n"
        "<pre>60</pre> - балл округления будет <b>2.60/3.60/4.60</b>",
        "incorrect_rounding": "Вы ввели <b>неправильное</b> число, нужно вводить как в образце(9&lt;x&lt;100):\n"
        + "<pre>60</pre> для округления в <b>2.60/3.60/4.60</b>",
        "successfully_changed": "✅ Успешно изменено.",
        "rounding_rule": "⏺ Округление",
        "are_you_sure": "Вы уверены, что хотите выйти из аккаунта?",
        "yes": "Да",
        "no": "Нет",
        "logout": "Выйти из аккаунта",
        "quarter": "Четверть",
        "marks": "Оценки",
    },
    "tr": {
        "language_applied": "<b>Сезнең телегез уңышлы сакланган, сез аны көйләүләрдә үзгәртә аласыз.</b>",
        "enter_login": "Edu.tatar.ru сайтыннан <b>логин</b> кертегез",
        "enter_password": "Edu.tatar.ru сайтыннан <b>серсүзегезне</b> кертегез ",
        "let_me_check_login_and_password": "Мин мәгълүматның дөреслеген тикшерермен, зинһар, көтегез.",
        "incorrect_login_and_password": "Ой, кертелгән мәгълүматны тикшерү уңышлы булмады. Ике вариант булырга мөмкин:\n"
        + "- Сез дөрес булмаган кулланучы исемен һәм серсүз парын керттегез.\n"
        + "- Edu.tatar.ru серверлары вакытлыча түбән."
        + "Әгәр дә сезнең кулланучы исемегез һәм серсүзегез төгәл икәненә инансагыз, берничә минуттан соң кабатлап карагыз.\n\n"
        + "Edu.tatar.ru сайтыннан <b>логин</b> кертегез",
        "choose_option": "<b>Эшне сайлагыз:</b>",
        "daily_grades": "Көндәлек билгеләр",
        "quarter_grades": "Чирек билгеләр",
        "first_quarter": "1 нче чирек",
        "second_quarter": "2 нче чирек",
        "third_quarter": "3 нче чирек",
        "fourth_quarter": "4 нче чирек",
        "year": "Ел",
        "copy": "Күчермә",
        "back": "Кире",
        "thanks": "Бот белән теркәлгән өчен рәхмәт.",
        "settings": "Көйләүләр",
        "here_you_can_change_settings": "Бу бүлектә сез бот көйләнмәләрен үзгәртә аласыз:",
        "language": "Тел",
        "ru": "Русский",
        "tr": "Татар",
        "enter_rounding": "Мәктәбегездә классларны дөрес түгәрәкләү өчен номер кертегез. Мисал:\n"
        "<pre>60</pre> - түгәрәк балл булачак <b>2.60/3.60/4.60</b>",
        "incorrect_rounding": "Сез <b>ялгыш</b> номерын керттегез, сез аны мисалдагы кебек кертергә тиеш:\n"
        + "<pre>60</pre> әйләндерү өчен <b>2.60/3.60/4.60</b>",
        "successfully_changed": "Уңышлы үзгәртелде.",
        "rounding_rule": "Түгәрәкләү",
    },
}


def get_text(language, string):
    __logger.debug(
        "ASKED FOR STRING: {}, LANGUAGE: {}".format(string, language)
    )
    try:
        return strings[language][string]
    except KeyError as e:
        traceback.print_exc()
        return ""
