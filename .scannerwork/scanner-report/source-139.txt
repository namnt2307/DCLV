from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model
from .forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required(login_url='/login/')
def redirect_page(request):
    if request.user.role == 'admin':
        return HttpResponseRedirect('/administration/')
    else:
        return HttpResponseRedirect('/fhir/')

class login_app(View):
    def get(self, request):
        return render(request, 'login/login.html')

    def post(self, request):
        custom_user_model = get_user_model()
        user_name = request.POST.get('username')
        password = request.POST.get('password')
        my_user = authenticate(request, username=user_name, password=password)
        if my_user is not None:
            login(request, my_user)
            role = custom_user_model.objects.get(
                username=user_name).role
            if role == "admin":
                return HttpResponseRedirect(f'/administration/')
            return HttpResponseRedirect(f'{self.request.GET.get("next", "/fhir/")}')
        else:
            message = 'Người dùng không tồn tại'
            return render(request, 'login/login.html', {'message': message})


class register_app(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'login/register.html', {'form': form})

    def post(self, request):
        if request.method == 'POST':
            form = UserCreationForm()
            user_regis = UserCreationForm(request.POST)
            if user_regis.is_valid():
                user_regis.save()
                message = 'Đăng kí thành công'
                return render(request, 'login/register.html', {'message': message, 'form': form})
            else:
                message = 'Không hợp lệ, vui lòng thử lại'
                return render(request, 'login/register.html', {'message': message, 'form': form})

def logout_request(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect('/login')


class change_password(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        return render(request, 'login/change_password.html')
    
    def post(self, request):
        user = get_user_model().objects.get(username=request.user.username)
        url_next = request.POST['url_next']
        if user.check_password(request.POST['old_password']):
            if request.POST['new_password_1'] == request.POST['new_password_2']:
                user.set_password(request.POST['new_password_1'])
                user.save()
                logout(request)
                messages.success(request, "Đổi mật khẩu thành công. Vui lòng đăng nhập lại !!!")
                return HttpResponseRedirect('/login/')
            else: 
                messages.error(request, "Mật khẩu mới không trùng khớp !!!")
                return HttpResponseRedirect(url_next)
        
        else:
            messages.error(request, "Mật khẩu cũ không chính xác !!!")
            return HttpResponseRedirect(url_next)            
        
    