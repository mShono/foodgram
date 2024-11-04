import csv

from djoser import views as djoser_views
from djoser import permissions as djoser_permissions
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, render
from rest_framework import filters, mixins, permissions, status
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, AllowAny
from rest_framework.response import Response
from .filters import IngredientFilter
from .models import (
    Tag, Ingredient, Recipe, RecipeIngredient, Subscription, Favorite,
    ShoppingCart
)
from .serializers import (
    UserSerializer, TagSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, RecipeIngredientSerializer,
    AvatarSerializer, CustomSetPasswordSerializer, SubscriptionSerializer,
    FavoriteSerializer, ShoppingCartSerializer
)
from .permissions import IsAdminUserOrReadOnly
from users.models import CustomUser


class CustomUserViewSet(djoser_views.UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    @action(["post"], detail=False)
    @permission_classes([IsAuthenticated])
    def set_password(self, request, *args, **kwargs):
        user = request.user
        serializer = CustomSetPasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


    @action(["put", "delete"], detail=False, url_path="me/avatar", url_name="upload-avatar")
    def manage_avatar(self, request):
        user = request.user
        if user.is_anonymous:
            return Response({"detail": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        if request.method == "PUT":
            serializer = AvatarSerializer(data=request.data, instance=user)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if request.method == "DELETE":
            user.avatar.delete()
            user.save()
            return Response({"detail": "Аватар успешно удалён."}, status=status.HTTP_204_NO_CONTENT)

    @action(["get"], detail=False, url_path="me", url_name="current_user")
    @permission_classes([IsAuthenticated])
    def get_me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(["post", "delete"], detail=True, url_path="subscribe", url_name="subscribe")
    def manage_subscriptions(self, request, id=None):
        user = request.user
        try:
            followee = get_object_or_404(CustomUser, id=id)
        except Http404:
            return Response({"detail": "Страница не найдена."}, status=status.HTTP_404_NOT_FOUND)
        if request.method == "POST":
            if user.is_anonymous:
                return Response({"detail": "Учетные данные не были предоставлены."}, status=status.HTTP_401_UNAUTHORIZED)
            elif user == followee:
                return Response({'detail': 'Вы не можете подписаться на самого себя.'}, status=status.HTTP_400_BAD_REQUEST)
            elif Subscription.objects.filter(subscriber=user, subscribed_to=followee).exists():
                return Response({'detail': 'Вы уже подписаны на этого автора.'}, status=status.HTTP_400_BAD_REQUEST)
            subscription = Subscription.objects.create(subscriber=user, subscribed_to=followee)
            serializer = SubscriptionSerializer(subscription, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            subscription = Subscription.objects.filter(subscriber=user, subscribed_to=followee) #.first()
            if not subscription:
                return Response(
                    {"detail": "Вы уже отписались этого автора."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], detail=False, url_path="subscriptions", url_name="subscriptions")
    @permission_classes([IsAuthenticated])
    def show_subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(subscriber=user)
        serializer = SubscriptionSerializer(subscriptions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(ModelViewSet):
    """Viewset for Tag model."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    # lookup_field = "slug"
    # filter_backends = (filters.SearchFilter,)
    # pagination_class = PageNumberPagination
    # search_fields = ("name",)


class IngredientViewSet(ModelViewSet):
    """Viewset for Ingredient model."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Viewset for Ingredient model."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeReadSerializer, RecipeWriteSerializer
    permission_classes = [AllowAny]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("author", "tags",)
    # filterset_fields = ('is_favorited', 'is_in_shopping_cart',)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(["post", "delete"], detail=True, url_path="favorite", url_name="favorite")
    def manage_favorites(self, request, pk=None):
        user = request.user
        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response({"detail": "Страница не найдена."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_anonymous:
            return Response({"detail": "Учетные данные не были предоставлены."}, status=status.HTTP_401_UNAUTHORIZED)
        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'detail': 'Этот рецепт уже есть в избранном.'}, status=status.HTTP_400_BAD_REQUEST)
            favorite_obj = Favorite.objects.create(user=user, recipe=recipe)
            serializer = FavoriteSerializer(favorite_obj, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            favorite_obj = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite_obj:
                return Response(
                    {"detail": "Этого рецепта не было в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_obj.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post", "delete"], detail=True, url_path="shopping_cart", url_name="shopping_cart")
    def manage_shopping_cart(self, request, pk=None):
        user = request.user
        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response({"detail": "Страница не найдена."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_anonymous:
            return Response({"detail": "Учетные данные не были предоставлены."}, status=status.HTTP_401_UNAUTHORIZED)
        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({'detail': 'Этот рецепт уже есть в списке покупок.'}, status=status.HTTP_400_BAD_REQUEST)
            shopping_cart_obj = ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartSerializer(shopping_cart_obj, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            shopping_cart_obj = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not shopping_cart_obj:
                return Response(
                    {"detail": "Этого рецепта не было в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart_obj.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], detail=False, url_path="download_shopping_cart", url_name="download_shopping_cart", permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        if not shopping_cart:
            return Response({"detail": "Список покупок пуст."}, status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(
            content_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=shopping_cart.txt"}
        )
        ingredients = {}
        for item in shopping_cart:
            for recipe_ingredient in item.recipe.recipe_ingredient.all():
                ingredient_name = recipe_ingredient.ingredients.name
                ingredient_amount = recipe_ingredient.amount
                ingredient_measurement_unit = recipe_ingredient.ingredients.measurement_unit
                name_measurement_unit = f'{ingredient_name} ({ingredient_measurement_unit})'
                if name_measurement_unit in ingredients:
                    ingredients[name_measurement_unit] += ingredient_amount
                else:
                    ingredients[name_measurement_unit] = ingredient_amount
        response.write("Список покупок:\n\n")
        for name_measurement_unit, amount in ingredients.items():
            response.write(f"{name_measurement_unit}: {amount}\n")
        return response


class RecipeIngredientViewSet(ModelViewSet):
    """Viewset for Ingredient model."""

    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
