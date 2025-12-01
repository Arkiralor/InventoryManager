from datetime import datetime, timedelta
from secrets import choice, token_hex
from pytz import timezone
from uuid import uuid4

from django.conf import settings as django_settings
from django.contrib.auth.hashers import make_password, check_password

from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.models import User


from auth_app import logger


class JWTUtils:
    """
    Utilities for basic operation on JWT.
    """
    @classmethod
    def get_tokens_for_user(cls, user: User = None):
        if not user:
            logger.warning(f'Invalid argument(s) NULL `user` passed.')
            return None
        if not isinstance(user, User):
            logger.warning(f'Invalid argument(s) `user` passed.')
            return None
        
        if not user in User.objects.all():
            logger.warning(f'Invalid argument(s) `user` does not exist.')
            return None
        refresh = RefreshToken.for_user(user)

        return {
            'refreshToken': str(refresh),
            'accessToken': str(refresh.access_token),
        }