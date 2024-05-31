from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    page_size = 1000
    # 为了跟ant design保持一致，减少代码量
    page_size_query_param = 'pageSize'
    page_query_param = 'current'
    max_page_size = 100


class MomentPagination(DefaultPagination):
    pass


class ThingPagination(DefaultPagination):
    pass
