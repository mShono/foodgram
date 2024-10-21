from django.contrib import admin

from .models import Tag, Ingredient, Recipe, RecipeIngredient

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "slug")
    search_fields = ("name",)
    empty_value_display = "-пусто-"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "measurement_unit")
    search_fields = ("name",)
    empty_value_display = "-пусто-"
    # "pk" из list_display убрать


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "pk", "author", "name",
    )
    search_fields = ("name", "author",)
    list_filter = ("tags",)
    empty_value_display = "-пусто-"
    # на странице рецепта вывести общее число добавлений этого рецепта в избранное.
    # "pk" из list_display убрать


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        "pk", "recipe", "ingredients", "amount",
    )
    search_fields = ("recipie",)
    empty_value_display = "-пусто-"
