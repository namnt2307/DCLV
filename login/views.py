from django.shortcuts import render
from django.views import View
from django.contrib.auth import authenticate
# Create your views here.
class login_app(View):
    def get(self,request):
        return render(request,'login/login.html')
    def user_auth(self, request):
        user_name = request.POST.get('user_name')
        password = request.POST.get('password')