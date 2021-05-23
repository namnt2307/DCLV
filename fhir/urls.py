from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = 'fhir'
urlpatterns = [
    path('<str:group_name>/<str:user_name>/',views.user_app,name="user_detail"),
    path('<str:group_name>/<str:user_name>/create/',views.register.as_view(),name="register"),
    path('<str:group_name>/<str:user_name>/upload/',views.upload.as_view(),name="upload"),
    path('<str:group_name>/<str:user_name>/search/',views.search.as_view(),name="search"),

    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)