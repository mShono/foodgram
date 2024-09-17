from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from .views import (CustomUserViewSet)

router = routers.DefaultRouter()
router.register("users", CustomUserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # path("admin/", admin.site.urls),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
