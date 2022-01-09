FROM python:3.8.8-alpine3.13

LABEL MAINTAINER NAMTUA

EXPOSE 8000

WORKDIR /doan

COPY requirements.txt /doan
RUN apk update && apk add --no-cache musl-dev build-base gcc alpine-sdk mariadb-connector-c-dev python3-dev py3-setuptools jpeg-dev zlib-dev \
    && pip3 install -r requirements.txt && rm -rf /var/cache/apk/* 

ENV FHIR_SERVER="http://35.219.75.55:8080/fhir"
COPY . /doan
# COPY entrypoint.sh /doan/entrypoint.sh
# RUN chmod 777 /doan/entrypoint.sh

# ENTRYPOINT [ "/bin/sh","entrypoint.sh" ]
CMD [ "python3", "manage.py", "runserver","0.0.0.0:8000" ]


