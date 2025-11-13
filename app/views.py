from django.shortcuts import render
from django.http import HttpResponse
from .models import  Product
from django.db.models import Q  # ← 検索に便利な「OR検索」= どちらかが一方が当てはまったらおk
from django.shortcuts import render, get_object_or_404

def top(request):
    return render(request, 'top.html')

# user側のビュー
def user_home(request):
    query = request.GET.get("q", "").strip()  # 空文字も含めて取得
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
    else:
        products = Product.objects.all()  # 検索していない場合は全件
    return render(request, "user/home.html", {"products": products})




def user_food_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)  # pk=product_id が参照される
    return render(request, 'user/user_food_detail.html', {'product': product})



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