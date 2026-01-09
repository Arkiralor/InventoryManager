from enum import Enum
from django.db import models

class Oauth2Choices:
    GOOGLE = "google"
    FACEBOOK = "facebook"
    GITHUB = "github"

    PROVIDER_CHOICES = [
        (GOOGLE, "Google"),
        (FACEBOOK, "Facebook"),
        (GITHUB, "GitHub"),
    ]