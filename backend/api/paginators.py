from rest_framework.pagination import PageNumberPagination


class PageAndLimitPagination(PageNumberPagination):
    page_size_query_param = "limit"
    page_size = 6

    def get_paginated_response(self, data):
        return super().get_paginated_response(data)
