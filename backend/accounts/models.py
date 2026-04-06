from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    bio = models.TextField(blank=True, default="")
    avatar_url = models.URLField(blank=True, default="")
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "accounts_user"

    def __str__(self):
        return self.username
