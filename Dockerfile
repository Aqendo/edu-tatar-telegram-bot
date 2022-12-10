FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN python -m pip install -r requirements.txt
CMD python main.py

