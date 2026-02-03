import hashlib
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q  # ← 検索に便利な「OR検索」= どちらかが一方が当てはまったらおk
from django.shortcuts import render, get_object_or_404 ,redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from .models import Notification
from django.contrib.auth.decorators import login_required
import pytesseract
import requests
from .models import (
    User, 
    Product, 
    Category, 
    Cart, 
    CartItem,
    Order, 
    OrderItem,
    Notification,
    Qr
)
from .forms import (
    UserSignupStep1Form, 
    UserSignupStep2Form, 
    UserEditUsernameForm, 
    UserEditEmailForm, 
    UserEditPasswordForm, 
    UserEditPhoneForm, 
    UserEditAddressForm, 
    StoreSignupStep1Form, 
    StoreSignupStep2Form, 
    StoreEditUsernameForm,
    StoreEditPhoneForm,
    StoreEditPasswordForm,
    StoreEditAddressForm,
    StoreEditHoursForm,
    StoreSigninForm,
    ProductForm
)
import datetime
from django.http import JsonResponse
from django.utils import timezone

now = timezone.now()

from django.shortcuts import redirect
from functools import wraps

def store_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('store_signin')
        if not request.user.is_store:
            return redirect('user_home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('user_signin')
        if request.user.is_store:
            return redirect('store_home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
 

# =========================
# トップページ
# =========================
def top(request):
    if request.method == 'POST':
        if 'store' in request.POST:
            return redirect('store_signup')
        elif 'user' in request.POST:
            return redirect('user_signup')
    return render(request, 'top.html')

# user側のビュー
def user_signup(request):
    step = request.session.get('signup_step', 1)

    # --------------------
    # Step 1
    # --------------------
    if step == 1:
        if request.method == "POST":
            form = UserSignupStep1Form(request.POST)
            if form.is_valid():
                request.session['signup_data'] = form.cleaned_data
                request.session['signup_step'] = 2
                return redirect('user_signup')
        else:
            initial = request.session.get('signup_data', {})
            form = UserSignupStep1Form(initial=initial)

        return render(request, 'user/signup1.html', {'form': form, 'step': 1})

    # --------------------
    # Step 2
    # --------------------
    elif step == 2:
        if request.method == "POST":

            # 戻るボタン
            if 'back' in request.POST:
                request.session['signup_step'] = 1
                return redirect('user_signup')

            # 住所フォーム
            form = UserSignupStep2Form(request.POST)
            if form.is_valid():
                request.session['signup_data2'] = form.cleaned_data
                request.session['signup_step'] = 3
                return redirect('user_signup')

        else:
            initial = request.session.get('signup_data2', {})
            form = UserSignupStep2Form(initial=initial)

        return render(request, 'user/signup2.html', {'form': form, 'step': 2})

    # --------------------
    # Step 3 → 登録処理
    # --------------------
    elif step == 3:
        signup_data = request.session.get('signup_data')
        signup_data2 = request.session.get('signup_data2')

        if not signup_data or not signup_data2:
            return redirect('user_signup')

        # パスワードを取り出す
        password = signup_data.pop('password')

        # User を作成
        user = User.objects.create(
            username=signup_data['username'],
            email=signup_data['email'],
            phone=signup_data['phone'],
            postal_code=signup_data2['postal_code'],
            prefecture=signup_data2['prefecture'],
            city=signup_data2['city'],
            address_line1=signup_data2['address_line1'],
            address_line2=signup_data2.get('address_line2'),
            is_store=False
        )
        user.set_password(password)
        user.save()

        # ログイン
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # セッションをクリア
        for key in ['signup_data', 'signup_data2', 'signup_step']:
            request.session.pop(key, None)

        return redirect('user_home')

        # return render(request, 'user/signup3.html', {
        #     'signup_data': signup_data,
        #     'signup_data2': signup_data2,
        #     'step': 3
        # })
    
def user_signin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or 'user_home'

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, 'メールアドレスかパスワードが間違っています')
            return render(request, 'user/signin.html')

        if user.is_store:
            messages.error(request, 'このアカウントは店舗用です')
            return render(request, 'user/signin.html')

        login(request, user)
        return redirect(next_url)

    return render(request, 'user/signin.html')
 
# @login_required
from django.db.models import Case, When, Value, IntegerField

from django.shortcuts import render
from django.utils import timezone
from .models import Product

from django.utils import timezone

def user_home(request):
    user = request.user
    now = timezone.now()

    # ▼ 期限切れでない商品だけ取得
    # ▼ 消費期限が近い順（昇順）に並べる
    products = (
        Product.objects
        .select_related('store')
        .filter(
            expiration_date__gte=now
        )
        .order_by('expiration_date')  # ← ★ここが変更点
    )
 
    MAX_PER_STORE = 10
    store_products = {}
 
    for product in products:
        store = product.store
 
        # ユーザーの市で絞る（市情報がある場合のみ）
        if getattr(user, 'city', None):
            if store.city != user.city:
                continue
 
        if store not in store_products:
            store_products[store] = []

        # ▼ 左から「期限が近い順」で最大10件
        if len(store_products[store]) < MAX_PER_STORE:
            store_products[store].append(product)
 
    # デバッグ出力
    print("==== USER HOME DEBUG ====")
    print("全商品数:", products.count())
    for p in products:
        print(
            p.name,
            "期限:", p.expiration_date,
            "今:", now,
            "期限OK:", p.expiration_date >= now,
            "在庫:", p.quantity
        )
 
    # 表示用に全店舗取得（市絞り込み済みのもの）
    stores = User.objects.filter(is_store=True)
 
    return render(request, 'user/home.html', {
        'store_products': store_products,
        'stores': stores,
    })
 
 
def user_search(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(
    expiration_date__gte=now,
    quantity__gt=0
)
 
 
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


def store_product_list(request, store_id):
    store = get_object_or_404(User, id=store_id, is_store=True)
    now = timezone.now()

    sort = request.GET.get('sort', 'expire')

    products = Product.objects.filter(
        store=store,
        expiration_date__gte=now,
        quantity__gt=0
    )

    if sort == 'price':
        # 値段が安い順 → 同価格なら期限が近い順
        products = products.order_by('price', 'expiration_date')
    else:
        # 消費期限が近い順 → 同期限なら安い順
        products = products.order_by('expiration_date', 'price')

    return render(request, 'user/store_product_list.html', {
        'store': store,
        'products': products,
        'sort': sort,
    })



def user_search(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(
    expiration_date__gte=now,
    quantity__gt=0
)


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
    categories = Category.objects.all()
    category = get_object_or_404(Category, id=category_id)

    products = Product.objects.filter(
    category=category,
    expiration_date__gte=now,
    quantity__gt=0
)


    context = {
        'categories': categories,
        'category': category,
        'products': products,
        'selected_category_id': category.id,
    }
    return render(request, 'user/search.html', context)




def user_food_detail(request, pk):
    product = get_object_or_404(
    Product,
    pk=pk,
    expiration_date__gte=date.today(),
    quantity__gt=0
)


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

    user_search = User.objects.none()
    mode = ""

    # 都道府県＋市区が選択されている場合のみ検索
    if prefecture and city:
        user_search = User.objects.filter(
            is_store=True,
            prefecture__icontains=prefecture,
            city__icontains=city
        )
        mode = "result"

    return render(request, "user/user_store_search.html", {
        "user_search": user_search,
        "selected_region": region,
        "selected_prefecture": prefecture,
        "selected_city": city,
        "mode": mode,
    })


from django.utils import timezone
from datetime import date


def user_store_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    today = date.today()

    # 新着順（作成日が新しい順）で、期限が切れていないもの
    new_products = Product.objects.filter(
        store=user,
        expiration_date__gte=now
    ).order_by('-created_at')

    # 期限が近い順（expiration_dateが近い順）で、期限が切れていないもの
    soon_expire_products = Product.objects.filter(
        store=user,
        expiration_date__gte=today
    ).order_by('expiration_date')

    # 残り日数を計算してテンプレートに渡す
    for product in new_products:
        product.days_remaining = (product.expiration_date - today).days

    for product in soon_expire_products:
        product.days_remaining = (product.expiration_date - today).days

    context = {
        'user': user,
        'new_products': new_products,
        'soon_expire_products': soon_expire_products,
    }
    return render(request, 'user/user_store_detail.html', context)



from django.utils import timezone
from datetime import date


def user_store_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    today = date.today()

    # 新着順（作成日が新しい順）で、期限が切れていないもの
    new_products = Product.objects.filter(
        store=user,
        expiration_date__gte=now
    ).order_by('-created_at')

    # 期限が近い順（expiration_dateが近い順）で、期限が切れていないもの
    soon_expire_products = Product.objects.filter(
        store=user,
        expiration_date__gte=now
    ).order_by('expiration_date')

    # 残り日数を計算してテンプレートに渡す
    for product in new_products:
        product.days_remaining = (product.expiration_date - today).days

    for product in soon_expire_products:
        product.days_remaining = (product.expiration_date - today).days

    context = {
        'user': user,
        'new_products': new_products,
        'soon_expire_products': soon_expire_products,
    }
    return render(request, 'user/user_store_detail.html', context)



# -------------------------
# カート画面（Session）
# -------------------------
from collections import defaultdict
@login_required
def user_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
 
    # 🔥 期限切れ商品を削除
    cart.items.filter(
        product__expiration_date__lt=timezone.now()
    ).delete()
 
    if request.method == "POST":
        action = request.POST.get("action")
 
        # =====================
        # 🛒 追加
        # =====================
        if action == "add":
            product_id = request.POST.get("product_id")
            quantity = int(request.POST.get("quantity", 1))
 
            product = get_object_or_404(Product, product_id=product_id)
 
            # 念のため期限切れ防止
            if product.is_expired:
                return redirect("user_cart")
 
            item, _ = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={"quantity": 0}
            )
 
            # 在庫を超えないように制限
            item.quantity = min(
                item.quantity + quantity,
                product.quantity
            )
            item.save()
 
            return redirect("user_cart")
 
        # =====================
        # 🔄 更新・削除
        # =====================
        elif action == "update":
            delete_id = request.POST.get("delete_item_id")
            if delete_id:
                CartItem.objects.filter(
                    cart=cart,
                    cart_item_id=delete_id
                ).delete()
                return redirect("user_cart")
 
            for item in cart.items.select_related("product"):
                key = f"quantity_{item.cart_item_id}"
                if key in request.POST:
                    requested = int(request.POST[key])
                    item.quantity = max(
                        1,
                        min(requested, item.product.quantity)
                    )
                    item.save()
 
            return redirect("user_cart")
 
    # =====================
    # 📦 表示用（店舗ごと）
    # =====================
    stores = defaultdict(list)
    for item in cart.items.select_related("product__store"):
        stores[item.product.store].append(item)
 
    store_blocks = []
    grand_total = 0
 
    for store, items in stores.items():
        total = sum(i.subtotal for i in items)
        grand_total += total
        store_blocks.append({
            "store": store,
            "items": items,
            "total": total,
        })
 
    return render(request, "user/cart.html", {
        "stores": store_blocks,
        "grand_total": grand_total,
    })

from django.views.decorators.http import require_POST
@login_required
@require_POST
def update_cart_quantity(request):
    item_id = request.POST.get("item_id")
    quantity = int(request.POST.get("quantity", 1))

    item = get_object_or_404(
        CartItem,
        cart__user=request.user,
        cart_item_id=item_id
    )

    # 在庫チェック
    quantity = max(1, min(quantity, item.product.quantity))
    item.quantity = quantity
    item.save()

    return JsonResponse({
        "subtotal": item.subtotal,
        "price": item.product.price,
    })
 
 
@login_required
def create_order_from_store(request):
    # GET で store_id を受け取る
    store_id = request.GET.get("store_id")
    if not store_id:
        return redirect("user_cart")
 
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.filter(product__store_id=store_id)
    if not items.exists():
        return redirect("user_cart")
 
    # Order 作成
    import datetime
    order_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + f"_{request.user.id}"
    order = Order.objects.create(
        order_id=order_id,
        user=request.user,
        store_id=store_id,
    )
 
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity
        )
        item.delete()
 
    order.update_total_price()
 
    # GMO EntryTran
    import requests
    from django.conf import settings
    payload = {
        "ShopID": settings.GMO_SHOP_ID,
        "ShopPass": settings.GMO_SHOP_PASS,
        "SiteID": settings.GMO_SITE_ID,
        "SitePass": settings.GMO_SITE_PASS,
        "OrderID": str(order.order_id),
        "JobCd": "CAPTURE",
        "Amount": str(int(order.total_price)),
    }
    response = requests.post("https://pt01.mul-pay.jp/payment/EntryTran.idPass", data=payload)
    result = dict(x.split("=") for x in response.text.split("&"))
 
    return render(request, "user/payment_page.html", {
        "order": order,
        "ShopID": settings.GMO_SHOP_ID,
        "AccessID": result['AccessID'],
        "AccessPass": result['AccessPass'],
        "OrderID": order.order_id,
        "JobCd": "CAPTURE",
        "Amount": int(order.total_price),
    })
 
 
 
# -------------------------
# カート → Order作成
# -------------------------
# @login_required
# def create_order_from_session(request):
#     cart = request.session.get('cart', {})
#     if not cart:
#         return redirect("user_cart")
 
#     # 店舗を最初の商品から取得
#     first_pk = next(iter(cart))
#     product = Product.objects.get(pk=first_pk)
#     store = product.store
 
#     # GMO用ユニークOrderID
#     order_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + f"_{request.user.id}"
 
#     # Order作成
#     order = Order.objects.create(
#         order_id=order_id,
#         user=request.user,
#         store=store,
#     )
 
#     # OrderItem作成
#     for pk, item in cart.items():
#         prod = Product.objects.get(pk=pk)
#         OrderItem.objects.create(
#             order=order,
#             product=prod,
#             quantity=item["quantity"]
#         )
 
#     # 合計計算
#     order.update_total_price()
 
#     # セッションカートクリア
#     request.session["cart"] = {}
 
#     return redirect("entry_tran", order_id=order.order_id)
 
 
# -------------------------
# EntryTran
# -------------------------
# @login_required
# def entry_tran(request, cart_item_id):
#     cart = get_object_or_404(CartItem, cart_item_id=cart_item_id)
 
#     payload = {
#         "ShopID": settings.GMO_SHOP_ID,
#         "ShopPass": settings.GMO_SHOP_PASS,
#         "SiteID": settings.GMO_SITE_ID,
#         "SitePass": settings.GMO_SITE_PASS,
#         "OrderID": str(cart.cart_item_id),
#         "JobCd": "CAPTURE",
#         "Amount": str(int(cart.total_price)),
#     }
 
#     response = requests.post("https://pt01.mul-pay.jp/payment/EntryTran.idPass", data=payload)
#     result = dict(x.split("=") for x in response.text.split("&"))
 
#     return redirect(
#         reverse("test_exec_tran", args=[cart.cart_item_id])
#         + f"?AccessID={result['AccessID']}&AccessPass={result['AccessPass']}"
#     )
 
# -------------------------
# テスト用 ExecTran
# -------------------------
from django.shortcuts import redirect
 
@login_required
def test_exec_tran(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
 
    if request.method == "POST":
        cardno = request.POST.get("CardNo")
        expire = request.POST.get("Expire")
        security = request.POST.get("SecurityCode")
        method = request.POST.get("Method")
        access_id = request.POST.get("AccessID")
        access_pass = request.POST.get("AccessPass")
 
        payload = {
            "ShopID": settings.GMO_SHOP_ID,
            "ShopPass": settings.GMO_SHOP_PASS,
            "AccessID": access_id,
            "AccessPass": access_pass,
            "OrderID": str(order.order_id),
            "JobCd": "CAPTURE",
            "Amount": str(int(order.total_price)),
            "Method": method,
            "CardNo": cardno,
            "Expire": expire,
            "SecurityCode": security,
        }
 
        response = requests.post(
            "https://pt01.mul-pay.jp/payment/ExecTran.idPass",
            data=payload
        )
        result = dict(x.split("=") for x in response.text.split("&"))
 
        approve = result.get("Approve")
        if approve:
            order.status = "pending"
            order.save()
 
            for item in order.items.all():
                product = item.product
                product.quantity -= item.quantity
                if product.quantity < 0:
                    product.quantity = 0
                product.save()
 
                Notification.objects.create(
                    type="order",
                    message=f"{product.name} が購入されました（数量: {item.quantity}）",
                    recipient_type="store",
                    store=order.store,
                    order=order,
                    product=product
                )
 
            # ✅ 決済完了後に home.html へ
            return redirect("user_home")
 
        else:
            order.status = "canceled"
            order.save()
            return redirect("user_cart")
 
    # GET → フォーム表示
    return render(request, "user/payment_page.html", {
        "order": order,
        "ShopID": settings.GMO_SHOP_ID,
        "AccessID": request.GET.get("AccessID"),
        "AccessPass": request.GET.get("AccessPass"),
        "OrderID": order.order_id,
        "JobCd": "CAPTURE",
        "Amount": int(order.total_price),
    })
 
 
 
    # GET → フォーム表示
    return render(request, "user/payment_page.html", {
        "order": order,
        "ShopID": settings.GMO_SHOP_ID,
        "AccessID": request.GET.get("AccessID"),
        "AccessPass": request.GET.get("AccessPass"),
        "OrderID": order.order_id,
        "JobCd": "CAPTURE",
        "Amount": int(order.total_price),
    })
 
 
 
 
# -------------------------
# 決済結果表示（本番用 RetURL 向け）
# -------------------------
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def payment_result(request):
    order_id = request.POST.get("OrderID")
    approve = request.POST.get("Approve")
    order = get_object_or_404(Order, order_id=order_id)
 
    if approve:
        order.status = "pending"
        order.ready = True
        message = "決済完了"
        print("決済成功")
        # --- 店舗に通知を作成 ---
        # send_store_notification(order)
        # for item in order.items.all():
        #         Notification.objects.create(
        #             type="order",
        #             message=f"{item.product.name} が購入されました（数量: {item.quantity}）",
        #             recipient_type="store",
        #             store=order.store,
        #             order=order,
        #             product=item.product
        #         )
    else:
        order.status = "canceled"
        message = "決済失敗"
 
    order.save()
 
    return render(request, "user/payment_result.html", {
        "order": order,
        "message": message,
        "result": request.POST,
    })

def payment_confirm(request, order_id):
    if request.method != "POST":
        return redirect("user_cart")

    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    context = {
        # 決済情報
        "CardNo": request.POST.get("CardNo"),
        "Expire": request.POST.get("Expire"),
        "SecurityCode": request.POST.get("SecurityCode"),
        "Method": request.POST.get("Method"),
        "AccessID": request.POST.get("AccessID"),
        "AccessPass": request.POST.get("AccessPass"),
        "OrderID": request.POST.get("OrderID"),

        # ★ここが追加
        "order": order,
        "order_items": order.items.all(),
    }

    return render(request, "user/payment_confirm.html", context)


@login_required
def user_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    print(orders)  # デバッグ用
    return render(request, 'user/history.html', {
        'orders': orders
    })


@login_required
def user_cancel_list(request):
    tab = request.GET.get("tab", "new")

    # 🟥 お客様キャンセル（自分でキャンセルした商品）
    user_cancelled_products = OrderItem.objects.filter(
        order__user=request.user,
        is_canceled=True,
    ).select_related("product", "order").order_by("-order__created_at")

    # 🟨 消費期限切れ自動キャンセル
    expired_products = OrderItem.objects.filter(
        order__user=request.user,
        product__expiration_date__lt=timezone.now(),
        is_canceled=False,
    ).select_related("product", "order").order_by("-product__expiration_date")

    return render(request, "user/cancel_list.html", {
        "tab": tab,
        "user_cancelled_products": user_cancelled_products,
        "expired_products": expired_products,
    })


@login_required
def order_item_cancel(request, order_item_id):
    item = get_object_or_404(OrderItem, order_item_id=order_item_id)
    order = item.order

    if order.user != request.user:
        messages.error(request, "権限がありません")
        return redirect("user_history")

    if order.status == "pending":
        item.is_canceled = True
        item.save()

        order.update_total_price()
        order.status = "canceled"
        order.save()
        
        product = item.product
        Notification.objects.create(
            recipient_type="store",
            store=order.store,
            order=order,
            product=product,
            type="user_cancel",
            message=f"購入者キャンセルしました。商品「{product.name}」を自己回収してください。"
        )

        messages.success(request, "商品をキャンセルしました")
    else:
        messages.error(request, "この注文はキャンセルできません")

    return redirect("user_history")


@login_required(login_url='user_signin')
def user_mypage(request):
    user = request.user  # ログイン中のユーザーを取得
    print(user)
    if request.method == 'POST' and 'logout' in request.POST:
        logout(request)
        return redirect('top')
    return render(request, 'user/mypage.html',{
        'user': user
    })

@login_required(login_url='user_signin')
def user_edit_menu(request):
    # 単に編集メニューを表示する
    return render(request, 'user/mypage_edit_menu.html')

@login_required(login_url='user_signin')
def user_edit_username(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditUsernameForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'ユーザネームを更新しました。')
            return redirect('user_mypage')
    else:
        form = UserEditUsernameForm()
    return render(request, 'user/mypage_edit_form.html', {
        'form': form,
        'title': 'ユーザネームを変更',
        'current_value': user.username
    })

@login_required(login_url='user_signin')
def user_edit_email(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditEmailForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'メールアドレスを更新しました。')
            return redirect('user_mypage')
    else:
        form = UserEditEmailForm()
    return render(request, 'user/mypage_edit_form.html', {
        'form': form,
        'title': 'メールアドレスを変更',
        'current_value': user.email
    })

@login_required(login_url='user_signin')
def user_edit_password(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditPasswordForm(user, request.POST)
        print(form)
        print("-----")
        print(form.errors)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, user)  # ログイン状態維持
            messages.success(request, 'パスワードを更新しました。')
            return redirect('user_mypage')
    else:
        form = UserEditPasswordForm(user)
    return render(request, 'user/mypage_edit_form.html', {
        'form': form,
        'title': 'パスワードを変更',
        'current_value': '●●●●●●'
    })

@login_required(login_url='user_signin')
def user_edit_phone(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditPhoneForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '電話番号を更新しました。')
            return redirect('user_mypage')
    else:
        form = UserEditPhoneForm()
    return render(request, 'user/mypage_edit_form.html', {
        'form': form,
        'title': '電話番号を変更',
        'current_value': user.phone
    })

@login_required(login_url='user_signin')
def user_edit_address(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditAddressForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '住所を更新しました。')
            return redirect('user_mypage')
    else:
        form = UserEditAddressForm()
    return render(request, 'user/mypage_edit_form.html', {
        'form': form,
        'title': '住所を変更',
        'current_value': f"{user.postal_code} {user.prefecture} {user.city} {user.address_line1} {user.address_line2}"
    })

def user_alert(request):
    notifications = Notification.objects.filter(
        recipient_type="user",
        user=request.user
    ).order_by('-created_at')

    notifications.filter(is_read=False).update(is_read=True)

    return render(request, "user/alert.html", {
        "notifications": notifications
    })

def user_read_qr_code(request, notification_id):
    notification = get_object_or_404(
        Notification,
        notification_id=notification_id,
        user=request.user
    )
    return render(request, "user/read_qr_code.html", {
            "notification": notification
        })


def user_qr_result(request, notification_id):
    notification = get_object_or_404(
        Notification,
        notification_id=notification_id,
        user=request.user
    )
    code_type = request.GET.get("type")
    code_data = request.GET.get("data")
    qr = get_object_or_404(
        Qr,
        code_data=code_data
    )
 
    # 通知に紐づく注文を取得
    order = notification.order
    if not order:
        messages.error(request, "注文情報が見つかりません")
        return redirect("user_home")
 
    # すでに完了している場合
    if order.status == "completed":
        messages.info(request, "この注文はすでに完了しています")
        return redirect("user_home")
 
    # 注文を完了にする
    order.status = "completed"
    order.save(update_fields=["status"])

    # 🔽 POST（受け取り完了）
    if request.method == "POST":
        code_data = request.GET.get("data")

        if not code_data:
            return render(request, "user/qr_error.html", {
                "message": "QR情報が不正です"
            })

        try:
            code_data = int(code_data)
        except ValueError:
            return render(request, "user/qr_error.html", {
                "message": "QRデータ形式が不正です"
            })

        qr = Qr.objects.filter(code_data=code_data).first()

        if not qr:
            return render(request, "user/qr_error.html", {
                "message": "このQRコードは無効です"
            })

        # ✅ 受け取り完了処理（例）
        qr.is_received = True
        qr.save()

        # ✅ ホーム画面へ戻る
        return redirect("user_home")  # ← 自分のホームURL名に合わせて

    # 🔽 GET（表示用）
    code_data = request.GET.get("data")

    if not code_data:
        return render(request, "user/qr_error.html", {
            "message": "QR情報が不正です"
        })

    try:
        code_data = int(code_data)
    except ValueError:
        return render(request, "user/qr_error.html", {
            "message": "QRデータ形式が不正です"
        })

    qr = Qr.objects.filter(code_data=code_data).first()

    if not qr:
        return render(request, "user/qr_error.html", {
            "message": "このQRコードは無効です"
        })

    return render(request, "user/qr_result.html", {
        "qr": qr,
    })





# store側のビュー
# =============================
# ヘルパー関数
# =============================
def serialize_form_data(cleaned_data):
    """
    cleaned_data内のtime型を文字列に変換して返す
    """
    result = cleaned_data.copy()
    for key, value in result.items():
        if isinstance(value, datetime.time):
            result[key] = value.strftime("%H:%M")
    return result


# =============================
# サインアップビュー
# =============================
def store_signup(request):
    step = request.session.get('signup_step', 1)

    # =============================
    # ステップ1（基本情報）
    # =============================
    if step == 1:
        if request.method == "POST":
            form = StoreSignupStep1Form(request.POST)
            if form.is_valid():
                # time型を文字列に変換してセッションに保存
                request.session['signup_data'] = serialize_form_data(form.cleaned_data)
                request.session['signup_step'] = 2
                return redirect('store_signup')
            else:
                print("フォームが無効です")
                print(form.errors)
        else:
            initial = request.session.get('signup_data', {})
            form = StoreSignupStep1Form(initial=initial)

        return render(request, 'store/signup1.html', {'form': form, 'step': 1})

    # =============================
    # ステップ2（住所情報）
    # =============================
    elif step == 2:
        if request.method == "POST":
            if 'back' in request.POST:
                request.session['signup_step'] = 1
                return redirect('store_signup')

            form = StoreSignupStep2Form(request.POST)
            if form.is_valid():
                # time型を文字列に変換してセッションに保存
                request.session['signup_data2'] = serialize_form_data(form.cleaned_data)
                request.session['signup_step'] = 3
                return redirect('store_signup')
        else:
            initial = request.session.get('signup_data2', {})
            form = StoreSignupStep2Form(initial=initial)

        return render(request, 'store/signup2.html', {'form': form, 'step': 2})

    # =============================
    # ステップ3（確認画面）
    # =============================
    elif step == 3:
        signup_data = request.session.get('signup_data', {})
        signup_data2 = request.session.get('signup_data2', {})

        if request.method == "POST":
            if 'back' in request.POST:
                request.session['signup_step'] = 2
                return redirect('store_signup')
            elif 'confirm' in request.POST:
                # 文字列 → time型 に戻して DB 保存
                opening_time = datetime.datetime.strptime(
                    signup_data.get('opening_time', '09:00'), "%H:%M"
                ).time()
                closing_time = datetime.datetime.strptime(
                    signup_data.get('closing_time', '18:00'), "%H:%M"
                ).time()

                # DB 保存
                store = User(
                    username=signup_data['username'],
                    email=signup_data['email'],
                    phone=signup_data['phone'],
                    postal_code=signup_data2.get('postal_code', ''),
                    prefecture=signup_data2.get('prefecture', ''),
                    city=signup_data2.get('city', ''),
                    address_line1=signup_data2.get('address_line1', ''),
                    opening_time=opening_time,
                    closing_time=closing_time,
                    is_store=True
                )
                # パスワードハッシュ化
                store.set_password(signup_data['password'])
                store.save()

                login(request, store, backend='django.contrib.auth.backends.ModelBackend')

                # セッションをクリア
                for key in ['signup_data', 'signup_data2', 'signup_step']:
                    request.session.pop(key, None)

                return redirect('store_qr_generate')

        return render(request, 'store/signup3.html', {
            'signup_data': signup_data,
            'signup_data2': signup_data2,
            'step': 3
        })


# =============================
# サインインビュー
# =============================
def store_signin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or 'store_home'

        store = authenticate(request, email=email, password=password)

        if store is None:
            messages.error(request, 'メールアドレスかパスワードが間違っています')
            return render(request, 'store/signin.html')

        if not store.is_store:
            messages.error(request, 'このアカウントは一般ユーザー用です')
            return render(request, 'store/signin.html')

        login(request, store)
        return redirect(next_url)

    return render(request, 'store/signin.html')
 

@login_required(login_url='store_signin')
def store_home(request):
    # 1. ログイン中のユーザー（店舗アカウント）を取得
    store = request.user
   
    # 2. その店舗が登録した商品のみをデータベースから取得
    #    新しいもの順に並べ替えることが多いです
    products = Product.objects.filter(store=store.id).order_by('-created_at')
   
    # 3. テンプレートにデータを渡す
    context = {
        'store': store,    # 店舗情報（ヘッダーなどに使う可能性）
        'products': products # 登録商品の一覧
    }
   
    return render(request, 'store/home.html', context)

@login_required(login_url='store_signin')
def store_list(request):
    products = Product.objects.all()
    return render(request, 'store/list.html', {'products': products})

@login_required(login_url='store_signin')
def store_mypage(request):
    user = request.user  # ログイン中のユーザーを取得
    print(user)
    if request.method == 'POST' and 'logout' in request.POST:
        logout(request)
        return redirect('top')
    return render(request, 'store/mypage.html',{
        'store': user
    })

@login_required(login_url='store_signin')
def store_edit_menu(request):
    return render(request, 'store/mypage_edit_menu.html')

# ===== 個別編集ビュー =====
@login_required(login_url='store_signin')
def store_edit_username(request):
    store = request.user
    if request.method == 'POST':
        form = StoreEditUsernameForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, '店舗名を更新しました。')
            return redirect('store_mypage')
    else:
        form = StoreEditUsernameForm()
    return render(request, 'store/mypage_edit_form.html', {
        'form': form,
        'title': '店舗名を変更',
        'current_value': store.username
    })

@login_required(login_url='store_signin')
def store_edit_phone(request):
    store = request.user
    if request.method == 'POST':
        form = StoreEditPhoneForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, '電話番号を更新しました。')
            return redirect('store_mypage')
    else:
        form = StoreEditPhoneForm()
    return render(request, 'store/mypage_edit_form.html', {
        'form': form,
        'title': '電話番号を変更',
        'current_value': store.phone or ''
    })

