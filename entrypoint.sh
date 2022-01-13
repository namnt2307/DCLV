#!/bin/bash
python3 manage.py makemigrations login
python3 manage.py makemigrations fhir
python3 manage.py migrate

export DJANGO_SUPERUSER_PASSWORD=12345678
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=namnt96@fpt.com.vn

python3 manage.py createsuperuser --noinput

python3 manage.py shell < fhir/disease.py