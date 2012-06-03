from demoscene.models import NickVariant, Releaser, Nick
import datetime
import re


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
			return Nick.objects.get(id=self.id)

	def __str__(self):
		return self.name

	def __repr__(self):
		return "NickSelection: %s, %s" % (repr(self.id), self.name)

	def __eq__(self, other):
		if not isinstance(other, NickSelection):
			return False
		if self.id == 'newscener' and other.id == 'newscener' and self.name == other.name:
			return True
		if self.id == 'newgroup' and other.id == 'newgroup' and self.name == other.name:
			return True
		return int(self.id) == int(other.id)

	def __ne__(self, other):
		return not self.__eq__(other)


class NickSearch():
	def __init__(self, search_term, selection=None,
		sceners_only=False, groups_only=False,
		group_names=[], member_names=[]):

		self.search_term = search_term

		nick_variants = NickVariant.autocompletion_search(
			search_term, exact=True,
			sceners_only=sceners_only, groups_only=groups_only,
			groups=group_names, members=member_names)

		self.suggestions = []

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
			# if there is a definite best-scoring nickvariant, select it
			if nick_variants.count() == 0:
				self.selection = None
			elif nick_variants.count() == 1 or nick_variants[0].score > nick_variants[1].score:
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
	def __init__(self, search_term,
		author_nick_selections=[], affiliation_nick_selections=[],
		autocomplete=False):

		self.search_term = search_term

		# parse the byline
		parts = self.search_term.split('/')
		authors_string = parts[0]  # everything before first slash is an author
		affiliations_string = '^'.join(parts[1:])  # everything after first slash is an affiliation
		author_names = re.split(r"[\,\+\^\&]", authors_string)
		author_names = [name.lstrip() for name in author_names if name.strip()]
		affiliation_names = re.split(r"[\,\+\^\&]", affiliations_string)
		affiliation_names = [name.lstrip() for name in affiliation_names if name.strip()]

		# attempt to autocomplete the last element of the name,
		# if autocomplete flag is True and search term has no trailing ,+^/& separator
		if autocomplete and not re.search(r"[\,\+\^\/\&]\s*$", self.search_term):
			if affiliation_names:
				autocompletion = NickVariant.autocomplete(
					affiliation_names[-1],
					significant_whitespace=False,
					groups_only=True, members=[name.strip() for name in author_names])
				affiliation_names[-1] += autocompletion
				self.search_term += autocompletion
			elif author_names:
				autocompletion = NickVariant.autocomplete(
					author_names[-1],
					significant_whitespace=False)
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
			search_term=byline.__unicode__(),
			author_nick_selections=[NickSelection(nick.id, nick.name) for nick in byline.author_nicks],
			affiliation_nick_selections=[NickSelection(nick.id, nick.name) for nick in byline.affiliation_nicks])
