from . import views
from django.urls import path, include
urlpatterns = [
    path('<str:group_name>/<str:user_name>/',views.user_app,name="user_detail")
    ]