@login_required(login_url='store_signin')
def store_edit_password(request):
    store = request.user
    if request.method == 'POST':
        form = StoreEditPasswordForm(store, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, store)
            messages.success(request, 'パスワードを更新しました。')
            return redirect('store_mypage')
    else:
        form = StoreEditPasswordForm(store)
    return render(request, 'store/mypage_edit_form.html', {
        'form': form,
        'title': 'パスワードを変更',
        'current_value': '●●●●●●'
    })

@login_required(login_url='store_signin')
def store_edit_address(request):
    store = request.user
    if request.method == 'POST':
        form = StoreEditAddressForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, '住所を更新しました。')
            return redirect('store_mypage')
    else:
        form = StoreEditAddressForm()
    return render(request, 'store/mypage_edit_form.html', {
        'form': form,
        'title': '住所を変更',
        'current_value': f"{store.postal_code} {store.prefecture} {store.city} {store.address_line1}"
    })
@login_required(login_url='store_signin')
def store_edit_hours(request):
    store = request.user

    if request.method == 'POST':
        form = StoreEditHoursForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, '営業時間を更新しました。')
            return redirect('store_mypage')
    else:
        form = StoreEditHoursForm(instance=store)

    current_value = None
    if store.opening_time and store.closing_time:
        current_value = (
            f"{store.opening_time.strftime('%H:%M')} "
            f"〜 "
            f"{store.closing_time.strftime('%H:%M')}"
        )

    return render(request, 'store/mypage_edit_form.html', {
        'form': form,
        'title': '営業時間を変更',
        'current_value': current_value
    })


