from django.contrib.auth.backends import ModelBackend
from .models import User, Store
import logging

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info("EmailBackend.authenticate called: email=%s password_len=%s", email, len(password) if password else 0)
        if not email or not password:
            logger.info("EmailBackend: missing email or password")
            return None
        try:
            user = User.objects.get(email=email)
            logger.info("EmailBackend: found user id=%s", user.id)
        except User.DoesNotExist:
            logger.info("EmailBackend: no user")
            return None

        if user.check_password(password):
            logger.info("EmailBackend: password ok")
            return user
        else:
            logger.info("EmailBackend: password wrong")
            return None
        
class PhoneBackend(ModelBackend):
    """
    店舗用：電話番号でログインするバックエンド
    """
    def authenticate(self, request, phone=None, password=None, **kwargs):
        try:
            store = Store.objects.get(phone=phone)
        except Store.DoesNotExist:
            return None
        if store.check_password(password):
            return store
        return None

    def get_user(self, user_id):
        try:
            return Store.objects.get(pk=user_id)
        except Store.DoesNotExist:
            return None