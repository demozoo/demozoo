import re

from demoscene.fields import NickSearch, NickSelection
from demoscene.models import NickVariant


class BylineSearch:
    def __init__(self, search_term, author_nick_selections=[], affiliation_nick_selections=[], autocomplete=False):
        self.search_term = search_term

        # parse the byline
        parts = self.search_term.split("/")
        authors_string = parts[0]  # everything before first slash is an author
        affiliations_string = "^".join(parts[1:])  # everything after first slash is an affiliation

        # split on separators that have a trailing (and optionally leading) space
        author_names = re.split(r"\s*[\,\+\^\&]\s+", authors_string)
        author_names = [name.lstrip() for name in author_names if name.strip()]
        affiliation_names = re.split(r"\s*[\,\+\^\&]\s+", affiliations_string)
        affiliation_names = [name.lstrip() for name in affiliation_names if name.strip()]

        # Now, for any item in author_names or affiliation_names with an internal separator character,
        # perform a pre-check for that name. If not present, split it and move on.
        vetted_author_names = []
        for name in author_names:
            if re.search(r"[\,\+\^\&]", name) and not NickVariant.objects.filter(name__iexact=name.strip()).exists():
                for subname in re.split(r"[\,\+\^\&]", name):
                    subname = subname.lstrip()
                    if subname:
                        vetted_author_names.append(subname)
            else:
                vetted_author_names.append(name)

        vetted_affiliation_names = []
        for name in affiliation_names:
            if (
                re.search(r"[\,\+\^\&]", name)
                and not NickVariant.objects.filter(name__iexact=name.strip(), nick__releaser__is_group=True).exists()
            ):
                for subname in re.split(r"[\,\+\^\&]", name):
                    subname = subname.lstrip()
                    if subname:
                        vetted_affiliation_names.append(subname)
            else:
                vetted_affiliation_names.append(name)

        author_names = vetted_author_names
        affiliation_names = vetted_affiliation_names

        # attempt to autocomplete the last element of the name,
        # if autocomplete flag is True and search term has no trailing ,+^/& separator
        if autocomplete and not re.search(r"[\,\+\^\/\&]\s*$", self.search_term):
            if affiliation_names:
                autocompletion = NickVariant.autocomplete(
                    affiliation_names[-1], groups_only=True, member_names=[name.strip() for name in author_names]
                )
                affiliation_names[-1] += autocompletion
                self.search_term += autocompletion
            elif author_names:
                autocompletion = NickVariant.autocomplete(author_names[-1])
                author_names[-1] += autocompletion
                self.search_term += autocompletion

        author_names = [name.strip() for name in author_names]
        affiliation_names = [name.strip() for name in affiliation_names]

        # construct a NickSearch for each element
        self.author_nick_searches = []
        for i, author_name in enumerate(author_names):
            try:
                selection = author_nick_selections[i]
            except IndexError:
                selection = None
            self.author_nick_searches.append(NickSearch(author_name, selection, group_names=affiliation_names))

        self.affiliation_nick_searches = []
        for i, affiliation_name in enumerate(affiliation_names):
            try:
                selection = affiliation_nick_selections[i]
            except IndexError:
                selection = None
            self.affiliation_nick_searches.append(
                NickSearch(affiliation_name, selection, groups_only=True, member_names=author_names)
            )

        self.author_nick_selections = [nick_search.selection for nick_search in self.author_nick_searches]
        self.affiliation_nick_selections = [nick_search.selection for nick_search in self.affiliation_nick_searches]

    @property
    def author_matches_data(self):
        return [nick_search.match_data for nick_search in self.author_nick_searches]

    @property
    def affiliation_matches_data(self):
        return [nick_search.match_data for nick_search in self.affiliation_nick_searches]

    @staticmethod
    def from_byline(byline):
        return BylineSearch(
            search_term=str(byline),
            author_nick_selections=[NickSelection(nick.id, nick.name) for nick in byline.author_nicks],
            affiliation_nick_selections=[NickSelection(nick.id, nick.name) for nick in byline.affiliation_nicks],
        )
