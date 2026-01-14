from django.urls import path
from auth_app.apis import UserRegisterAPI, AdminUserRegisterAPI, UserPasswordLoginAPI


PREFIX = "api/auth/"

urlpatterns = [
    path('register-normal/', UserRegisterAPI.as_view(), name='new-user-registration'),
    path('register-sudo/', AdminUserRegisterAPI.as_view(), name='admin-user-registration'),
    path('login/', UserPasswordLoginAPI.as_view(), name='password-login'),
]