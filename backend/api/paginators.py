from backend.constants import PAGE_SIZE
from rest_framework.pagination import PageNumberPagination


class PageAndLimitPagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_size = PAGE_SIZE
