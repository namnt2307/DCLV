from . import views
from django.urls import path, include

urlpatterns = [
    path('',views.index_class.as_view(),name="index"),
    # path('',views.fhir_index)
    ]