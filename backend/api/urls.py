import short_url
from django.shortcuts import get_object_or_404, redirect
from django.urls import include, path
from rest_framework import routers

from .models import Recipe
from .views import (
    CustomUserViewSet, TagViewSet, IngredientViewSet, RecipeViewSet,
)


def redirect_to_recipe(request, short_id):
    # Декодируем ID из короткого URL
    recipe_id = short_url.decode_url(short_id)
    # recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect('recipe-detail', pk=recipe_id)  # 'recipe-detail' - это URL name для детальной страницы рецепта


router = routers.DefaultRouter()
router.register("users", CustomUserViewSet)
router.register("tags", TagViewSet)
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet, basename='recipe')

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path('r/<str:short_id>/', redirect_to_recipe, name='short_recipe_link'),
]
