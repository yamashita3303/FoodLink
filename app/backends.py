from django.contrib.auth.backends import ModelBackend
from .models import User
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
        