from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Value
from django.db.models.functions import Concat

from .models import Subscription, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "avatar",
        'is_superuser',
        'is_active',
    )
    search_fields = (
        "username", "email", "first_name", "last_name",
    )

    def get_search_results(self, request, queryset, search_term):
        """Поиск для first_name и last_name в одном запросе."""

        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        if search_term:
            full_name_query = queryset.annotate(
                full_name=Concat(
                    'first_name', Value(' '), 'last_name'
                )
            )
            queryset |= full_name_query.filter(
                full_name__icontains=search_term
            )
        return queryset, use_distinct


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("pk", "subscriber", "subscribed_to")
    list_display_links = ("subscriber__username",)
    search_fields = ("subscriber",)
    empty_value_display = "-пусто-"
