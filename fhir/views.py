from django.shortcuts import render
from django.http import HttpResponse , request
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.auth.decorators import login_required

# Create your views here.
class index_class(LoginRequiredMixin ,View):
    login_url = '/login/'
    def get(self,request):
        return render(request,'fhir/index.html')
        
# @login_required(login_url='/login/')
# def fhir_index(request):
#     # if request.user.has_perm('')
#     return  render(request,'fhir/index.html') 