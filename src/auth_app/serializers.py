from django.contrib.auth.hashers import make_password

from rest_framework.serializers import ModelSerializer
from auth_app.models import User, UserProfile


class UserRegisterSerializer(ModelSerializer):
    """
    Serializer used when registering a new user.
    """
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password'
        )

    def create(self, validated_data):
        validated_data['password'] = make_password(
            validated_data.get('password'))
        return super(UserRegisterSerializer, self).create(validated_data)


class UserSerializer(ModelSerializer):
    """
    General-purpose serializer to be used when returning user data.
    """
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'slug',
        )


class UserProfileInputSerializer(ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"


class UserProfileOutputSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            'user',
            'first_name',
            'last_name',
            'bio',
            'profile_picture'
        )
