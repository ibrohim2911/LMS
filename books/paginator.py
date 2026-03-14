from rest_framework.pagination import PageNumberPagination

class KitobPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Allow client to set page size with ?page_size=
    max_page_size = 50  # Maximum page size to prevent abuse
class ReservationPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50