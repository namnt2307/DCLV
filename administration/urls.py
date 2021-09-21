from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = 'administration'
urlpatterns = [
    path("", views.administration_view, name="administration"),
]