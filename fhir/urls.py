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
    path('<str:group_name>/<str:user_name>/<str:patient_identifier>/encounter/',views.encounter.as_view(), name='encounter'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/hanhchinh', views.hanhchinh.as_view(), name='hanhchinh'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/service', views.service.as_view(), name='service'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/<str:service_id>/ketqua', views.ketqua.as_view(), name='ketqua'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/dangky', views.dangky.as_view(), name='dangky'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/hoibenh', views.hoibenh.as_view(), name='hoibenh'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/xetnghiem', views.xetnghiem.as_view(), name='xetnghiem'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/sieuam', views.sieuam.as_view(), name='sieuam'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/save', views.save.as_view(), name='save'),
    path('<str:group_name>/<str:user_name>/patient-view/',views.patient_view,name="patient-view"),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)