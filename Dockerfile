FROM python:3.8.8-alpine3.13

LABEL MAINTAINER NAMTUA

EXPOSE 8000

WORKDIR /doan

COPY requirements.txt /doan
RUN apk update && apk add --no-cache build-base gcc alpine-sdk default-libmysqlclient-dev \
    && pip3 install -r requirements.txt && rm -rf /var/cache/apk/* 

COPY . /doan
RUN chmod 777 /doan/entrypoint.sh

ENTRYPOINT [ "./doan/entrypoint.sh" ]
CMD [ "python3", "manage.py", "runserver","0.0.0.0:8000" ]


