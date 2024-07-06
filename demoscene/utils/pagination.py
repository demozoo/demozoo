from django.http import QueryDict

from laces.components import Component


def extract_query_params(query_dict, params):
    new_query_dict = QueryDict('', mutable=True)
    for param in params:
        if param in query_dict:
            new_query_dict.setlist(param, query_dict.getlist(param))

    return new_query_dict


class PageLink:
    def __init__(self, url=None, label=None, title=None, is_current=False):
        self.url = url
        self.label = label
        self.title = title
        self.is_current = is_current


class PaginationControls(Component):
    template_name = "shared/pagination_controls.html"

    def __init__(self, page, base_url, query_dict=None):
        self.page = page
        self.base_url = base_url
        self.query_dict = query_dict or QueryDict('')

    def get_page_url(self, page_num):
        new_query_dict = self.query_dict.copy()
        new_query_dict.setlist('page', [page_num])
        return "%s?%s" % (self.base_url, new_query_dict.urlencode())

    def get_context_data(self, parent_context=None):
        links = []
        if self.page.has_previous():
            links.append(
                PageLink(
                    url=self.get_page_url(self.page.previous_page_number()),
                    label="«",
                    title="Previous page",
                )
            )

        for page_num in self.page.paginator.get_elided_page_range(self.page.number):
            if isinstance(page_num, int):
                is_current_page = (page_num == self.page.number)
                links.append(
                    PageLink(
                        url=None if is_current_page else self.get_page_url(page_num),
                        label=str(page_num),
                        is_current=is_current_page,
                    )
                )
            else:
                links.append(
                    PageLink(
                        url=None,
                        label=str(page_num),
                    )
                )

        if self.page.has_next():
            links.append(
                PageLink(
                    url=self.get_page_url(self.page.next_page_number()),
                    label="»",
                    title="Next page",
                )
            )

        return {
            "links": links,
        }
