import base64
import uuid

from django.core.files.base import ContentFile
from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Tag)
from rest_framework import serializers
from users.models import Subscription, User

from backend.constants import PAGE_SIZE


class Base64ImageField(serializers.ImageField):
    """Настраиваемое поле для обработки кодировки изображений в Base64."""

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
    """Сериализатор для загрузки аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)


class RecipeShortInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода рецепта."""

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    class Meta:
        model = Subscription
        fields = (
            "subscriber",
            "subscribed_to",
        )

    def validate(self, attrs):
        user = attrs.get("subscriber")
        followee = attrs.get("subscribed_to")
        if user == followee:
            raise serializers.ValidationError(
                "Вы не можете подписаться на самого себя."
            )
        if Subscription.objects.filter(
                subscriber=user,
                subscribed_to=followee
        ).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого автора."
            )
        return attrs

    def to_representation(self, instance):
        user = instance.subscribed_to
        recipes_limit = self.context.get("recipes_limit", PAGE_SIZE)
        recipes = user.recipes.all()
        if recipes_limit:
            recipes = recipes[:recipes_limit]
        recipes_data = RecipeShortInfoSerializer(recipes, many=True).data
        subscription = Subscription.objects.filter(
            subscriber=instance.subscriber,
            subscribed_to=user
        ).exists()
        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_subscribed": subscription,
            "recipes": recipes_data,
            "recipes_count": getattr(instance, "recipes_count", 0),
            "avatar": user.avatar.url if user.avatar else None,
        }


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Favorite
        fields = ("recipe", "user")

    def to_representation(self, instance):
        return RecipeShortInfoSerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины покупок."""

    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = ShoppingCart
        fields = ("recipe", "user")

    def to_representation(self, instance):
        return RecipeShortInfoSerializer(instance.recipe).data


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для кастомной модели пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
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
    """Сериализатор для Тегов."""

    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "slug",
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для Ингредиентов."""

    class Meta:
        model = Ingredient
        fields = (
            "id",
            "name",
            "measurement_unit",
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RecipeIngredient."""

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

    ingredients = RecipeIngredientWriteSerializer(
        many=True, write_only=True, required=True, allow_empty=False
    )
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

    def validate(self, attrs):
        required_fields = [
            "tags", "ingredients"
        ]
        for field in required_fields:
            if field not in attrs or not attrs[field]:
                raise serializers.ValidationError(
                    f'{field} = ["Обязательное поле"]'
                )
        if "ingredients" in attrs:
            ingredients = attrs["ingredients"]
            ingredients_ids = [ingredient['id'] for ingredient in ingredients]
            if len(ingredients_ids) != len(set(ingredients_ids)):
                raise serializers.ValidationError(
                    {"ingredients": [
                        "Ингредиенты не должны повторяться"
                    ]}
                )
            for ingredient in ingredients:
                if not Ingredient.objects.filter(id=ingredient["id"]).exists():
                    raise serializers.ValidationError(
                        {"ingredients": [
                            "Такого ингредиента не существует"
                        ]}
                    )
                if ingredient["amount"] <= 0:
                    raise serializers.ValidationError(
                        {"ingredients": [
                            "Количество не должно быть меньше нуля"
                        ]}
                    )
        if "tags" in attrs:
            tags = attrs["tags"]
            tag_ids = [tag.id for tag in tags]
            if len(tag_ids) != len(set(tag_ids)):
                raise serializers.ValidationError(
                    {"tags": ["Тэги не должны повторяться"]}
                )
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
        user = self.context.get("request").user
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(author=user, **validated_data)
        self._update_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        self._update_tags_and_ingredients(instance, tags, ingredients)
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
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    tags = TagSerializer(many=True)
    author = UserSerializer(
        read_only=True,
    )
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

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
