from djoser import views as djoser_views
from django.shortcuts import render
from rest_framework.decorators import action
from .serializers import CustomUserSerializer
from users.models import CustomUser

class CustomUserViewSet(djoser_views.UserViewSet):
    queryset = CustomUser.objects.all
    serializer_class = CustomUserSerializer

    @action(
        # methods=["get", "patch"],
        # detail=False,
        url_path="me/avatar",
        # url_name="users_detail",
        # permission_classes=(permissions.IsAuthenticated,),
        # serializer_class=CustomUserSerializer,
        # subscribe
    )