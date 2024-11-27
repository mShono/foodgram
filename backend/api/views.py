import short_url
from django.db.models import Count, Prefetch
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from rest_framework import status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from users.models import CustomUser, Subscription

from .filters import IngredientFilter, RecipeFilter
from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Tag)
from .serializers import (AvatarSerializer,
                          FavoriteSerializer, IngredientSerializer,
                          RecipeIngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserSerializer)
from .paginators import PageAndLimitPagination


class CustomUserViewSet(djoser_views.UserViewSet):
    """Вьюсет для модели CustomUser."""

    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageAndLimitPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if "recipes_limit" in self.request.query_params:
            recipes_limit = int(self.request.query_params["recipes_limit"])
            context["recipes_limit"] = recipes_limit
        return context

    @action(
        ["put", "delete"],
        detail=False,
        url_path="me/avatar",
        url_name="upload-avatar"
    )
    def manage_avatar(self, request):
        user = request.user
        if user.is_anonymous:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.method == "PUT":
            serializer = AvatarSerializer(data=request.data, instance=user)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == "DELETE":
            user.avatar.delete()
            return Response(
                {"detail": "Аватар успешно удалён."},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(["get"], detail=False, url_path="me", url_name="current_user")
    @permission_classes([IsAuthenticated])
    def get_me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        ["post", "delete"],
        detail=True,
        url_path="subscribe",
        url_name="subscribe"
    )
    def manage_subscriptions(self, request, id=None):
        user = request.user
        if user.is_anonymous:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.method == "POST":
            try:
                followee = get_object_or_404(CustomUser, id=id)
            except Http404:
                return Response(
                    {"detail": "Страница не найдена."},
                    status=status.HTTP_404_NOT_FOUND
                )
            if user == followee:
                return Response(
                    {"detail": "Вы не можете подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif Subscription.objects.filter(
                subscriber=user,
                subscribed_to=followee
            ).exists():
                return Response(
                    {"detail": "Вы уже подписаны на этого автора."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                 data={"subscriber": user.id, "subscribed_to": followee.id},
                 context=self.get_serializer_context()
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            followee = get_object_or_404(CustomUser, id=id)
            deleted_count, _ = Subscription.objects.filter(
                subscriber=user,
                subscribed_to=followee
            ).delete()
            if deleted_count == 0:
                return Response(
                    {"detail": "Вы уже отписались этого автора."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ["get"],
        detail=False,
        url_path="subscriptions",
        url_name="subscriptions"
    )
    @permission_classes([IsAuthenticated])
    def show_subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(subscriber=user).select_related(
            "subscribed_to"
        ).annotate(
            recipes_count=Count("subscribed_to__recipes")
        ).prefetch_related(
            Prefetch(
                "subscribed_to__recipes",
                queryset=Recipe.objects.only("id", "name", "image", "cooking_time")
            )
        )
        paginator = self.pagination_class()
        paginated_subscriptions = paginator.paginate_queryset(
            subscriptions,
            request
        )
        serializer = SubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context=self.get_serializer_context()
        )
        return paginator.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    filter_backends = (DjangoFilterBackend,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Ingredient."""

    queryset = Recipe.objects.all()
    serializer_class = (RecipeReadSerializer, RecipeWriteSerializer,)
    permission_classes = [AllowAny]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageAndLimitPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def destroy(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        recipe = get_object_or_404(Recipe, id=kwargs["pk"])
        if recipe.author != request.user:
            return Response(
                {
                    "detail": (
                        "У вас недостаточно прав для выполнения "
                        "данного действия."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(
        ["post", "delete"],
        detail=True,
        url_path="favorite",
    )
    def manage_favorites(self, request, pk=None):
        user = request.user
        if user.is_anonymous:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Этот рецепт уже есть в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_obj = Favorite.objects.create(user=user, recipe=recipe)
            serializer = FavoriteSerializer(
                favorite_obj,
                context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            deleted_count, _ = Favorite.objects.filter(
                user=user, recipe=recipe
            ).delete()
            if deleted_count == 0:
                return Response(
                    {"detail": "Этого рецепта не было в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)


    @action(
        ["post", "delete"],
        detail=True,
        url_path="shopping_cart",
        url_name="shopping_cart"
    )
    def manage_shopping_cart(self, request, pk=None):
        user = request.user
        if user.is_anonymous:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Этот рецепт уже есть в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart_obj = ShoppingCart.objects.create(
                user=user,
                recipe=recipe
            )
            serializer = ShoppingCartSerializer(
                shopping_cart_obj,
                context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            deleted_count, _ = ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).delete()
            if deleted_count == 0:
                return Response(
                    {"detail": "Этого рецепта не было в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        ["get"],
        detail=False,
        url_path="download_shopping_cart",
        url_name="download_shopping_cart",
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        if not shopping_cart:
            return Response(
                {"detail": "Список покупок пуст."},
                status=status.HTTP_400_BAD_REQUEST
            )
        response = HttpResponse(
            content_type="text/plain",
            headers={
                "Content-Disposition": "attachment; filename=shopping_cart.txt"
            }
        )
        ingredients = {}
        for item in shopping_cart:
            for recipe_ingredient in item.recipe.recipe_ingredient.all():
                ingredient_name = recipe_ingredient.ingredients.name
                ingredient_amount = recipe_ingredient.amount
                ingredient_measurement_unit = (
                    recipe_ingredient.ingredients.measurement_unit
                )
                name_measurement_unit = (
                    f"{ingredient_name} ({ingredient_measurement_unit})"
                )
                if name_measurement_unit in ingredients:
                    ingredients[name_measurement_unit] += ingredient_amount
                else:
                    ingredients[name_measurement_unit] = ingredient_amount
        response.write("Список покупок:\n\n")
        for name_measurement_unit, amount in ingredients.items():
            response.write(f"{name_measurement_unit}: {amount}\n")
        return response

    @action(
        ["get"],
        detail=True,
        url_path="get-link",
        url_name="get_link",
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_id = short_url.encode_url(recipe.id)

        short_link = request.build_absolute_uri(
            reverse("short_recipe_link", args=[short_id])
        )
        return Response({"short-link": short_link})


class RecipeIngredientViewSet(ModelViewSet):
    """Вьюсет для модели RecipeIngredient."""

    queryset = RecipeIngredient.objects.all()
    serializer_class = RecipeIngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