@login_required
def store_purchased_list(request):

    # ✅ 購入済み通知（購入された商品）
    notifications = Notification.objects.filter(
        store=request.user,
        recipient_type="store",
        type="order",
        product__isnull=False,
        order__isnull=False,
    ).select_related(
        "product", "order"
    ).order_by("-created_at")

    notifications.filter(is_read=False).update(is_read=True)

    return render(request, "store/store_purchased_list.html", {
        "notifications": notifications,
    })



@login_required(login_url='store_signin')
def store_alert(request):
    tab = request.GET.get("tab", "new")

    # ❌ お客様キャンセル
    user_cancelled_products = Notification.objects.filter(
        recipient_type="store",
        store=request.user,
        type="user_cancel",
    ).select_related(
        "product", "order"
    ).order_by("-created_at")

    # ⏰ 期限切れ関連（自動キャンセル＋在庫期限切れ）
    expired_products = Notification.objects.filter(
        recipient_type="store",
        store=request.user,
        type__in=["auto_cancel", "expiration_date"],
    ).select_related(
        "product", "order"
    ).order_by("-created_at")

    # ✅ 表示されたタブのみ既読
    if tab == "user_cancel":
        user_cancelled_products.filter(is_read=False).update(is_read=True)
    elif tab == "expired_cancel":
        expired_products.filter(is_read=False).update(is_read=True)

    return render(request, "store/alert.html", {
        "tab": tab,
        "user_cancelled_products": user_cancelled_products,
        "expired_products": expired_products,
    })

