from core.boilerplate.response_template import Resp
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings as django_settings
from django.utils import timezone

from auth_app.models import User, UserProfile, UserOauth2Credential
from auth_app.constants import FormatRegex
from auth_app.serializers import UserSerializer, UserProfileOutputSerializer, UserProfileInputSerializer, UserRegisterSerializer
from auth_app.utils import JWTUtils

from django.db.models import Q, QuerySet

from auth_app import logger


class UserModelHelpers:

    @classmethod
    def get(cls, username: str = None, email: str = None, return_obj: bool = False) -> Resp:
        """
        Get a user by username or email.
        """
        query = Q()
        resp = Resp()

        if username:
            query = Q(username__iexact=username.strip().lower())
        elif email:
            query = Q(email__iexact=email.strip().lower())
        elif username and email:
            resp.error = "Invalid Parameters"
            resp.message = "Provide either username or email, not both."
            resp.status_code = status.HTTP_400_BAD_REQUEST
            logger.error(resp.to_text())
            return resp
        else:
            resp.error = "No Parameters"
            resp.message = "No username or email provided to 'get user'."
            resp.status_code = status.HTTP_400_BAD_REQUEST
            logger.error(resp.to_text())
            return resp

        user = User.objects.filter(query).first()
        if not user:
            resp.error = "User Not Found."
            resp.message = "No user found with the given credentials."
            resp.status_code = status.HTTP_404_NOT_FOUND
            logger.warning(resp.to_text())
            return resp

        resp.message = f"User {user.email} retrieved successfully."
        resp.data = user if return_obj else UserSerializer(user).data
        resp.status_code = status.HTTP_200_OK
        logger.info(resp.to_text())
        return resp

    @classmethod
    def check_if_user_exists(cls, username: str = None, email: str = None) -> bool:
        """
        Check if a user exists with the given username or email.
        """
        query = Q()
        if username:
            query = Q(username__iexact=username.strip().lower())
        elif email:
            query = Q(email__iexact=email.strip().lower())
        elif username and email:
            query = Q(
                Q(username__iexact=username.strip().lower()) |
                Q(email__iexact=email.strip().lower())
            )
        else:
            logger.error(
                "No username or email provided to 'check if user exists'.")
            return False

        return User.objects.filter(query).exists()

    @classmethod
    def register(cls, data: dict = None, is_superuser: bool = False, is_staff: bool = False) -> Resp:
        resp = Resp()

        if cls.check_if_user_exists(username=data.get('username'), email=data.get('email')):
            resp.error = "User Exists."
            resp.data = data
            resp.message = f"A user with the given credentials (username | email) already exists."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.warning(resp.to_text())
            return resp

        if "user_type" in data:
            del data['user_type']
        if "is_superuser" in data:
            del data['is_superuser']
        if 'is_staff' in data:
            del data['is_staff']

        if is_superuser:
            data['is_superuser'] = True
            data['is_staff'] = True

        if is_staff:
            data['is_staff'] = True

        password = data.get('password', '')
        if not FormatRegex.PASSWORD_REGEX.match(password):
            resp.error = "Weak Password."
            resp.data = data
            resp.message = "The provided password does not meet the required complexity."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.warning(resp.to_text())
            return resp

        serializer = UserRegisterSerializer(data=data)
        if not serializer.is_valid():
            resp.error = "Invalid Data."
            resp.data = serializer.errors
            resp.message = "The provided data is invalid."
            resp.status_code = status.HTTP_400_BAD_REQUEST

            logger.warning(resp.to_text())
            return resp

        serializer.save()

        resp.message = f"User '{serializer.instance.email}' registered successfully."
        resp.data = UserSerializer(serializer.instance).data
        resp.status_code = status.HTTP_201_CREATED

        logger.info(resp.to_text())
        return resp

    @classmethod
    def login_via_password(cls, username: str = None, email: str = None, password: str = None) -> Resp:
        resp = Resp()
        if not username and not email:
            resp.error = "Invalid Parameters"
            resp.message = "Provide either username or email to login."
            resp.status_code = status.HTTP_400_BAD_REQUEST
            logger.error(resp.to_text())
            return resp

        user_resp = cls.get(username=username, email=email, return_obj=True)
        if user_resp.error:
            return user_resp

        user: User = user_resp.data

        if user.blocked_until and user.blocked_until > timezone.now():
            resp.error = "User Blocked"
            resp.message = f"User is blocked until {user.blocked_until} due to multiple unsuccessful login attempts."
            resp.status_code = status.HTTP_403_FORBIDDEN
            logger.warning(resp.to_text())
            return resp

        if not password:
            resp.error = "Invalid Parameters"
            resp.message = "Password not provided."
            resp.status_code = status.HTTP_400_BAD_REQUEST
            logger.error(resp.to_text())
            return resp

        if not user.check_password(password):
            user.unsuccessful_login_attempts += 1
            user.save()

            if user.unsuccessful_login_attempts > django_settings.OTP_ATTEMPT_LIMIT:
                user.block()
                resp.error = "User Blocked"
                resp.message = f"Too many unsuccessful login attempts. User is blocked until {user.blocked_until}."
                resp.status_code = status.HTTP_403_FORBIDDEN
                return resp

            resp.error = "Invalid Credentials"
            resp.message = "The provided credentials are invalid."
            resp.data = {
                "username": username,
                "email": email,
                "password": password,
                "attemptsLeft": django_settings.OTP_ATTEMPT_LIMIT - user.unsuccessful_login_attempts
            }
            resp.status_code = status.HTTP_401_UNAUTHORIZED
            logger.warning(resp.to_text())
            return resp

        tokens = JWTUtils.get_tokens_for_user(user)

        if user.blocked_until:
            user.unblock()

        resp.message = f"User '{user.email}' logged in successfully."
        resp.data = {
            'user': UserSerializer(user).data,
            'tokens': tokens
        }
        resp.status_code = status.HTTP_200_OK
        logger.info(resp.to_text())
        return resp

    @classmethod
    def delete(cls, user: User = None, email: str = None, password: str = None) -> Resp:
        resp = Resp()
        if not user or not isinstance(user, User):
            resp.error = "Invalid Parameters"
            resp.message = "Valid user instance must be provided to delete a user."
            resp.status_code = status.HTTP_400_BAD_REQUEST
            logger.error(resp.to_text())
            return resp

        if not password:
            resp.error = "Invalid Parameters"
            resp.message = "Password must be provided to delete a user."
            resp.status_code = status.HTTP_400_BAD_REQUEST
            logger.error(resp.to_text())
            return resp

        if not email:
            resp.error = "Invalid Parameters"
            resp.message = "Email must be provided to delete a user."
            resp.status_code = status.HTTP_400_BAD_REQUEST
            logger.error(resp.to_text())
            return resp

        if user.blocked_until and user.blocked_until > timezone.now():
            resp.error = "User Blocked"
            resp.message = f"User is blocked until {user.blocked_until}."
            resp.status_code = status.HTTP_403_FORBIDDEN
            logger.warning(resp.to_text())
            return resp

        if user.email != email.strip().lower():
            resp.error = "Invalid Credentials"
            resp.message = "The provided email does not match the user's email."
            resp.status_code = status.HTTP_401_UNAUTHORIZED
            logger.warning(resp.to_text())
            return resp

        if not user.check_password(password):
            resp.error = "Invalid Credentials"
            resp.message = "The provided password is incorrect."
            resp.status_code = status.HTTP_401_UNAUTHORIZED
            logger.warning(resp.to_text())
            return resp

        user_email = user.email
        user.delete()

        resp.message = f"User '{user_email}' deleted successfully."
        resp.status_code = status.HTTP_200_OK
        logger.info(resp.to_text())
        return resp


class Oauth2Helpers:
    pass