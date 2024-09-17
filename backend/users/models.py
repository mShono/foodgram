from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.constants import (DEFAULT_USER_ROLE, MAX_LEN_EMAIL,
                                 MAX_LEN_ROLE, MAX_LEN_USER_INFO)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name'
        'last_name'
    )
    # ADMIN = "admin"
    # MODERATOR = "moderator"
    # USER = "user"
    # ROLES = (
    #     (USER, "Пользователь"),
    #     (MODERATOR, "Модератор"),
    #     (ADMIN, "Администратор"),
    # )

    username = models.CharField(
        "Имя пользователя",
        max_length=MAX_LEN_USER_INFO,
        unique=True,
        error_messages={
            "unique": "Пользователь с таким именем уже существует"
        }
        # validators=(validate_username, UnicodeUsernameValidator()),
    )
    email = models.EmailField(
        "Почта",
        max_length=MAX_LEN_EMAIL,
        unique=True,
        error_messages={
            "unique": "Данный адрес уже используется",
        }
    )
    first_name = models.CharField(
        "Имя",
        max_length=MAX_LEN_USER_INFO,
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=MAX_LEN_USER_INFO,
    )
    avatar = models.ImageField(
        "Изображение",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
