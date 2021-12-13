from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import PractitionerForm
from .models import PractitionerModel
from lib import dttype as dt
from django.contrib import messages
import requests
# Create your views here.
fhir_server = "http://10.0.0.25:8080/fhir"

@login_required(login_url='/login/')
def administration_view(request):
    return render(request, 'administration/index.html')


class staff(LoginRequiredMixin, View):
    login_url = "/login/"
    def get(self, request):
        practitioners = PractitionerModel.objects.all()
        context = {
            'practitioners': practitioners,
        }
        return render(request, 'administration/staff.html', context)
        
    def post(self, request):
        pass
        
        
class add_staff(LoginRequiredMixin, View):
    login_url = "/login/"
    def get(self, request):
        form = PractitionerForm()
        context = {
            'form': form
        }
        return render(request, 'administration/add_staff.html', context)
    
    def post(self, request):
        post_practitioner = None
        post = request.POST.copy()
        post['identifier'] = "P" + request.POST['identifier']
        request.POST = post
        form = PractitionerForm(request.POST or None)
        if form.is_valid():
            form.save()
            new_user = get_user_model().objects.create_user(username=request.POST['identifier'], role=request.POST['practitioner_role'], password="1")
            new_practitioner = dt.create_practitioner_resource(request.POST)
            if new_practitioner:
                post_practitioner = requests.post(fhir_server + "/Practitioner/", headers={
                    'Content-type': 'application/xml'}, data=new_practitioner.decode('utf-8'))
                if post_practitioner.status_code == 201:
                    messages.success(request, "Thêm thành công")
        else:
            messages.error(request, form.errors) 
        return HttpResponseRedirect("/administration/staff")
    
    
    
def delete(request):
    if request.method == "POST":
        resource_type = request.POST['resource_type']
        resource_identifier = request.POST['resource_identifier']
        url_next = request.POST['url_next']
        if resource_type == 'practitioner':
            resource = PractitionerModel.objects.get(identifier=resource_identifier)
            resource.delete()
        elif resource_type == 'location':
            pass
        return HttpResponseRedirect(url_next)
    else:
        return HttpResponseRedirect("/login/")
        
            