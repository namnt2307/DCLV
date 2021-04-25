from django.shortcuts import render
from django.views import View
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
# Create your views here.
class login_app(View):
    def get(self,request):
        return render(request,'login/login.html')
    
    def post(self,request):
        user_name = request.POST.get('username')
        password = request.POST.get('password')
        my_user = authenticate(username=user_name,password=password,)
        if my_user is None:
            return HttpResponse('User khong ton tai')
        login(request,my_user)
        if request.user.groups.filter(name='doctor'):
            page = 'fhir/doctor.html'
        if request.user.groups.filter(name='patient'):
            page = 'fhir/patient.html'
        return render(request,page)

