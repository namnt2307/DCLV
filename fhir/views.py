from django.shortcuts import render
from django.http import HttpResponse , request
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your views here.
@login_required(login_url='/login/')
def user_app(request,group_name,user_name):
    user_id = User.objects.get(username=user_name).id
    if request.user.groups.filter(name='doctor'):
        page = 'fhir/doctor.html'
    if request.user.groups.filter(name='patient'):
        page = 'fhir/patient.html'

    return render(request,page,{'user_id':user_id,'group_name':group_name})



        