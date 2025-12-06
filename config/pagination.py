from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """
    Default pagination class.

    This pagination strategy uses page-number based navigation, which is
    intuitive for client applications and efficient for most API endpoints.
    Clients can request a custom page size by using the `page_size` query
    parameter, while the server enforces an upper limit to prevent excessive
    payloads.

    Behavior:
        - `page_size`: Default number of results per page.
        - `page_size_query_param`: Allows clients to override the default size.
        - `max_page_size`: Safety limit to avoid expensive or abusive queries.

    This pagination class is recommended for list endpoints that expose
    database-backed resources such as items, invoices, transactions, and users.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 1000
