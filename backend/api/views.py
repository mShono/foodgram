import io

import short_url
from django.db.models import BooleanField, Case, Count, Sum, Value, When
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Tag)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .paginators import PageAndLimitPagination
from .permissions import IsAuthenticatedAuthorOrReadOnly
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeIngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          TagSerializer, UserSerializer)


class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет для модели Пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageAndLimitPagination
    permission_classes = [IsAuthenticatedAuthorOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if "recipes_limit" in self.request.query_params:
            recipes_limit = int(self.request.query_params["recipes_limit"])
            context["recipes_limit"] = recipes_limit
        return context

    def get_permissions(self):
        if self.action == "get_me":
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        ["put", "delete"],
        detail=False,
        url_path="me/avatar",
        url_name="upload-avatar"
    )
    def manage_avatar(self, request):
        user = request.user
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

    @action(
        ["get"],
        detail=False,
        url_path="me",
        url_name="current_user",
    )
    def get_me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        ["post", "delete"],
        detail=True,
        url_path="subscribe",
        url_name="subscribe"
    )
    def manage_subscriptions(self, request, id=None):
        user = request.user
        if request.method == "POST":
            try:
                followee = get_object_or_404(User, id=id)
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
                data={"subscribed_to": followee.id},
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            annotated_subscription = Subscription.objects.filter(
                id=subscription.id
            ).annotate(
                recipes_count=Count("subscribed_to__recipes")
            ).first()
            response_serializer = SubscriptionSerializer(
                annotated_subscription,
                context=self.get_serializer_context()
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        if request.method == "DELETE":
            deleted_count, _ = Subscription.objects.filter(
                subscriber=user,
                subscribed_to=get_object_or_404(User, id=id)
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
        url_name="subscriptions",
        permission_classes=[IsAuthenticated]
    )
    def show_subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(
            subscriber=user
        ).select_related(
            "subscribed_to"
        ).annotate(
            recipes_count=Count("subscribed_to__recipes")
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


def manage_recipe_action(
    request, model, serializer_class,
    user, recipe_id, error_message, delete_message
):
    """Добавление/удаление рецепта в избранное или корзину."""
    recipe = get_object_or_404(Recipe, id=recipe_id)

    if request.method == "POST":
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = serializer_class(
            data={"recipe": recipe.id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == "DELETE":
        deleted_count, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted_count == 0:
            return Response(
                {"detail": delete_message},
                status=status.HTTP_400_BAD_REQUEST
            )
    return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Ingredient."""

    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'tags', 'ingredients'
    )
    serializer_class = (RecipeReadSerializer, RecipeWriteSerializer,)
    permission_classes = [IsAuthenticatedAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageAndLimitPagination

    def get_queryset(self):
        """Аннотирование полей is_favorited и is_in_shopping_cart."""
        user = self.request.user
        queryset = super().get_queryset()
        if not user.is_authenticated:
            return queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField())
            )
        return queryset.annotate(
            is_favorited=Case(
                When(recipe_favorite_related__user=user, then=True),
                default=False,
                output_field=BooleanField()
            ),
            is_in_shopping_cart=Case(
                When(recipe_shoppingcart_related__user=user, then=True),
                default=False,
                output_field=BooleanField()
            )
        )

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        ["post", "delete"],
        detail=True,
        url_path="favorite",
    )
    def manage_favorites(self, request, pk=None):
        return manage_recipe_action(
            request=request,
            model=Favorite,
            serializer_class=FavoriteSerializer,
            user=request.user,
            recipe_id=pk,
            error_message="Этот рецепт уже есть в избранном.",
            delete_message="Этого рецепта не было в избранном."
        )

    @action(
        ["post", "delete"],
        detail=True,
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def manage_shopping_cart(self, request, pk=None):
        return manage_recipe_action(
            request=request,
            model=ShoppingCart,
            serializer_class=ShoppingCartSerializer,
            user=request.user,
            recipe_id=pk,
            error_message="Этот рецепт уже есть в списке покупок.",
            delete_message="Этого рецепта не было в списке покупок."
        )

    @staticmethod
    def generate_shopping_cart_file(ingredients):
        """Генерация содержимое файла для списка покупок."""
        buffer = io.BytesIO()
        for ingredient in ingredients:
            name_measurement_unit = (
                f"{ingredient['ingredients__name']} "
                f"({ingredient['ingredients__measurement_unit']})"
            )
            buffer.write(
                (
                    f"{name_measurement_unit}: {ingredient['total_amount']}\n"
                ).encode('utf-8')
            )
        buffer.seek(0)
        return buffer

    @action(
        ["get"],
        detail=False,
        url_path="download_shopping_cart",
        url_name="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response(
                {"detail": "Список покупок пуст."},
                status=status.HTTP_400_BAD_REQUEST
            )
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__recipe_shoppingcart_related__user=user
            )
            .values(
                "ingredients__name",
                "ingredients__measurement_unit",
            ).annotate(total_amount=Sum("amount"))
        )
        file_content = self.generate_shopping_cart_file(ingredients)
        return HttpResponse(
            file_content.getvalue(),
            content_type="text/plain",
            headers={
                "Content-Disposition": "attachment; filename=shopping_cart.txt"
            }
        )

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
