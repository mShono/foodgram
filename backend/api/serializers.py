import base64
import uuid
from django.core.files.base import ContentFile
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

    # ingredients = serializers.StringRelatedField() # - не поддерживает операцию записи
    # id = serializers.IntegerField()
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.SerializerMethodField()
    # ingredients = IngredientSerializer()
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

    # def get_fields(self):
    #     fields = super().get_fields()
    #     request = self.context.get('request', None)

    #     if request and request.method in ['POST', 'PUT', 'PATCH']:
    #         fields.pop('ingredients')

    #     return fields


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


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Serializer for RecipeViewSet."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    ) # возвращает только id
    # tags = TagFieldRepresentation(
    #     many=True,
    #     queryset=Tag.objects.all()
    # ) # рабочий вариант
    # tags = TagSerializer(many=True) # рабочий вариант
    # author = serializers.PrimaryKeyRelatedField(
    #     default=serializers.CurrentUserDefault(),
    #     read_only=True,
    # )
    # ingredients = RecipeIngredientSerializer(
    #     source='recipe_ingredient',
    #     many=True,
    # )
    # ingredients = serializers.PrimaryKeyRelatedField(
    #     queryset=RecipeIngredient.objects.all(),
    #     many=True,
    # )
    ingredients = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        write_only=True
    )
    # ingredients = serializers.ListField(
    #     child=serializers.DictField(child=serializers.PrimaryKeyRelatedField(
    #         queryset=RecipeIngredient.objects.all()))
    # )

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

    def to_internal_value(self, data):
        image_data = data.get('image', None)
        if image_data and isinstance(image_data, str) and image_data.startswith('data:image'):
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f'{uuid.uuid4()}.{ext}'
            data['image'] = ContentFile(base64.b64decode(imgstr), name=file_name)
        return super().to_internal_value(data)

    def create(self, validated_data):
        print(f'validated_data = {validated_data}')
        tags = validated_data.pop('tags')
        # ingredients = validated_data.pop('recipe_ingredient')
        ingredients = validated_data.pop('ingredients')
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        print(f'ingredients = {ingredients}')
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data['id']
            print(f'ingredient_id = {ingredient_id}')
            amount = ingredient_data['amount']
            print(f'amount = {amount}')
            # RecipeIngredient.objects.create(
            #     ingredients_id=ingredient_id, recipe=recipe, amount=amount
            # )
            RecipeIngredient.objects.create(
                ingredients_id=ingredient_id, recipe=recipe, amount=amount
            )
        return recipe

    def to_representation(self, instance):
        data = super().to_representation(instance)
        ingredients = RecipeIngredient.objects.filter(recipe=instance)
        ingredients_data = [
            {"id": ingredient.ingredients.id, "amount": ingredient.amount}
            for ingredient in ingredients
        ]
        data = {"ingredients": ingredients_data, **data}
        # data['ingredients'] = ingredients_data
        return data

    # def update(self, instance, validated_data):
    #     tags = validated_data.pop('tags', None)
    #     ingredients = validated_data.pop('ingredients', None)

    #     if tags is not None:
    #         instance.tags.set(tags)

    #     if ingredients is not None:
    #         instance.recipe_ingredient.all().delete()
    #         for ingredient_data in ingredients:
    #             ingredient_id = ingredient_data['id']
    #             amount = ingredient_data['amount']
    #             RecipeIngredient.objects.create(
    #                 ingredients_id=ingredient_id, recipe=instance, amount=amount
    #             )
    #     return super().update(instance, validated_data)


class RecipeReadSerializer(serializers.ModelSerializer):
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
            # "is_favorited",
            # "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
