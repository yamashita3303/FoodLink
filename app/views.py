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
    Notification
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

        if not email or not password:
            messages.error(request, 'メールアドレスとパスワードを入力してください')
            return render(request, 'user/signin.html', {'next': next_url})

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, 'メールアドレスかパスワードが間違っています')
            return render(request, 'user/signin.html', {'next': next_url})

    # GET の場合
    next_url = request.GET.get('next', '')
    return render(request, 'user/signin.html', {'next': next_url})

def store_alert(request):
    return render(request, 'store/alert.html')

# @login_required
from django.db.models import Case, When, Value, IntegerField

def user_home(request):
    user = request.user

    products = (
        Product.objects
        .select_related('store')
        .order_by('-created_at')
    )

    store_products = {}
    MAX_PER_STORE = 10

    for product in products:
        store = product.store

        # ▼ 同じ市の店舗だけ通す
        if user.is_authenticated and user.city:
            if store.city != user.city:
                continue

        if store not in store_products:
            store_products[store] = []

        if len(store_products[store]) < MAX_PER_STORE:
            store_products[store].append(product)

    return render(request, 'user/home.html', {
        'store_products': store_products
    })






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
    categories = Category.objects.all()
    category = get_object_or_404(Category, id=category_id)

    products = Product.objects.filter(category=category)  # ← 修正ポイント

    context = {
        'categories': categories,
        'category': category,
        'products': products,
        'selected_category_id': category.id,
    }
    return render(request, 'user/search.html', context)




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
        expiration_date__gte=today
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
        expiration_date__gte=today
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



# -------------------------
# カート画面（Session）
# -------------------------
# @login_required
# def user_cart(request):
#     cart = request.session.get('cart', {})

#     if request.method == 'POST':
#         for pk, item in cart.items():
#             key = f'quantity_{pk}'
#             if key in request.POST:
#                 cart[pk]["quantity"] = max(1, int(request.POST[key]))
#         request.session["cart"] = cart
#         return redirect("user_cart")

#     total = sum(item["price"] * item["quantity"] for item in cart.values())
#     for pk, item in cart.items():
#         item["subtotal"] = item["price"] * item["quantity"]

#     return render(request, "user/cart.html", {
#         "cart": cart,
#         "total": total,
#     })
from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from collections import defaultdict

@login_required
def user_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # POST処理
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add":
            product_id = request.POST.get("product_id")
            quantity = int(request.POST.get("quantity", 1))
            if product_id:
                product = get_object_or_404(Product, product_id=product_id)
                item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={"quantity": quantity}
                )
                if not created:
                    item.quantity += 1
                    item.save()
        elif action == "update":
            for item in cart.items.all():
                key = f"quantity_{item.cart_item_id}"
                if key in request.POST:
                    item.quantity = max(1, int(request.POST[key]))
                    item.save()
        return redirect("user_cart")

    # GET処理：店舗ごとにグルーピング
    stores = defaultdict(list)
    # select_relatedでProductとUser（store）をまとめて取得
    for item in cart.items.select_related("product__store"):
        stores[item.product.store].append(item)

    store_blocks = []
    grand_total = 0
    for store, items in stores.items():
        total = sum(item.subtotal for item in items)
        grand_total += total
        store_blocks.append({
            "store": store,   # store は User オブジェクト
            "items": items,
            "total": total,
        })

    return render(request, "user/cart.html", {
        "stores": store_blocks,
        "grand_total": grand_total,
    })


    # =========================
    # 店舗ごとにグルーピング
    # =========================
    stores = defaultdict(list)

    for item in cart.items.select_related("product__store"):
        stores[item.product.store].append(item)

    store_blocks = []
    grand_total = 0

    for store, items in stores.items():
        total = sum(item.subtotal for item in items)
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
        for item in order.items.all():
                Notification.objects.create(
                    type="order",
                    message=f"{item.product.name} が購入されました（数量: {item.quantity}）",
                    recipient_type="store",
                    store=order.store,
                    order=order,
                    product=item.product
                )
    else:
        order.status = "canceled"
        message = "決済失敗"

    order.save()

    return render(request, "user/payment_result.html", {
        "order": order,
        "message": message,
        "result": request.POST,
    })

