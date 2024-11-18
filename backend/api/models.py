from django.db import models

from backend.constants import (MAX_LEN_INGREDIENT_NAME,
                               MAX_LEN_MEASURMENT_UNIT, MAX_LEN_RECIPE_NAME,
                               MAX_LEN_TAG_NAME)
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
    """The model connecting Recipe and Ingredient models."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredient",
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

    class Meta:
        verbose_name = "рецепт-ингредиент"
        verbose_name_plural = "Рецепты-Ингредиенты"

    def __str__(self):
        return f"{self.ingredients.name} в {self.recipe.name}: {self.amount}"


class Subscription(models.Model):
    """Subscription's model."""

    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Подписчик",
    )
    subscribed_to = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="followees",
        verbose_name="Блогер",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "subscribed_to"],
                name="unique_user_following"
            )
        ]
        default_related_name = "subscriptions"
        verbose_name = "подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.subscriber} на {self.subscribed_to}"


class Favorite(models.Model):
    """Favorite's model."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                name="unique_user_favorites"
            )
        ]
        verbose_name = "избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f"{self.recipe} в избранном {self.user}"


class ShoppingCart(models.Model):
    """Shopping Cart's model."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shoppingcart",
        verbose_name="Рецепт",
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="shoppingcart",
        verbose_name="Пользователь",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                name="unique_user_shoppingcart"
            )
        ]
        verbose_name = "список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.recipe} в списке покупок {self.user}"