@login_required(login_url='store_signin')
def store_registar(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        images = request.FILES.getlist("images")  # HTMLのmultiple inputから取得
 
        # 画像を image1～5 に順番にセット
        for i in range(min(5, len(images))):
            setattr(form.instance, f'image{i+1}', images[i])
 
        if form.is_valid():
            product = form.save(commit=False)
            product.store = request.user
            product.save()
            print("フォーム成功:", product)
            return JsonResponse({"success": True})
        else:
            # ここでフォームエラーを確認
            print("フォームエラー:", form.errors)
            print("POSTデータ:", request.POST)
            print("FILESデータ:", request.FILES)
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = ProductForm()
 
    return render(request, "store/registar.html", {"form": form})

from PIL import Image
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Product

def product_ocr(request, product_id):
    # 商品データ取得
    product = get_object_or_404(Product, pk=product_id)

    # # 画像がない場合
    # if not product.image:
    #     return HttpResponse("画像がありません")

    # # 実際のファイルパス
    # image_path = product.image.path

    images = [product.image1, product.image2, product.image3, product.image4, product.image5]

    for img in images:
        if img:
            img_path = img.path

    # OCR 実行
    img = Image.open(img_path)
    extracted_text = pytesseract.image_to_string(img, lang="jpn")  # ★日本語OCR

    print("=== OCR結果 ===")
    print(extracted_text)

    return HttpResponse("OCR 完了！コンソールを確認してください")

def store_read_qr_code(request, notification_id):
    notification = get_object_or_404(
        Notification,
        notification_id=notification_id,
        store=request.user
    )
    return render(request, "store/read_qr_code.html", {
            "notification": notification
        })

def store_qr_result(request, notification_id):
    notification = get_object_or_404(
        Notification,
        notification_id=notification_id,
        store=request.user
    )
    code_type = request.GET.get("type")
    code_data = request.GET.get("data")

    return render(request, "store/qr_result.html", {
        "code_type": code_type,
        "code_data": code_data,
        "notification": notification
    })


def store_qr_verify(request, notification_id):
    notification = get_object_or_404(
        Notification,
        notification_id=notification_id,
        store=request.user
    )

    if request.method != "POST":
        return redirect("store_qr_read")

    code_type = request.POST.get("code_type")
    code_data = request.POST.get("code_data")
    pin = request.POST.get("pin")

    if not pin or not pin.isdigit():
        messages.error(request, "暗証番号は数字で入力してください")
        return redirect(
            f"/qr/result/?type={code_type}&data={code_data}"
        )

    # QR保存
    Qr.objects.create(
        code_data=code_data,
        pin=int(pin)
    )

    # ✅ ここが超重要！！！！！！
    order = notification.order
    order.ready = True
    order.save(update_fields=["ready"])
    order.status = 'completed'
    order.save()

    # ユーザーに準備完了通知
    Notification.objects.create(
        type="ready",
        message=(
            f"ご注文の「{notification.product.name}」の準備が完了しました。\n"
            f"受け取りロッカー番号：{code_data}"
        ),
        recipient_type="user",
        user=order.user,
        store=notification.store,
        product=notification.product,
        order=order,
    )

    messages.success(request, "準備完了にしました")
    return redirect("store_alert")


import qrcode
import io
import base64
def store_qr_generate(request):
    qr_list = []

    if request.method == "POST":
        start = request.POST.get("start_locker")
        end = request.POST.get("end_locker")

        if start and end and start.isdigit() and end.isdigit():
            start = int(start)
            end = int(end)

            if start <= end:
                for number in range(start, end + 1):
                    qr = qrcode.make(str(number))

                    buffer = io.BytesIO()
                    qr.save(buffer, format="PNG")
                    image_base64 = base64.b64encode(buffer.getvalue()).decode()

                    qr_list.append({
                        "locker": number,
                        "image": f"data:image/png;base64,{image_base64}"
                    })

    return render(request, "store/qr_generate.html", {
        "qr_list": qr_list
    })

@login_required(login_url='store_signin')
def product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)


    # 自分の店舗の商品以外は編集不可
    if product.store != request.user:
        return HttpResponse("権限がありません", status=403)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        images = request.FILES.getlist("images")

        # 画像上書き（最大5枚）
        for i in range(min(5, len(images))):
            setattr(product, f'image{i+1}', images[i])

        if form.is_valid():
            form.save()
            return redirect('store_home')
    else:
        form = ProductForm(instance=product)

    return render(request, "store/product_edit.html", {
        "form": form,
        "product": product,
        "id": product_id
    })

