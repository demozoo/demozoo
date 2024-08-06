import datetime
import re

from demoscene.models import Nick, NickVariant, Releaser


# A placeholder for a Nick object, used as the cleaned value of a MatchedNickField
# and the value MatchedNickWidget returns from value_from_datadict.
# We can't use a Nick because we may not want to save it to the database yet (because
# the form might be failing validation elsewhere), and using an unsaved Nick object
# isn't an option either because we need to create a Releaser as a side effect, and
# Django won't let us build multi-object structures of unsaved models.
class NickSelection():
    def __init__(self, id, name):
        self.id = id
        self.name = name

    class FailedToResolve(Exception):
        pass

    def commit(self):
        if self.id == 'newscener':
            releaser = Releaser(name=self.name, is_group=False, updated_at=datetime.datetime.now())
            releaser.save()
            self.id = releaser.primary_nick.id
            return releaser.primary_nick
        elif self.id == 'newgroup':
            releaser = Releaser(name=self.name, is_group=True, updated_at=datetime.datetime.now())
            releaser.save()
            self.id = releaser.primary_nick.id
            return releaser.primary_nick
        else:
            try:
                return Nick.objects.get(id=self.id)
            except Nick.DoesNotExist:
                raise NickSelection.FailedToResolve(
                    "Tried to match the name '#{self.name}' to nick ID #{self.id} which does not exist"
                )

    def __str__(self):
        return self.name

    def __repr__(self):
        return "NickSelection: %s, %s" % (repr(self.id), self.name)

    def __eq__(self, other):
        if not isinstance(other, NickSelection):
            return False
        if self.id == 'newscener' and other.id == 'newscener' and self.name == other.name:
            return True
        elif self.id == 'newgroup' and other.id == 'newgroup' and self.name == other.name:
            return True

        try:
            return int(self.id) == int(other.id)
        except ValueError:  # respond with non-match if either id is non-numeric, i.e. 'newscener' or 'newgroup'
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class NickSearch():
    def __init__(
        self, search_term, selection=None,
        sceners_only=False, groups_only=False,
        group_ids=[],
        group_names=[], member_names=[],
        id_lookup=False,
    ):

        self.search_term = search_term

        nick_variants = NickVariant.autocompletion_search(
            search_term, exact=True,
            sceners_only=sceners_only, groups_only=groups_only,
            group_ids=group_ids,
            group_names=group_names, member_names=member_names)

        self.suggestions = []

        suggested_nick_ids = set()
        for nv in nick_variants:
            suggestion = {
                'className': ('group' if nv.nick.releaser.is_group else 'scener'),
                'nameWithAffiliations': nv.nick.name_with_affiliations(),
                'name': nv.nick.name,
                'id': nv.nick_id
            }
            if nv.nick.releaser.country_code:
                suggestion['countryCode'] = nv.nick.releaser.country_code.lower()

            if nv.nick.differentiator:
                suggestion['differentiator'] = nv.nick.differentiator
                suggestion['nameWithDifferentiator'] = "%s (%s)" % (nv.nick.name, nv.nick.differentiator)
            else:
                suggestion['nameWithDifferentiator'] = nv.nick.name

            if nv.nick.name != nv.name:
                suggestion['alias'] = nv.name

            self.suggestions.append(suggestion)

        has_id_lookup = False
        if id_lookup and search_term:
            id_to_look_up = None
            if search_term.isdigit():
                id_to_look_up = int(search_term)
            elif match := re.search(r'/(?:sceners|groups)/(\d+)/$', search_term):
                id_to_look_up = int(match.group(1))
            if id_to_look_up is not None:
                releaser_lookup_filters = {
                    'id': id_to_look_up,
                }
                if groups_only:
                    releaser_lookup_filters['is_group'] = True
                elif sceners_only:
                    releaser_lookup_filters['is_group'] = False
                try:
                    releaser = Releaser.objects.get(**releaser_lookup_filters)
                except Releaser.DoesNotExist:
                    pass
                else:
                    nicks = releaser.nicks.all()
                    ordered_nicks = sorted(nicks, key=lambda nick: (1 if nick.name == releaser.name else 2, nick.name))
                    for nick in ordered_nicks:
                        suggestion = {
                            'className': ('group' if releaser.is_group else 'scener'),
                            'nameWithAffiliations': nick.name_with_affiliations(),
                            'nameWithDifferentiator': nick.name,
                            'name': nick.name,
                            'id': nick.id
                        }
                        if releaser.country_code:
                            suggestion['countryCode'] = releaser.country_code.lower()
                        if nick.differentiator:
                            suggestion['differentiator'] = nick.differentiator
                            suggestion['nameWithDifferentiator'] = "%s (%s)" % (nick.name, nick.differentiator)
                        else:
                            suggestion['nameWithDifferentiator'] = nick.name

                        self.suggestions.append(suggestion)
                    has_id_lookup = True

        if not groups_only:
            self.suggestions.append({
                'className': 'add_scener',
                'nameWithAffiliations': "Add a new scener named '%s'" % search_term,
                'nameWithDifferentiator': search_term,
                'name': search_term,
                'id': 'newscener',
            })

        if not sceners_only:
            self.suggestions.append({
                'className': 'add_group',
                'nameWithAffiliations': "Add a new group named '%s'" % search_term,
                'nameWithDifferentiator': search_term,
                'name': search_term,
                'id': 'newgroup'
            })

        if selection:
            self.selection = selection
        else:
            nick_variant_count = len(nick_variants)
            # if there is a definite best-scoring nickvariant, select it
            if (
                nick_variant_count == 1
                or (nick_variant_count > 1 and nick_variants[0].score > nick_variants[1].score)
                or has_id_lookup
            ):
                self.selection = NickSelection(self.suggestions[0]['id'], self.suggestions[0]['nameWithDifferentiator'])
            else:
                self.selection = None

    @property
    def match_data(self):
        return {
            'choices': self.suggestions,
            'selection': {
                'id': (self.selection and self.selection.id),
                'name': self.search_term,
            }
        }


class BylineSearch():
    def __init__(
        self, search_term,
        author_nick_selections=[], affiliation_nick_selections=[],
        autocomplete=False
    ):

        self.search_term = search_term

        # parse the byline
        parts = self.search_term.split('/')
        authors_string = parts[0]  # everything before first slash is an author
        affiliations_string = '^'.join(parts[1:])  # everything after first slash is an affiliation

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
                    affiliation_names[-1],
                    groups_only=True, member_names=[name.strip() for name in author_names])
                affiliation_names[-1] += autocompletion
                self.search_term += autocompletion
            elif author_names:
                autocompletion = NickVariant.autocomplete(
                    author_names[-1])
                author_names[-1] += autocompletion
                self.search_term += autocompletion

        author_names = [name.strip() for name in author_names]
        affiliation_names = [name.strip() for name in affiliation_names]

        # construct a NickSearch for each element
        self.author_nick_searches = []
        for (i, author_name) in enumerate(author_names):
            try:
                selection = author_nick_selections[i]
            except IndexError:
                selection = None
            self.author_nick_searches.append(
                NickSearch(author_name, selection, group_names=affiliation_names)
            )

        self.affiliation_nick_searches = []
        for (i, affiliation_name) in enumerate(affiliation_names):
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
            affiliation_nick_selections=[NickSelection(nick.id, nick.name) for nick in byline.affiliation_nicks])
