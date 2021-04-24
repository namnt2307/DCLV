from . import views
from django.urls import path, include

urlpatterns = [
    path('',views.index_class.as_view(),name="index"),
    # path('',include('django.contrib.auth.urls')),
    ]