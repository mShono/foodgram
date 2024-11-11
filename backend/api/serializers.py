import base64
import uuid

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from djoser.serializers import SetPasswordSerializer
from django.shortcuts import get_object_or_404
from django.db.utils import IntegrityError
from rest_framework import serializers

from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from backend.constants import (
    MAX_LEN_TAG_NAME, MAX_LEN_INGREDIENT_NAME, MAX_LEN_MEASURMENT_UNIT,
    MAX_LEN_RECIPE_NAME,
)
from .models import (
    Tag, Ingredient, Recipe, RecipeIngredient, Subscription, Favorite,
    ShoppingCart
)
from users.models import CustomUser


class Base64ImageField(serializers.ImageField):
    """Custom field to handle image encoding to Base64."""

    def to_representation(self, value):
        if value:
            with open(value.path, "rb") as image_file:
                string = base64.b64encode(image_file.read()).decode('utf-8')
                return f'data:image/png;base64,{string}'
        return None

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f'{uuid.uuid4()}.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=file_name)
        else:
            raise serializers.ValidationError("Обязательное поле")
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer for uploading avatar."""

    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ("avatar",)


class CustomSetPasswordSerializer(SetPasswordSerializer):
    def validate(self, attrs):
        super().validate(attrs)
        return {
            "new_password": attrs["new_password"],
            "current_password": attrs["current_password"]
        }


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscriptions."""
    email = serializers.EmailField(source='subscribed_to.email')
    id = serializers.IntegerField(source='subscribed_to.id')
    username = serializers.CharField(source='subscribed_to.username')
    first_name = serializers.CharField(source='subscribed_to.first_name')
    last_name = serializers.CharField(source='subscribed_to.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='subscribed_to.avatar')

    class Meta:
        model = Subscription
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Subscription.objects.filter(subscriber=request.user, subscribed_to=obj.subscribed_to).exists()
        return False

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        recipes = obj.subscribed_to.recipes.all()
        if recipes_limit:
            recipes = recipes[:recipes_limit]
        return [
            {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url,
                'cooking_time': recipe.cooking_time
             } for recipe in recipes
            ]

    def get_recipes_count(self, obj):
        return obj.subscribed_to.recipes.count()


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for Subscriptions."""
    id = serializers.IntegerField(source='recipe.id')
    name = serializers.CharField(source='recipe.name')
    image = serializers.CharField(source='recipe.image')
    cooking_time = serializers.CharField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for Shopping Cart."""
    id = serializers.IntegerField(source='recipe.id')
    name = serializers.CharField(source='recipe.name')
    image = serializers.CharField(source='recipe.image')
    cooking_time = serializers.CharField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class UserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUserViewSet."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Subscription.objects.filter(subscriber=request.user, subscribed_to=obj).exists()
        return False


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

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )

    def get_measurement_unit(self, obj):
        return obj.ingredients.measurement_unit

    def get_name(self, obj):
        return obj.ingredients.name

    # def validate_id(self, value):
    #     print(f'value_id = {value}')
    #     if not Ingredient.objects.filter(id=value).exists():
    #         raise serializers.ValidationError(f"The 'ingredient' {value} do not exists")
    #     return value


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Writing serializer for RecipeViewSet."""
    # tags = serializers.PrimaryKeyRelatedField(
    #     many=True,
    #     queryset=Tag.objects.all()
    # )
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    ingredients = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        write_only=True
    )
    image = Base64ImageField()
    name = serializers.CharField(allow_blank=True)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def check_authenticated_user(self):
        user = self.context.get('request').user
        if user.is_anonymous:
            raise NotAuthenticated("Учетные данные не были предоставлены.")
        return user

    def validate(self, attrs):
        required_fields = ["tags", "ingredients", "image", "name", "text", "cooking_time"]
        errors = {}
        for field in required_fields:
            if field not in attrs or not attrs[field]:
                errors[field] = ["Обязательное поле"]
        if "ingredients" in attrs:
            ingredients = attrs["ingredients"]
            unique_ingredients = set()
            for ingredient in ingredients:
                if not Ingredient.objects.filter(id=ingredient['id']).exists():
                    errors["ingredients"] = ["Обязательное поле"]
                if ingredient['amount'] <= 0:
                    errors["ingredients"] = ["Обязательное поле"]
                if ingredient['id'] in unique_ingredients:
                    errors["ingredients"] = ["Обязательное поле"]
                unique_ingredients.add(ingredient['id'])
        if "tags" in attrs:
            tags = attrs["tags"]
            if len(tags) != len(set(tags)):
                errors["tags"] = ["Обязательное поле"]
            for tag in tags:
                if not Tag.objects.filter(id=tag).exists():
                    errors["tags"] = ["Обязательное поле"]
        if "name" in attrs:
            name = attrs["name"]
            if len(name) > MAX_LEN_RECIPE_NAME:
                errors["name"] = ["Обязательное поле"]
        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        user = self.check_authenticated_user()
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        try:
            recipe = Recipe.objects.create(author=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"name": ["Рецепт с таким именем уже существует."]})
        recipe.tags.set(tags)
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data['id']
            amount = ingredient_data['amount']
            RecipeIngredient.objects.create(
                ingredients_id=ingredient_id, recipe=recipe, amount=amount
            )
        return recipe

    def update(self, instance, validated_data):
        user = self.check_authenticated_user()
        if user != instance.author:
            raise PermissionDenied("У вас недостаточно прав для выполнения данного действия.")
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        instance.recipe_ingredient.all().delete()
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data['id']
            amount = ingredient_data['amount']
            RecipeIngredient.objects.create(
                ingredients_id=ingredient_id, recipe=instance, amount=amount
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tags = instance.tags.all()
        tags_id = [tag.id for tag in tags]
        # data["tags"] = tags_id
        ingredients = RecipeIngredient.objects.filter(recipe=instance)
        ingredients_data = [
            {"id": ingredient.ingredients.id, "amount": ingredient.amount}
            for ingredient in ingredients
        ]
        # data = {"ingredients": ingredients_data, **data}
        data = {
            "ingredients": ingredients_data,
            "tags": tags_id,
            "image": data.get("image"),
            "name": data.get("name"),
            "text": data.get("text"),
            "cooking_time": data.get("cooking_time")
        }
        return data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Reading serializer for RecipeViewSet."""
    tags = TagSerializer(many=True)
    author = UserSerializer(
        read_only=True,
    )
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredient',
        many=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False
