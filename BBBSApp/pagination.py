from rest_framework import pagination

class CustomPagination(pagination.PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    page_query_param = 'page'