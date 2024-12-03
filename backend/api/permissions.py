from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticatedAuthorOrReadOnly(BasePermission):
    """
    Разрешение на редактирование информации только автором
    или аутентифицированным пользователем или чтение
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            raise NotAuthenticated("Учетные данные не были предоставлены.")
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
