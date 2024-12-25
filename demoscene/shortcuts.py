from django.core.paginator import EmptyPage, InvalidPage, Paginator


def get_page(queryset, page_number, **kwargs):
    count = kwargs.get("count", 50)

    paginator = Paginator(queryset, count)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(page_number)
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        return paginator.page(page)
    except (EmptyPage, InvalidPage):
        return paginator.page(paginator.num_pages)
