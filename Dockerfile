FROM python:3.10

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y nodejs npm

RUN pip install -r requirements.txt

CMD gunicorn -w 4 -b 0.0.0.0:$PORT app:app
