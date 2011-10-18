(function($) {
	$.fn.bylineField = function() {
		this.each(function() {
			var context = this;
			var searchField = $('.byline_search > input:text', context);
			var bylineFieldPrefix = searchField.attr('name').replace(/search$/, '');
			
			var bylineMatchContainer = $('.byline_match_container', context);
			var authorMatches = [];
			var affiliationMatches = [];
			
			bylineMatchContainer.children().each(function() {
				var matchData = $(this).extractNickMatchData();
				if (matchData.fieldPrefix.match('^'+bylineFieldPrefix+'author_')) {
					authorMatches.push(matchData);
				} else {
					affiliationMatches.push(matchData);
				}
			})
			
			BylineField(context, searchField.val(),
				authorMatches, affiliationMatches, bylineFieldPrefix);
		});
	}
})(jQuery);

function BylineField(elem, searchTerm, authorMatches, affiliationMatches, fieldPrefix) {
	var self = {};
	var $elem = $(elem);
	
	$elem.empty();
	var searchContainer = $('<div class="byline_search"></div>');
	var searchField = $('<input type="text" />').attr({
		'name': fieldPrefix + 'search',
		'id': 'id_' + fieldPrefix + 'search',
		'value': searchTerm,
		'autocomplete': 'off'
	});
	searchContainer.append(searchField);
	$elem.append(searchContainer);
	var searchFieldElement = searchField.get(0);
	
	var bylineMatchContainer = $('<div class="byline_match_container"></div>');
	$elem.append(bylineMatchContainer);
	
	function populateMatches(authorMatches, affiliationMatches) {
		bylineMatchContainer.empty();
		if (authorMatches.length || affiliationMatches.length) {
			bylineMatchContainer.show();
			for (var i = 0; i < authorMatches.length; i++) {
				var nickMatch = $('<div class="nick_match"></div>');
				bylineMatchContainer.append(nickMatch);
				NickMatchWidget(
					nickMatch, authorMatches[i].selection, authorMatches[i].choices,
					fieldPrefix + 'author_match_' + i + '_');
			}
			for (var i = 0; i < affiliationMatches.length; i++) {
				var nickMatch = $('<div class="nick_match"></div>');
				bylineMatchContainer.append(nickMatch);
				NickMatchWidget(
					nickMatch, affiliationMatches[i].selection, affiliationMatches[i].choices,
					fieldPrefix + 'affiliation_match_' + i + '_');
			}
		} else {
			bylineMatchContainer.hide();
		}
	}
	
	populateMatches(authorMatches, affiliationMatches);
	
	var uid = $.uid('byline');
	
	searchField.typeahead(function(value, autocomplete) {
		if (value.match(/\S/)) {
			$.ajaxQueue(uid, function(release) {
				/* TODO: consider caching results in a JS variable */
				$.getJSON('/nicks/byline_match/', {
					q: value,
					autocomplete: autocomplete
				}, function(data) {
					if (searchField.val() == data['initial_query']) {
						/* only update fields if search box contents have not changed since making this query */
						populateMatches(data.author_matches, data.affiliation_matches);
						if (autocomplete) {
							searchField.val(data.query);
							if (searchFieldElement.setSelectionRange) {
								searchFieldElement.setSelectionRange(data['initial_query'].length, data.query.length);
								/* TODO: IE compatibility */
							}
						}
					}
					release();
				})
			})
		} else {
			/* blank */
			populateMatches([], []);
		}
	});
}
