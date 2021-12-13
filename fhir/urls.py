from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = 'fhir'
urlpatterns = [
    path('',views.user_app,name="user_detail"),
    path('create/',views.register.as_view(),name="register"),
    path('upload/',views.upload.as_view(),name="upload"),
    path('search/',views.search.as_view(),name="search"),
    path('display-detail/<str:patient_identifier>',views.display_detail,name="display_detail"),
    path('<str:patient_identifier>/encounter/',views.encounter.as_view(), name='encounter'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/hanhchinh', views.hanhchinh.as_view(), name='hanhchinh'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/toanthan', views.khambenh.as_view(), name='toanthan'),
    # path('encounter/<str:patient_identifier>/<str:encounter_identifier>/service', views.service.as_view(), name='service'),
    # path('encounter/<str:patient_identifier>/<str:encounter_identifier>/<str:service_identifier>/ketqua', views.ketqua.as_view(), name='ketqua'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/dangky', views.dangky.as_view(), name='dangky'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/hoibenh', views.hoibenh.as_view(), name='hoibenh'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/xetnghiem', views.xetnghiem.as_view(), name='xetnghiem'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/chitietxetnghiem/<str:service_identifier>', views.chitietxetnghiem.as_view(), name='chitietxetnghiem'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/thuthuat', views.thuthuat.as_view(), name='thuthuat'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/chitietthuthuat/<str:procedure_identifier>', views.chitietthuthuat.as_view(), name='chitietthuthuat'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/hinhanh', views.hinhanh.as_view(), name='hinhanh'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/chitiethinhanh/<str:service_identifier>', views.chitiethinhanh.as_view(), name='chitiethinhanh'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/thuoc', views.thuoc.as_view(), name='thuoc'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/chandoan/<str:service_identifier>', views.chandoan.as_view(), name='chandoan'),
    path('encounter/<str:patient_identifier>/<str:encounter_identifier>/save', views.save.as_view(), name='save'),
    path('<str:patient_identifier>/<str:encounter_identifier>/view_benhan', views.view_benhan.as_view(), name='view_benhan'),
    path('<str:patient_identifier>/<str:encounter_identifier>/view_xetnghiem', views.view_xetnghiem.as_view(), name='view_xetnghiem'),
    path('<str:patient_identifier>/<str:encounter_identifier>/view_thuthuat', views.view_thuthuat.as_view(), name='view_thuthuat'),
    path('<str:patient_identifier>/<str:encounter_identifier>/view_donthuoc', views.view_donthuoc.as_view(), name='view_donthuoc'),
    path('schedule/', views.schedule.as_view(), name="schedule"),
    path('manage_schedule/', views.manage_schedule.as_view(), name="manage_schedule"),
    path('delete/', views.delete, name='delete'),
    # path('patient-view/',views.patient_view,name="patient-view"),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)