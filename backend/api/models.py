from django.db import models
from backend.constants import (
    MAX_LEN_TAG_NAME, MAX_LEN_INGREDIENT_NAME, MAX_LEN_MEASURMENT_UNIT,
    MAX_LEN_RECIPE_NAME,
)
from users.models import CustomUser


class Tag(models.Model):
    """Tag's model."""

    name = models.CharField(
        "Название",
        max_length=MAX_LEN_TAG_NAME,
        unique=True
    )
    slug = models.SlugField(
        "Идентификатор",
        max_length=MAX_LEN_TAG_NAME,
        unique=True
    )

    class Meta:
        verbose_name = "тэг"
        verbose_name_plural = "Тэги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient's model."""

    name = models.CharField(
        "Ингредиент",
        max_length=MAX_LEN_INGREDIENT_NAME,
        unique=True
    )
    measurement_unit = models.CharField(
        "Мера веса",
        max_length=MAX_LEN_MEASURMENT_UNIT,
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Recipe's model."""

    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Тэг",
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name="recipes",
        verbose_name="Ингредиент",
    )
    name = models.CharField(
        "Имя рецепта",
        max_length=MAX_LEN_RECIPE_NAME,
        unique=True
    )
    image = models.ImageField(
        "Картинка",
        upload_to="recipes/")
    text = models.TextField("Текст рецепта")
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления",
    )

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """The model connecting Recipe and Ingredient models."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name="Рецепт",
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
    )
    # amount = models.FloatField(
    #     "Количество",
    # )

    class Meta:
        verbose_name = "рецепт-ингредиент"
        verbose_name_plural = "Рецепты-Ингредиенты"

    def __str__(self):
        return f'{self.ingredients.name} в {self.recipe.name}: {self.amount}'
