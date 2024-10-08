from djoser import views as djoser_views
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from .filters import IngredientFilter
from .models import Tag, Ingredient, Recipe, RecipeIngredient
from .serializers import (
    CustomUserSerializer, TagSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, RecipeIngredientSerializer,
)
from users.models import CustomUser


class CustomUserViewSet(djoser_views.UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    # @action(
    #     # methods=["get", "patch"],
    #     # detail=False,
    #     url_path="me/avatar",
    #     # url_name="users_detail",
    #     # permission_classes=(permissions.IsAuthenticated,),
    #     # serializer_class=CustomUserSerializer,
    #     # subscribe
    # )


class TagViewSet(ReadOnlyModelViewSet):
    """Viewset for Tag model."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    # permission_classes = (IsAdminUserOrReadOnly,)
    # lookup_field = "slug"
    # filter_backends = (filters.SearchFilter,)
    # pagination_class = PageNumberPagination
    # search_fields = ("name",)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Viewset for Ingredient model."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Viewset for Ingredient model."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeReadSerializer, RecipeWriteSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', 'tags',)
    # filterset_fields = ('is_favorited', 'is_in_shopping_cart',)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer


class RecipeIngredientViewSet(ModelViewSet):
    """Viewset for Ingredient model."""

    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
