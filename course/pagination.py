from rest_framework.pagination import CursorPagination, PageNumberPagination


class CoursePagination(CursorPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 50
    ordering = ('-student_count', '-id')


class SearchRelevancePagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 50
