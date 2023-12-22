from rest_framework.pagination import PageNumberPagination


class MomentPagination(PageNumberPagination):

    page_size = 1000
    page_size_query_param = 'page_size'
    page_query_param = 'page'
    max_page_size = 100
