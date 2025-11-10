from django.shortcuts import render
from django.http import HttpResponse

def top(request):
    return render(request, 'top.html')

# user側のビュー
def user_home(request):
    return render(request, 'user/home.html')

def user_category(request):
    return render(request, 'user/category.html')

def user_cart(request):
    return render(request, 'user/cart.html')

def user_history(request):
    return render(request, 'user/history.html')


def user_mypage(request):
    return render(request, 'user/mypage.html')

def user_alert(request):
    return render(request, 'user/alert.html')

# store側のビュー
def store_home(request):
    return render(request, 'store/home.html')

def store_list(request):
    return render(request, 'store/list.html')

def store_mypage(request):
    return render(request, 'store/mypage.html')

def store_alert(request):
    return render(request, 'store/alert.html')