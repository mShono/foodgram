from rest_framework import serializers

from .models import Tag, Ingredient
from users.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUserViewSet."""

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
        )


class TagSerializer(serializers.ModelSerializer):
    """Serializer for TagViewSet."""

    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "slug",
        )
        # extra_kwargs = {"url": {"lookup_field": "slug"}}


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for IngredientViewSet."""

    class Meta:
        model = Ingredient
        fields = (
            "id",
            "name",
            "measurement_unit",
        )