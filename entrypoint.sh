/usr/bin/python3 manage.py makemigrations login
/usr/bin/python3 manage.py makemigrations fhir
/usr/bin/python3 manage.py migrate

export DJANGO_SUPERUSER_PASSWORD=12345678
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=namnt96@fpt.com.vn

/usr/bin/python3 manage.py createsuperuser --noinput