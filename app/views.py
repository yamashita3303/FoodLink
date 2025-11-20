from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
import pytesseract
from .models import User, Store, Product
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
    if request.method == 'POST' and 'store' in request.POST:
        return redirect('store_signin')
    elif request.method == 'POST' and 'user' in request.POST:
        return redirect('user_signin')
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
        data1 = request.session.get('signup_data')
        data2 = request.session.get('signup_data2')

        if not data1 or not data2:
            return redirect('user_signup')

        # パスワードを取り出す
        password = data1.pop('password')

        # User を作成
        user = User.objects.create(
            username=data1['username'],
            email=data1['email'],
            phone=data1['phone'],
            postal_code=data2['postal_code'],
            prefecture=data2['prefecture'],
            city=data2['city'],
            address_line1=data2['address_line1'],
            address_line2=data2.get('address_line2'),
        )
        user.set_password(password)
        user.save()

        # セッション消す
        request.session.flush()

        # ログイン
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
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
def user_home(request):
    products = Product.objects.all()
    return render(request, 'user/home.html', {'products': products})

def user_category(request):
    return render(request, 'user/category.html')

def user_cart(request):
    return render(request, 'user/cart.html')

def user_history(request):
    return render(request, 'user/history.html')

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
    return render(request, 'user/alert.html')

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
                store = Store(
                    username=signup_data['username'],
                    phone=signup_data['phone'],
                    postal_code=signup_data2.get('postal_code', ''),
                    prefecture=signup_data2.get('prefecture', ''),
                    city=signup_data2.get('city', ''),
                    address_line1=signup_data2.get('address_line1', ''),
                    opening_time=opening_time,
                    closing_time=closing_time,
                )
                # パスワードハッシュ化
                store.set_password(signup_data['password'])
                store.save()

                # セッションをクリア
                request.session.flush()
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
        form = StoreSigninForm(request.POST)
        next_url = request.POST.get('next') or 'store_home'

        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']

            store = authenticate(request, phone=phone, password=password)
            if store is not None:
                login(request, store)  # ここで Django の認証は実行されるが request.user は User 型
                request.session['store_id'] = store.id  # ← store_id をセッションに保存
                return redirect(next_url)
            else:
                messages.error(request, '電話番号かパスワードが間違っています')
        else:
            messages.error(request, '電話番号とパスワードを入力してください')

        return render(request, 'store/signin.html', {'form': form, 'next': next_url})

    # GET の場合
    next_url = request.GET.get('next', '')
    form = StoreSigninForm()
    return render(request, 'store/signin.html', {'form': form, 'next': next_url})

def store_home(request):
    return render(request, 'store/home.html')

def store_list(request):
    return render(request, 'store/list.html')

@login_required(login_url='store_signin')
def store_mypage(request):
    store_id = request.session.get('store_id')
    if not store_id:
        return redirect('store_signin')  # セッションがなければ再ログイン

    store = Store.objects.get(id=store_id)  # DBから Store を取得

    if request.method == 'POST' and 'logout' in request.POST:
        logout(request)
        request.session.pop('store_id', None)  # セッションも削除
        return redirect('top')

    return render(request, 'store/mypage.html', {
        'store': store
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
def store_alert(request):
    return render(request, 'store/alert.html')

# =========================
# 商品登録フォーム
# =========================
def store_registar(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # request.user は Store インスタンス
            form.save(store=request.user)
            return redirect('user_home')
        else:
            print(form.errors)
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
            form.save(store=request.user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    else:
        form = ProductForm()

    return render(request, "store/product_create.html", {"form": form})

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
