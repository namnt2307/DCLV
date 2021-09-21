from django.http.response import HttpResponse
from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
# Create your views here.

@login_required(login_url='/login/')
def administration_view(request):
    HttpResponse("Logged in!!")