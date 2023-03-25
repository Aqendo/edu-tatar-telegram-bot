# edu.tatar.ru telegram client

И для этого я создал этот проект. 
## Установка
### Публичный инстанс:
- [@edutatarclientbot](https://t.me/edutatarclientbot)
### Локально
Здесь есть Dockerfile с которым вы можете легко разместить бота у себя на сервере

> Не забудьте создать `.env` файл с нужными перменными! Образец находится в `.env.example`
```bash
edu-tatar-telegram-bot $ docker build -t edu .
edu-tatar-telegram-bot $ docker run -it -d --name edu -v PATH/TO/YOUR/DB/FOLDER/ON/PC:/mountpoint edu
```
