from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.request import Request


from auth_app.helpers import UserModelHelpers

from auth_app import logger


class UserRegisterAPI(APIView):
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        resp = UserModelHelpers.register(data=request.data)
        return resp.to_response()


class AdminUserRegisterAPI(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request: Request) -> Response:
        resp = UserModelHelpers.register(
            data=request.data, is_admin=True, is_staff=True
        )
        return resp.to_response()


class UserPasswordLoginAPI(APIView):
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        resp = UserModelHelpers.login_via_password(
            username=username, email=email, password=password
        )
        return resp.to_response()
