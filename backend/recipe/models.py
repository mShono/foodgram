from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from backend.constants import (MAX_LEN_INGREDIENT_NAME,
                               MAX_LEN_MEASURMENT_UNIT, MAX_LEN_RECIPE_NAME,
                               MAX_LEN_TAG_NAME)
from users.models import User


class Tag(models.Model):
    """Модель для тегов."""

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
    """Модель для ингредиентов."""

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
    """Модель для рецептов."""

    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Тэг",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиент",
    )
    name = models.CharField(
        max_length=MAX_LEN_RECIPE_NAME,
        unique=True,
        verbose_name="Имя рецепта",
    )
    image = models.ImageField(
        upload_to="recipes/",
        verbose_name="Картинка",
        blank=True,
        null=True,
    )
    text = models.TextField(
        verbose_name="Текст рецепта"
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        verbose_name="Время приготовления",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
    )

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель соединяющая модель рецептов и ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredient",
        verbose_name="Рецепт",
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredient",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "рецепт-ингредиент"
        verbose_name_plural = "Рецепты-Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredients"],
                name="unique_recipe_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.ingredients.name} в {self.recipe.name}: {self.amount}"


class FavoriteShoppingCartFields(models.Model):
    """Модель с полями для Избранного и Списка покупок."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        verbose_name="Рецепт",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        verbose_name="Пользователь",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                name="unique_user_favorites"
            )
        ]
        abstract = True


class Favorite(FavoriteShoppingCartFields):
    """Модель избранного."""

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f"{self.recipe} в избранном {self.user}"


class ShoppingCart(FavoriteShoppingCartFields):
    """Модель списка покупок."""

    class Meta:
        verbose_name = "список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.recipe} в списке покупок {self.user}"
