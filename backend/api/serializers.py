import base64
import uuid

from django.core.files.base import ContentFile
from django.db.utils import IntegrityError
from djoser.serializers import SetPasswordSerializer
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from backend.constants import MAX_LEN_RECIPE_NAME
from users.models import CustomUser, Subscription

from recipe.models import (Ingredient, Favorite, Recipe, RecipeIngredient,
                           ShoppingCart, Tag)


class Base64ImageField(serializers.ImageField):
    """Custom field to handle image encoding to Base64."""

    def to_representation(self, value):
        if value:
            with open(value.path, "rb") as image_file:
                string = base64.b64encode(image_file.read()).decode("utf-8")
                return f"data:image/png;base64,{string}"
        return None

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            file_name = f"{uuid.uuid4()}.{ext}"
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
    """Serializer for setting a new password."""

    def validate(self, attrs):
        super().validate(attrs)
        return {
            "new_password": attrs["new_password"],
            "current_password": attrs["current_password"]
        }


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscriptions."""

    email = serializers.EmailField(source="subscribed_to.email")
    id = serializers.IntegerField(source="subscribed_to.id")
    username = serializers.CharField(source="subscribed_to.username")
    first_name = serializers.CharField(source="subscribed_to.first_name")
    last_name = serializers.CharField(source="subscribed_to.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source="subscribed_to.avatar")

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
        request = self.context.get("request")
        if request and not request.user.is_anonymous:
            return Subscription.objects.filter(
                subscriber=request.user,
                subscribed_to=obj.subscribed_to
            ).exists()
        return False

    def get_recipes(self, obj):
        recipes_limit = self.context.get("recipes_limit")
        recipes = obj.subscribed_to.recipes.all()
        if recipes_limit:
            recipes = recipes[:recipes_limit]
        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image.url,
                "cooking_time": recipe.cooking_time
            } for recipe in recipes
        ]

    def get_recipes_count(self, obj):
        return obj.subscribed_to.recipes.count()


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for Subscriptions."""

    id = serializers.IntegerField(source="recipe.id")
    name = serializers.CharField(source="recipe.name")
    image = serializers.CharField(source="recipe.image")
    cooking_time = serializers.IntegerField(source="recipe.cooking_time")

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

    id = serializers.IntegerField(source="recipe.id")
    name = serializers.CharField(source="recipe.name")
    image = serializers.CharField(source="recipe.image")
    cooking_time = serializers.IntegerField(source="recipe.cooking_time")

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
        request = self.context.get("request")
        if request and not request.user.is_anonymous:
            return Subscription.objects.filter(
                subscriber=request.user,
                subscribed_to=obj
            ).exists()
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

    id = serializers.IntegerField(source="ingredients.id")
    name = serializers.CharField(source="ingredients.name")
    measurement_unit = serializers.CharField(
        source="ingredients.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Сериализатор для записи ингредиентов."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецептов."""

    ingredients = RecipeIngredientWriteSerializer(many=True, write_only=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

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

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if self.context['request'].method in ['PATCH', 'PUT']:
    #         self.fields['image'].required = False

    def check_authenticated_user(self):
        user = self.context.get("request").user
        if user.is_anonymous:
            raise NotAuthenticated("Учетные данные не были предоставлены.")
        return user

    def validate(self, attrs):
        required_fields = [
            "tags", "ingredients", "image", "name", "text", "cooking_time"
        ]
        if self.context.get("request").method == "PATCH":
            required_fields.remove("image")
        errors = {}
        for field in required_fields:
            if field not in attrs or not attrs[field]:
                errors[field] = ["Обязательное поле"]
        if "ingredients" in attrs:
            ingredients = attrs["ingredients"]
            ingredients_ids = [ingredient['id'] for ingredient in ingredients]
            if len(ingredients_ids) != len(set(ingredients_ids)):
                errors["ingredients"] = ["Обязательное поле"]
            for ingredient in ingredients:
                if not Ingredient.objects.filter(id=ingredient["id"]).exists():
                    errors["ingredients"] = ["Обязательное поле"]
                if ingredient["amount"] <= 0:
                    errors["ingredients"] = ["Обязательное поле"]
        if "tags" in attrs:
            tags = attrs["tags"]
            tag_ids = [tag.id for tag in tags]
            if len(tag_ids) != len(set(tag_ids)):
                errors["tags"] = ["Обязательное поле"]
            for tag_id in tag_ids:
                if not Tag.objects.filter(id=tag_id).exists():
                    errors["tags"] = ["Обязательное поле"]
        if "name" in attrs:
            name = attrs["name"]
            if len(name) > MAX_LEN_RECIPE_NAME:
                errors["name"] = ["Обязательное поле"]
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def _update_tags_and_ingredients(self, recipe, tags, ingredients):
        """Обновление тегов и ингредиентов для рецепта."""
        recipe.tags.set(tags)
        recipe.recipe_ingredient.all().delete()
        recipe_ingredients = [
            RecipeIngredient(
                ingredients_id=ingredient_data["id"],
                recipe=recipe,
                amount=ingredient_data["amount"]
            )
            for ingredient_data in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        user = self.check_authenticated_user()
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(author=user, **validated_data)
        self._update_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        user = self.check_authenticated_user()
        if user != instance.author:
            raise PermissionDenied(
                "У вас недостаточно прав для выполнения данного действия."
            )
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        self._update_tags_and_ingredients(instance, tags, ingredients)
        # if "image" not in validated_data:
        #     validated_data.pop("image", None)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tags = instance.tags.all()
        tags_data = [
            {"id": tag.id, "name": tag.name, "slug": tag.slug}
            for tag in tags
        ]
        ingredients = RecipeIngredient.objects.filter(recipe=instance)
        ingredients_data = [
            {
                **IngredientSerializer(ingredient.ingredients).data,
                "amount": ingredient.amount
            }
            for ingredient in ingredients
        ]
        data = {
            "id": data.get("id"),
            "tags": tags_data,
            "author": data.get("author"),
            "ingredients": ingredients_data,
            "is_favorited": data.get("is_favorited"),
            "is_in_shopping_cart": data.get("is_in_shopping_cart"),
            "name": data.get("name"),
            "image": data.get("image"),
            "text": data.get("text"),
            "cooking_time": int(data.get("cooking_time"))
        }
        return data

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False


class RecipeReadSerializer(serializers.ModelSerializer):
    """Reading serializer for RecipeViewSet."""

    tags = TagSerializer(many=True)
    author = UserSerializer(
        read_only=True,
    )
    ingredients = serializers.SerializerMethodField()
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

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return [
            {
                **IngredientSerializer(ingredient.ingredients).data,
                "amount": ingredient.amount
            }
            for ingredient in ingredients
        ]

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and not request.user.is_anonymous:
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and not request.user.is_anonymous:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False
