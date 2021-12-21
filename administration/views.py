from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import PractitionerForm
from .models import PractitionerModel, ClinicalDepartment
from lib import dttype as dt
from django.contrib import messages
import requests
from django.template.defaulttags import register
# Create your views here.
fhir_server = "http://10.0.0.25:8080/fhir"

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def make_range(num):
    return range(num)

@login_required(login_url='/login/')
def administration_view(request):
    return render(request, 'administration/index.html')


class staff(LoginRequiredMixin, View):
    login_url = "/login/"
     
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)
    
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
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)
    
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
            user = get_user_model().objects.get(username=resource_identifier)
            user.delete()
        elif resource_type == 'location':
            pass
        return HttpResponseRedirect(url_next)
    else:
        return HttpResponseRedirect("/login/")
        
class staff_info(LoginRequiredMixin, View):
    login_url = "/login/"
    
    def dispatch(self, request, *args, **kwargs):
        if not kwargs.get('practitioner_identifier'):
            messages.error('Trang bạn tìm không khả dụng')
            return HttpResponseRedirect('/')
        try: 
            PractitionerModel.objects.get(identifier = kwargs['practitioner_identifier'])
            
        except PractitionerModel.DoesNotExist:
            messages.error(request, "Mã nhân viên không hợp lệ")
            return HttpResponseRedirect('/')
        if request.user.role != 'admin' and request.user.username != kwargs['practitioner_identifier']:
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return HttpResponseRedirect('/')
        # Checks pass, let http method handlers process the request
        return super().dispatch(request, *args, **kwargs)
    
    
    def get(self, request, practitioner_identifier):
        practitioner = PractitionerModel.objects.get(identifier=practitioner_identifier)
        practitioner_form = PractitionerForm()
        context = {
            'practitioner': practitioner,
            'practitioner_form': practitioner_form
        }
        return render(request, 'administration/staff_info.html', context)
        
        
    def post(self, request, practitioner_identifier):
        practitioner = PractitionerModel.objects.get(identifier=practitioner_identifier)
        practitioner_update = PractitionerForm(request.POST or None, instance=practitioner)
        print(request.POST)
        if practitioner_update.is_valid():
            practitioner_id = dt.query_practitioner(practitioner_identifier, query_type='id')
            print(practitioner_id)
            practitioner_data = request.POST.copy()
            practitioner_data['id'] = practitioner_id['id']
            practitioner_resource = dt.create_practitioner_resource(practitioner_data)
            put_practitioner = requests.put(fhir_server + "/Practitioner/" + practitioner_id['id'], headers={
                'Content-type': 'application/xml'}, data=practitioner_resource.decode('utf-8'))            
            if put_practitioner.status_code == 200:
                practitioner_update.save()
                messages.success(request, "Cập nhật thông tin thành công")
                return HttpResponseRedirect(self.request.path_info)
            else:
                messages.error(request, "Không cập nhật thành công")
                return HttpResponseRedirect(self.request.path_info)
        else:
            print(practitioner_update.errors)
            messages.error(request, "Thông tin cung cấp không hợp lệ")
            return HttpResponseRedirect(self.request.path_info)
        
            
            
class department(LoginRequiredMixin, View):
    login_url = '/login/'
    
    def get(self, request):
        department_categories = ClinicalDepartment.objects.order_by().values_list('department_category', flat=True).distinct()
        departments = {}
        for category in department_categories:
            departments[category] = ClinicalDepartment.objects.filter(department_category=category)
        context = {
            'department_categories': department_categories,
            'departments': departments
        }    
        return render(request, 'administration/department.html', context)
        
        
    def post(self, request):
        department_name = request.POST['department_name']
        department_category = request.POST['department_category']
        department_type = request.POST['department_type']
        try:
            ClinicalDepartment.objects.create(department_name=department_name, department_category=department_category, department_type=department_type)
            messages.success(request, "Thêm thành công")
            return HttpResponseRedirect(self.request.path_info)
        except:
            messages.error(request, "Thêm không thành công")
            return HttpResponseRedirect(self.request.path_info)