@login_required
def user_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    print(orders)  # デバッグ用
    return render(request, 'user/history.html', {
        'orders': orders
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

    return render(request, "user/alert.html", {
        "notifications": notifications
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

                return redirect('store_home')

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

        if not email or not password:
            messages.error(request, 'メールアドレスとパスワードを入力してください')
            return render(request, 'store/signin.html', {'next': next_url})

        store = authenticate(request, email=email, password=password)
        if store is not None:
            login(request, store)
            return redirect(next_url)
        else:
            messages.error(request, 'メールアドレスかパスワードが間違っています')
            return render(request, 'store/signin.html', {'next': next_url})

    # GET の場合
    next_url = request.GET.get('next', '')
    return render(request, 'store/signin.html', {'next': next_url})


    # GET の場合
    next_url = request.GET.get('next', '')
    form = StoreSigninForm()
    return render(request, 'store/signin.html', {'form': form, 'next': next_url})

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
        form = StoreEditHoursForm()
    return render(request, 'store/mypage_edit_form.html', {
        'form': form,
        'title': '営業時間を変更',
        'current_value': f"{store.opening_time} - {store.closing_time}"
    })

from .models import Notification, Product

from django.contrib.auth.decorators import login_required
from .models import Product, OrderItem
@login_required(login_url='store_signin')
@login_required(login_url='store_signin')
def store_alert(request):
    tab = request.GET.get('tab', 'new')

    # 🆕 新着商品（在庫あり）
    products = Product.objects.filter(
        store=request.user,
        quantity__gt=0
    ).order_by('-created_at')

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


    return render(request, "store/alert.html", {
        "products": products,
        "notifications": notifications,
        "tab": tab,
    })




@login_required(login_url='store_signin')
def prepare_product(request, notification_id):
    notification = get_object_or_404(
        Notification,
        notification_id=notification_id,
        store=request.user
    )

    if request.method == "POST":
        locker = request.POST.get("locker")
        pin = request.POST.get("pin")

        # 📨 購入者へ「準備完了」通知
        Notification.objects.create(
            type="ready",
            message=(
                f"ご注文の「{notification.product.name}」の準備が完了しました。\n"
                f"受け取りロッカー番号：{locker}\n"
                f"暗証番号：{pin}\n"
                f"ご来店の上、お受け取りください。"
            ),
            recipient_type="user",
            user=notification.order.user,
            store=notification.store,
            product=notification.product,
            order=notification.order,
        )

        # ✅ 店舗側の購入通知を既読（＝対応済み）
        notification.read = True
        notification.save()

        # ---- 購入者へメール送信 ----
        # EmailMessage のインスタンスを作成する
        # emailMessage = EmailMessage(
        #     subject='【FoodLink】商品の準備が完了しました',
        #     body=(
        #         f"ご注文の「{notification.product}」の準備が完了しました。\n"
        #         f"受け取りロッカー番号：{locker}\n"
        #         f"暗証番号：{pin}\n"
        #         f"ご来店の上、お受け取りください。"
        #     ),
        #     from_email='FoodLink <noreply@example.com>',  # ← ここで Gmail アドレスを隠す
        #     to=[notification.order.user.email],
        # )
        # # send 関数を呼び出してメールを送信する
        # emailMessage.send()

        return redirect("store_alert")

    return render(request, "store/prepare_form.html", {
        "notification": notification
    })



@login_required(login_url='store_signin')
def store_registar(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        images = request.FILES.getlist("images")  # HTMLのmultiple inputから取得

        if form.is_valid():
            product = form.save(commit=False)
            product.store = request.user

            # images を image1～5 に順番にセット
            for i in range(min(5, len(images))):
                setattr(product, f'image{i+1}', images[i])

            product.save()
            return JsonResponse({"success": True})
        else:
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
