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
    path('<str:group_name>/<str:user_name>/display-detail/<str:patient_identifier>',views.display_detail,name="display_detail"),
    path('<str:group_name>/<str:user_name>/<str:patient_identifier>/encounter/',views.encounter.as_view(), name='encounter'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/hanhchinh', views.hanhchinh.as_view(), name='hanhchinh'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/toanthan', views.khambenh.as_view(), name='toanthan'),
    # path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/service', views.service.as_view(), name='service'),
    # path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/<str:service_identifier>/ketqua', views.ketqua.as_view(), name='ketqua'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/dangky', views.dangky.as_view(), name='dangky'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/hoibenh', views.hoibenh_.as_view(), name='hoibenh'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/xetnghiem', views.xetnghiem.as_view(), name='xetnghiem'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/<str:service_identifier>/chitietxetnghiem', views.chitietxetnghiem.as_view(), name='chitietxetnghiem'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/thuthuat', views.thuthuat.as_view(), name='thuthuat'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/<str:procedure_identifier>/chitietthuthuat', views.chitietthuthuat.as_view(), name='chitietthuthuat'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/hinhanh', views.hinhanh.as_view(), name='hinhanh'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/<str:service_identifier>/chitiethinhanh', views.chitiethinhanh.as_view(), name='chitiethinhanh'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/thuoc', views.thuoc.as_view(), name='thuoc'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/<str:service_identifier>/chandoan', views.chandoan.as_view(), name='chandoan'),
    path('<str:group_name>/<str:user_name>/encounter/<str:patient_identifier>/<str:encounter_identifier>/save', views.save.as_view(), name='save'),
    path('<str:group_name>/<str:user_name>/<str:patient_identifier>/<str:encounter_identifier>/view_benhan', views.view_benhan.as_view(), name='view_benhan'),
    path('<str:group_name>/<str:user_name>/<str:patient_identifier>/<str:encounter_identifier>/view_xetnghiem', views.view_xetnghiem.as_view(), name='view_xetnghiem'),
    path('<str:group_name>/<str:user_name>/<str:patient_identifier>/<str:encounter_identifier>/view_thuthuat', views.view_thuthuat.as_view(), name='view_thuthuat'),
    path('<str:group_name>/<str:user_name>/<str:patient_identifier>/<str:encounter_identifier>/view_donthuoc', views.view_donthuoc.as_view(), name='view_donthuoc'),
    path('delete/', views.delete, name='delete'),
    path('<str:group_name>/<str:user_name>/patient-view/',views.patient_view,name="patient-view"),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)