from django.core.paginator import Paginator

def paginate(queue, per_page):
    paginator = Paginator(queue, per_page)

    for num in paginator.page_range:
        yield paginator.page(num)
