from rest_framework.permissions import SAFE_METHODS, BasePermission


# class IsAdminUser(BasePermission):
#     """Разрешение на редактирование информации только администратором"""

#     def has_permission(self, request, view):
#         return (
#             request.user
#             and request.user.is_authenticated
#             and request.user.is_admin
#         )


class IsAdminUserOrReadOnly(BasePermission):
    """Разрешение на редактирование информации только администратором
    или чтение
    """

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
