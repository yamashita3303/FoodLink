from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from .models import User, Store
from .forms import UserSignupStep1Form, UserSignupStep2Form, StoreSignupStep1Form, StoreSignupStep2Form, StoreSigninForm
import datetime

def top(request):
    if request.method == 'POST' and 'store' in request.POST:
        return redirect('store_signin')
    elif request.method == 'POST' and 'user' in request.POST:
        return redirect('user_signin')
    return render(request, 'top.html')

# user側のビュー
def user_signup(request):
    step = request.session.get('signup_step', 1)

    # =============================
    # ステップ1（基本情報）
    # =============================
    if step == 1:
        if request.method == "POST":
            form = UserSignupStep1Form(request.POST)
            if form.is_valid():
                # 入力データをセッションに保存
                request.session['signup_data'] = form.cleaned_data
                request.session['signup_step'] = 2
                return redirect('user_signup')
            else:
                print("フォームが無効です")
                print(form.errors)  # ←ここで何が原因か確認する
        else:
            print("form is not valid")
            # セッションから初期値をセット
            initial = request.session.get('signup_data', {})
            form = UserSignupStep1Form(initial=initial)

        return render(request, 'user/signup1.html', {'form': form, 'step': 1})


    # =============================
    # ステップ2（住所情報）
    # =============================
    elif step == 2:
        if request.method == "POST":
            if 'back' in request.POST:
                request.session['signup_step'] = 1
                return redirect('user_signup')

            form = UserSignupStep2Form(request.POST)
            if form.is_valid():
                request.session['signup_data2'] = form.cleaned_data
                request.session['signup_step'] = 3
                return redirect('user_signup')
        else:
            initial = request.session.get('signup_data2', {})
            form = UserSignupStep2Form(initial=initial)

        return render(request, 'user/signup2.html', {'form': form, 'step': 2})


    # =============================
    # ステップ3（確認画面）
    # =============================
    elif step == 3:
        signup_data = request.session.get('signup_data', {})
        signup_data2 = request.session.get('signup_data2', {})

        if request.method == "POST":
            if 'back' in request.POST:
                request.session['signup_step'] = 2
                return redirect('user_signup')
            elif 'confirm' in request.POST:
                # DB保存処理
                user = User(
                    username=signup_data['username'],
                    email=signup_data['email'],
                    phone=signup_data['phone'],
                    postal_code=signup_data.get('postal_code', ''),
                    prefecture=signup_data.get('prefecture', ''),
                    city=signup_data.get('city', ''),
                    address_line1=signup_data.get('address_line1', ''),
                    address_line2=signup_data.get('address_line2', ''),
                )
                # パスワードをハッシュ化して保存
                user.set_password(signup_data['password'])
                user.save()
                request.session.flush()  # セッションをクリア
                return redirect('user_home')

        return render(request, 'user/signup3.html', {
            'signup_data': signup_data,
            'signup_data2': signup_data2,
            'step': 3
        })
    
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

# @login_required
def user_home(request):
    return render(request, 'user/home.html')

def user_category(request):
    return render(request, 'user/category.html')

def user_cart(request):
    return render(request, 'user/cart.html')

def user_history(request):
    return render(request, 'user/history.html')


def user_mypage(request):
    if request.method == 'POST' and 'logout' in request.POST:
        logout(request)
        return redirect('top')
    return render(request, 'user/mypage.html')

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
                login(request, store)
                return redirect(next_url)
            else:
                print(phone, password)
                print(store)
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

def store_mypage(request):
    if request.method == 'POST' and 'logout' in request.POST:
        logout(request)
        return redirect('top')
    return render(request, 'store/mypage.html')

def store_alert(request):
    return render(request, 'store/alert.html')