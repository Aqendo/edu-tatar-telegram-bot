FROM python:3.10-slim
WORKDIR /app
COPY ./.env ./.env
COPY ./bot ./bot
COPY ./edutatar ./edutatar
COPY ./main.py ./main.py
COPY ./requirements.txt ./requirements.txt
RUN python -m pip install -r requirements.txt
CMD python main.py

