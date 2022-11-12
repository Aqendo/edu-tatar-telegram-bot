from datetime import datetime

strings = {
    "ru": {
        "language_applied": "<b>Ваш язык успешно сохранён, изменить вы его сможете в настройках.</b>",
        "enter_login": "Введите ваш <b>логин</b> от edu.tatar.ru",
        "enter_password": "Введите ваш <b>пароль</b> от edu.tatar.ru",
        "let_me_check_login_and_password": "Сейчас проверю данные на правильность, подождите.",
        "incorrect_login_and_password": "Упс, проверка введённых данных не увенчалась успехом. Может быть два варианта:\n" +
                                        "- Вы ввели неверную пару логина и пароля\n" +
                                        "- Серверы edu.tatar.ru временно не работают." +
                                        "Если вы убеждены, что ваши логин и пароль точно корректны, попробуйте через несколько минут.\n\n" +
                                        "Введите ваш **логин** от edu.tatar.ru",
        "choose_option": "<b>Выберите действие:</b>",
        "daily_grades": "Оценки за день",
        "quarter_grades": "Оценки за четверть",
        "first_quarter": "1-ая четверть",
        "second_quarter": "2-ая четверть",
        "third_quarter": "3-ая четверть",
        "fourth_quarter": "4-ая четверть",
        "year": "Год",
        "copy": "Дублировать",
        "back": "Назад",
        "thanks": "Спасибо за регистрацию в боте.",
        "settings": "Настройки",
        "here_you_can_change_settings": "В этом разделе вы можете менять настройки бота:",
        "language": "Язык",
        "ru": "Русский",
        "tr": "Татарский"
    },
    "tr": {

    }
}



def get_text(language, string):
    try:
        return strings[language][string]
    except KeyError as e:
        print(e)
        return ""