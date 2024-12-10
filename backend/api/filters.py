import django_filters

from recipe.models import Ingredient, Recipe, Tag


class IngredientFilter(django_filters.FilterSet):
    """Фильтр для модели Ингредиентов."""

    name = django_filters.CharFilter(
        field_name="name", lookup_expr="istartswith"
    )

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для модели Рецептов."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all()
    )
    is_favorited = django_filters.filters.CharFilter(
        method="is_favorited_filter"
    )
    is_in_shopping_cart = django_filters.filters.CharFilter(
        method="is_in_shopping_cart_filter"
    )

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart")

    def is_in_shopping_cart_filter(self, queryset, name, value):
        user = self.request.user
        if value == "1" and not user.is_anonymous:
            return queryset.filter(recipe_shoppingcart_related__user=user)
        return queryset

    def is_favorited_filter(self, queryset, name, value):
        user = self.request.user
        if value == "1" and not user.is_anonymous:
            return queryset.filter(recipe_favorite_related__user=user)
        return queryset
