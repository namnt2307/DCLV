from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = 'administration'
urlpatterns = [
    path("", views.administration_view, name="administration"),
    path("staff/", views.staff.as_view(), name="staff"),
    path("staff/add_staff", views.add_staff.as_view(), name="add_staff"),
    path("delete/", views.delete, name="delete")
]