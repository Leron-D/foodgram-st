from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Класс кастомной пагинации для приложения"""

    page_query_param = 'page'
    page_size_query_param = 'limit'
    page_size = 6
    max_page_size = 100

    def get_page_number(self, request, paginator):
        """
        Метод, который устанавливает
        номер страницы по умолчанию,
        если он не указан
        """

        page_number = request.query_params.get(self.page_query_param) or 1
        return page_number