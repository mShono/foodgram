from django.urls import include, path
from rest_framework import routers

from .views import (
    CustomUserViewSet, TagViewSet, IngredientViewSet, RecipeViewSet,
)

router = routers.DefaultRouter()
router.register("users", CustomUserViewSet)
router.register("tags", TagViewSet)
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet, basename='recipe')

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
