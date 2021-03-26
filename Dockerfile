FROM python:3.7
MAINTAINER Tarjei N Skrede "tarjei.skrede@sesam.io"
COPY ./service /service

RUN pip install --upgrade pip

RUN pip install -r /service/requirements.txt

EXPOSE 5000/tcp

CMD ["python3", "-u", "./service/odata-simple.py"]
