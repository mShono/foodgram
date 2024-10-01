from djoser import views as djoser_views
from django.shortcuts import render
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from .models import Tag
from .serializers import CustomUserSerializer, TagSerializer
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
