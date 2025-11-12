from django.contrib.auth.backends import ModelBackend
from .models import User, Store

class EmailBackend(ModelBackend):
    """
    メールアドレスでログインできる認証バックエンド
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None

class PhoneBackend(ModelBackend):
    """
    店舗用：電話番号でログインするバックエンド
    """
    def authenticate(self, request, phone=None, password=None, **kwargs):
        if phone is None or password is None:
            return None
        try:
            store = Store.objects.get(phone=phone)
        except Store.DoesNotExist:
            return None
        if store.check_password(password):
            return store
        return None