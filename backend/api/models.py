from django.db import models
from backend.constants import (MAX_LEN_NAME)


class Tag(models.Model):
    """Tag's model."""

    name = models.CharField("Название", max_length=MAX_LEN_NAME, unique=True)
    slug = models.SlugField(
        "Идентификатор",
        max_length=MAX_LEN_NAME,
        unique=True)
