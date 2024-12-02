from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Модифицированный пагинатор"""

    page_size_query_param = 'limit'
