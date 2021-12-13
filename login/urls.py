from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = 'login'
urlpatterns = [
    path('login/',views.login_app.as_view(),name="index"),
    path('register/',views.register_app.as_view(),name="register"),
    path('logout/', views.logout_request,name="logout"),
    path("change_password/", views.change_password.as_view(), name="change_password")
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)