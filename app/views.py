from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import ProductForm
from .models import Product

# =========================
# トップページ
# =========================
def top(request):
    return render(request, 'top.html')

# =========================
# user側ビュー
# =========================
def user_home(request):
    products = Product.objects.all()
    return render(request, 'user/home.html', {'products': products})

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

# =========================
# store側ビュー
# =========================
def store_home(request):
    return render(request, 'store/home.html')

def store_list(request):
    return render(request, 'store/list.html')

def store_mypage(request):
    return render(request, 'store/mypage.html')

def store_alert(request):
    return render(request, 'store/alert.html')

# =========================
# 商品登録フォーム
# =========================
def store_registar(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # 必要であれば店舗情報を紐付け
            # product.store = request.user.store
            product.save()
            return redirect('user_home')
        else:
            print(form.errors)  # エラー確認用
    else:
        form = ProductForm()

    return render(request, 'store/registar.html', {'form': form})

# =========================
# Ajax / JSON対応用の登録
# =========================
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        images = request.FILES.getlist("images")

        if len(images) > 5:
            return JsonResponse({"success": False, "error": "最大5枚までです"}, status=400)

        if form.is_valid():
            product = form.save(commit=False)
            # 必要であれば店舗情報を紐付け
            # product.store = request.user.store

            # 画像を順番に image1〜image5 にセット
            for idx, img in enumerate(images):
                if idx == 0:
                    product.image1 = img
                elif idx == 1:
                    product.image2 = img
                elif idx == 2:
                    product.image3 = img
                elif idx == 3:
                    product.image4 = img
                elif idx == 4:
                    product.image5 = img

            product.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    else:
        form = ProductForm()

    return render(request, "store/product_create.html", {"form": form})
