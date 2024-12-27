from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "slug")
    list_display_links = ("name",)
    search_fields = ("name",)
    empty_value_display = "-пусто-"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
    empty_value_display = "-пусто-"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "author", "name")
    list_display_links = ("author",)
    list_filter = ("name", "author", "tags",)
    empty_value_display = "-пусто-"
    readonly_fields = ("favorites_count",)

    def get_queryset(self, request):
        """Оптимизация запроса для списка рецептов."""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "author"
        ).prefetch_related(
            "tags", "ingredients"
        )

    @admin.display(description="Количество в избранном")
    def favorites_count(self, obj):
        """Возвращает количество рецептов, добавленных в избранное"""
        return obj.favorites.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        "pk", "recipe", "ingredients", "amount",
    )
    list_display_links = ("recipe",)
    search_fields = ("recipe",)
    empty_value_display = "-пусто-"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "user")
    list_display_links = ("recipe",)
    search_fields = ("recipe__name", "user__username", "user__email")
    empty_value_display = "-пусто-"

    def get_queryset(self, request):
        """Оптимизация запроса для избранного."""
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "recipe")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "user")
    list_display_links = ("recipe",)
    search_fields = ("recipe__name", "user__username", "user__email")
    empty_value_display = "-пусто-"

    def get_queryset(self, request):
        """Оптимизация запроса для корзины покупок."""
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "recipe")
