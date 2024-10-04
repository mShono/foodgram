from rest_framework import serializers

from rest_framework.relations import PrimaryKeyRelatedField

from .models import Tag, Ingredient, Recipe, RecipeIngredient
from users.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUserViewSet."""

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            # "is_subscribed",
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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for RecipeIngredientViewSet."""

    ingredients = serializers.StringRelatedField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = (
            "id",
            "ingredients",
            "measurement_unit",
            "amount",
        )

    def get_measurement_unit(self, obj):
        return obj.ingredients.measurement_unit


class TagFieldRepresentation(serializers.PrimaryKeyRelatedField):
    """Displaying Tag's related fields as a dictionary."""

    def to_representation(self, value):
        tag = Tag.objects.get(pk=value.pk)
        return {"id": tag.pk, "name": tag.name, "slug": tag.slug}


class AuthorFieldRepresentation(serializers.PrimaryKeyRelatedField):
    """Displaying Tag's related fields as a dictionary."""

    def to_representation(self, value):
        tag = Tag.objects.get(pk=value.pk)
        return {"id": tag.pk, "name": tag.name, "slug": tag.slug}


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for RecipeViewSet."""
    # tags = serializers.PrimaryKeyRelatedField(
    #     many=True,
    #     queryset=Tag.objects.all()
    # ) # возвращает только id
    tags = TagFieldRepresentation(
        many=True,
        queryset=Tag.objects.all()
    ) # рабочий вариант
    # tags = TagSerializer(many=True) # рабочий вариант
    # author = serializers.PrimaryKeyRelatedField(
    #     default=serializers.CurrentUserDefault(),
    #     read_only=True,
    # )
    author = CustomUserSerializer(
        read_only=True,
    ) # рабочий вариант
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredient',
        many=True,
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            # "is_favorited",
            # "is_in_shopping_cart",
        )
