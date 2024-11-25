from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from backend.constants import MAX_LEN_EMAIL, MAX_LEN_USER_INFO


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = (
        "username",
        "first_name",
        "last_name"
    )

    username = models.CharField(
        "Имя пользователя",
        max_length=MAX_LEN_USER_INFO,
        unique=True,
        error_messages={
            "unique": "Пользователь с таким именем уже существует"
        },
        validators=(UnicodeUsernameValidator(),),
    )
    email = models.EmailField(
        "Электронная почта",
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


class Subscription(models.Model):
    """Модель подписок."""

    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Подписчик",
    )
    subscribed_to = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="followees",
        verbose_name="Блогер",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "subscribed_to"],
                name="unique_user_following"
            )
        ]
        default_related_name = "subscriptions"
        verbose_name = "подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.subscriber} на {self.subscribed_to}"
