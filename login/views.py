from django.shortcuts import render
from django.views import View
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model
from .forms import UserCreationForm
# Create your views here.


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
            group_name = custom_user_model.objects.get(
                username=user_name).group_name
            return HttpResponseRedirect(f'/user/{group_name}/{user_name}')
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
