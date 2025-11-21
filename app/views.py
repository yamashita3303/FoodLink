from django.shortcuts import render
from django.http import HttpResponse
from .models import  Product, Category,Store
from django.db.models import Q  # ← 検索に便利な「OR検索」= どちらかが一方が当てはまったらおk
from django.shortcuts import render, get_object_or_404 ,redirect

def top(request):
    return render(request, 'top.html')

# user側のビュー
def user_home(request):
    # ホームの既存処理（一覧表示など）
    products = Product.objects.all()[:9]  # 例：トップ表示用の少数
    return render(request, 'user/home.html', {'products': products})




def user_search(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.all()

    if query:
        keywords = query.split()  # スペースで区切る
        # 最初のキーワードで Q を作る
        q_objects = Q(name__icontains=keywords[0])
        # 2個目以降は & で追加
        for kw in keywords[1:]:
            q_objects &= Q(name__icontains=kw)
        products = products.filter(q_objects)

    categories = Category.objects.all()

    return render(request, 'user/search.html', {
        'products': products,
        'categories': categories,
        'query': query,
    })



def user_category_results(request, category_id):
    # 全カテゴリ（ヘッダ等で表示するため）
    categories = Category.objects.all()

    # 指定カテゴリを取得（無ければ 404）
    category = get_object_or_404(Category, id=category_id)

    # そのカテゴリの全商品（必要なら追加フィルタを適用）
    products = Product.objects.filter(category_id=category_id)

    context = {
        'categories': categories,
        'category': category,
        'products': products,
    }
    return render(request, 'user/category_results.html', context)


def user_food_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # 画像リストを作る
    images = [img for img in [product.image1, product.image2, product.image3, product.image4, product.image5] if img]

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})

        if str(product.pk) in cart:
            cart[str(product.pk)]['quantity'] += quantity
        else:
            cart[str(product.pk)] = {
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
            }

        request.session['cart'] = cart

        # GETパラメータでアラート表示用にフラグを送る
        return redirect(f"{request.path}?added=1")

    added = request.GET.get('added', '')
    context = {
        'product': product,
        'images': images,  # ここで images を渡す
        'added': added,
    }
    return render(request, 'user/user_food_detail.html', context)


def user_store_search(request):
    region = request.GET.get('region', '')
    prefecture = request.GET.get('prefecture', '')
    city = request.GET.get('city', '')

    stores = Store.objects.none()  # 初期は空
    mode = ""  # 表示モード

    # 都道府県＋市区が両方選ばれている場合のみ検索
    if prefecture and city:
        stores = Store.objects.filter(prefecture=prefecture, city=city)
        mode = "result"  # 結果表示用

    return render(request, "user/user_store_search.html", {
        "stores": stores,
        "selected_region": region,
        "selected_prefecture": prefecture,
        "selected_city": city,
        "mode": mode,
    })






def user_cart(request):
    cart = request.session.get('cart', {})

    if request.method == 'POST':
        for pk in cart.keys():
            key = f'quantity_{pk}'
            if key in request.POST:
                quantity = int(request.POST[key])
                cart[pk]['quantity'] = max(1, quantity)

        request.session['cart'] = cart
        return redirect('/cart/?updated=1')  # GETパラメータでフラグ

    total = 0
    for pk, item in cart.items():
        item['subtotal'] = item['price'] * item['quantity']
        total += item['subtotal']

    updated = request.GET.get('updated', '')
    return render(request, 'user/cart.html', {'cart': cart, 'total': total, 'updated': updated})

    cart = request.session.get('cart', {})

    if request.method == 'POST':
        # 各商品の数量を更新
        for pk in cart.keys():
            key = f'quantity_{pk}'
            if key in request.POST:
                quantity = int(request.POST[key])
                cart[pk]['quantity'] = max(1, quantity)  # 1以上に制限

        request.session['cart'] = cart
        return redirect('user_cart')  # 更新後リロード

    # GET時に小計と合計を計算
    total = 0
    for pk, item in cart.items():
        item['subtotal'] = item['price'] * item['quantity']
        total += item['subtotal']

    return render(request, 'user/cart.html', {'cart': cart, 'total': total})




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