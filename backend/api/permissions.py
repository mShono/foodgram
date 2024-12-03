from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticatedOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        # # Разрешить безопасные методы (GET, HEAD, OPTIONS) всем
        if request.method in SAFE_METHODS:
            return True
        # # Проверка на аутентификацию для методов записи
        # return request.user and request.user.is_authenticated
        if not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")
        return True


class IsAuthenticatedAuthorOrReadOnly(BasePermission):
    """Разрешение на редактирование информации только автором или аутентифицированным пользователем или чтение"""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            raise NotAuthenticated("Учетные данные не были предоставлены.")
        return True

    def has_object_permission(self, request, view, obj):
        # return (
        #     request.method in SAFE_METHODS
        #     or obj.author == request.user
        # )
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
