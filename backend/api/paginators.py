from rest_framework.pagination import PageNumberPagination

from backend.constants import PAGE_SIZE


class PageAndLimitPagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_size = PAGE_SIZE
