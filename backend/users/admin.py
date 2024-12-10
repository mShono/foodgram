from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "avatar",
    )
    list_filter = ("username",)
    search_fields = (
        "username", "email"
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("pk", "subscriber", "subscribed_to")
    search_fields = ("subscriber",)
    empty_value_display = "-пусто-"
