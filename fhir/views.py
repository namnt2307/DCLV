from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from .models import user_content
from django.contrib.auth.decorators import login_required

# Create your views here.
class index_class(View):
    def get(self,request):
        return render(request,'fhir/index.html')
@login_required(login_url='/accounts/login')
def ehr_content(request):
    pass
    # return  ehr_contents.object. 