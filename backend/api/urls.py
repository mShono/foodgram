import short_url
from django.shortcuts import redirect
from django.urls import include, path
from rest_framework import routers

from .views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet)


def redirect_to_recipe(request, short_id):
    recipe_id = short_url.decode_url(short_id)
    return redirect('recipe-detail', pk=recipe_id)


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
