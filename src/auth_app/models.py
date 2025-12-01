from django.db import models
from django.template.defaultfilters import slugify
from core.boilerplate.base_model import BaseModel
from django.conf import settings as django_settings
from django.contrib.auth.hashers import make_password

from datetime import datetime, timedelta
from uuid import uuid4

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=256)
    slug = models.SlugField(max_length=250, null=True, blank=True)

    unsuccessful_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of unsuccessful login attempts"
    )
    blocked_until = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Blocked until"
    )

    date_joined = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.clean_text_field('username')
        self.clean_text_field('email')
        self.create_slug()

        super(User, self).save(*args, **kwargs)

    def block(self, minutes=django_settings.OTP_ATTEMPT_TIMEOUT):
        self.blocked_until = datetime.now() + timedelta(minutes=minutes)
        self.unsuccessful_login_attempts = 0
        self.save()

    def unblock(self):
        self.blocked_until = None
        self.unsuccessful_login_attempts = 0
        self.save()

    def create_slug(self):
        if not self.slug:
            self.slug = slugify(self.username)

    def clean_text_field(self, field_name: str):
        value = getattr(self, field_name, None)
        if value and isinstance(value, str):
            cleaned_value = value.lstrip().rstrip().lower()
            setattr(self, field_name, cleaned_value)

    def force_reset_password(self, new_password: str):
        self.password = make_password(new_password)
        self.save()

    class Meta:
        indexes = (
            models.Index(fields=("username", "email"))
        )


class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='images/profile_pictures', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile."
    
    def save(self, *args, **kwargs):
        if self.first_name:
            self.first_name = self.first_name.lstrip().rstrip().title()
        
        if self.last_name:
            self.last_name = self.last_name.lstrip().rstrip().title()

        super(UserProfile, self).save(*args, **kwargs)
    
    class Meta:
        indexes = (
            models.Index(fields=("user",)),
            models.Index(fields=("first_name", "last_name")),
        )
    