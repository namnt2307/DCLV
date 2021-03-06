from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = 'login'
urlpatterns = [
    path('',views.login_app.as_view(),name="index"),
    path('register/',views.register_app.as_view(),name="register"),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)