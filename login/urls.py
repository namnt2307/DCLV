from . import views
from django.urls import path, include

urlpatterns = [
    path('',views.login_app.as_view(),name="index"),
    ]