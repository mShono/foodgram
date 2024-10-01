import django_filters

from .models import Ingredient


class IngredientFilter(django_filters.FilterSet):
    """Filter for Ingredient model."""

    name = django_filters.CharFilter(
        field_name="name", lookup_expr="istartswith"
    )

    class Meta:
        model = Ingredient
        fields = ["name",]
