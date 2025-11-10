from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'user/home.html')

def category(request):
    return render(request, 'user/category.html')

def cart(request):
    return render(request, 'user/cart.html')

def history(request):
    return render(request, 'user/history.html')


def mypage(request):
    return render(request, 'user/mypage.html')

def alert(request):
    return render(request, 'user/alert.html')