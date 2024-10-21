from djoser import views as djoser_views
from djoser import permissions as djoser_permissions
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from .filters import IngredientFilter
from .models import Tag, Ingredient, Recipe, RecipeIngredient
from .serializers import (
    UserSerializer, TagSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, RecipeIngredientSerializer,
    AvatarSerializer,
)
from users.models import CustomUser


class CustomUserViewSet(djoser_views.UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    @action(["put"], detail=False, url_path='me/avatar', url_name='upload-avatar')
    @permission_classes([IsAuthenticated])
    def upload_avatar(self, request):
        user = request.user
        if user.is_anonymous:
            return Response({"detail": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        serializer = AvatarSerializer(data=request.data, instance=user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @action(
    #     # methods=["get", "patch"],
    #     # detail=False,
    #     url_path="me/avatar",
    #     # url_name="users_detail",
    #     # permission_classes=(permissions.IsAuthenticated,),
    #     # serializer_class=UserSerializer,
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
