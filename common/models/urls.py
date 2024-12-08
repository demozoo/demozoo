from django.urls import reverse
from django.utils.functional import cached_property


class URLLookup:
    def __init__(self, routes, pk):
        self.routes = routes
        self.pk = pk

    def __getitem__(self, key):
        return reverse(self.routes[key], args=[self.pk])


class URLMixin:
    """
    Mixin to provide a dict-like `urls` property that can be used to look up URLs for a model instance.

    Models provide a `url_routes` dictionary that maps keys to URL route names, for example:
        url_routes = {
            "edit": "edit_party",
            "edit_notes": "party_edit_notes",
            "edit_external_links": "party_edit_external_links",
        }

    Accessing `party.urls["edit"]` will return the URL for the "edit_party" route, passing the instance's primary key
    as the sole argument.
    """

    url_routes = {}

    @cached_property
    def urls(self):
        return URLLookup(self.url_routes, self.pk)