def product_delete(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)

    if request.method == "POST":
        product.delete()
        return redirect('store_home')  # 一覧に戻す

    return redirect('store_list')

def store_qr_confirm(request, notification_id):
    if request.method != "POST":
        return redirect("store_home")

    notification = get_object_or_404(Notification, pk=notification_id)

    pin = request.POST.get("pin")
    code_type = request.POST.get("code_type")
    code_data = request.POST.get("code_data")

    return render(request, "store/qr_confirm.html", {
        "notification": notification,
        "pin": pin,
        "code_type": code_type,
        "code_data": code_data,
    })

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.utils import timezone
from datetime import timedelta
from .models import OrderItem

@login_required(login_url='store_signin')
def store_sales(request):
    store = request.user

    # 表示する日を判定
    day_type = request.GET.get('day', 'today')

    if day_type == 'yesterday':
        target_date = timezone.localdate() - timedelta(days=1)
        label = '前日の売上'
    else:
        target_date = timezone.localdate()
        label = '今日の売上'

    start = timezone.make_aware(
        timezone.datetime.combine(target_date, timezone.datetime.min.time())
    )
    end = start + timedelta(days=1)

    sales_items = OrderItem.objects.filter(
        order__store=store,
        order__status='completed',
        is_canceled=False,
        order__created_at__range=(start, end)
    ).annotate(
        net_sales=ExpressionWrapper(
            F('subtotal') * 0.9,
            output_field=DecimalField()
        )
    )

    total_gross = sales_items.aggregate(
        total=Sum('subtotal')
    )['total'] or 0

    total_net = sales_items.aggregate(
        total=Sum('net_sales')
    )['total'] or 0

    return render(request, 'store/sales.html', {
        'sales_items': sales_items,
        'total_gross': total_gross,
        'total_net': total_net,
        'target_date': target_date,
        'label': label,
        'day_type': day_type,
    })

