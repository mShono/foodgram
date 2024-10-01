from django.db import models
from backend.constants import (
    MAX_LEN_TAG_NAME, MAX_LEN_INGREDIENT_NAME, MAX_LEN_MEASURMENT_UNIT
)


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
