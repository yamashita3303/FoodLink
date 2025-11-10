from django.shortcuts import render
from django.http import HttpResponse

def userhome(request):
    return render(request, 'user/home.html')

def category(request):
    return render(request, 'user/category.html')

def cart(request):
    return render(request, 'user/cart.html')

def history(request):
    return render(request, 'user/history.html')


def usermypage(request):
    return render(request, 'user/mypage.html')

def useralert(request):
    return render(request, 'user/alert.html')