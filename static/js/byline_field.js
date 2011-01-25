(function($) {
	$.fn.bylineField = function() {
		this.each(function() {
			var bylineFieldElement = this;
			var bylineField = $(this);
			
			$('.byline_search input:submit', bylineFieldElement).hide();
			var searchField = $('.byline_search input:text', bylineFieldElement);
			var searchFieldElement = searchField.get(0);
			searchField.attr('autocomplete', 'off');
			
			searchField.focus(function() {
				$(this).addClass('focused');
			}).blur(function() {
				$(this).removeClass('focused');
			})
			
			var lookupRunning = false;
			var lastSearchTerm = searchField.val();
			var nextSearchTerm;
			var autocompleteNextSearchTerm;
			
			function cueLookup(autocomplete) {
				var value = searchField.val();
				if (lookupRunning) {
					nextSearchTerm = value;
					autocompleteNextSearchTerm = autocomplete
				} else {
					lookup(value, autocomplete);
				}
			}
			
			function lookup(value, autocomplete) {
				if (value.match(/\S/)) {
					if (value == lastSearchTerm) return;
					lookupRunning = true;
					/* TODO: consider caching results in a JS variable */
					$.getJSON('/nicks/byline_match/', {
						q: value,
						field_name: searchField.attr('name').replace(/_search$/, ''),
						autocomplete: autocomplete
					}, function(data) {
						if (searchField.val() == data['initial_query']) {
							/* only update fields if search box contents have not changed since making this query */
							$('.byline_match_container', bylineFieldElement).show().html(data.matches);
							$('.nick_match', bylineFieldElement).nickMatchWidget();
							if (autocomplete) {
								searchField.val(data.query);
								if (searchFieldElement.setSelectionRange) {
									searchFieldElement.setSelectionRange(data['initial_query'].length, data.query.length);
									/* TODO: IE compatibility */
								}
							}
							lastSearchTerm = data.query;
						}
						lookupRunning = false;
						if (nextSearchTerm) {
							lookup(nextSearchTerm, autocompleteNextSearchTerm);
							nextSearchTerm = null;
						}
					})
				} else {
					/* blank */
					lastSearchTerm = '';
					$('.byline_match_container', bylineFieldElement).html('').hide();
				}
			}
			
			searchField.blur(function() {
				cueLookup(false);
			}).keydown(function(e) {
				/* compare current field contents to new field contents to decide what to do about autocompletion */
				var oldValue = searchField.val();
				var selectionWasAtEnd = (searchFieldElement.selectionEnd == oldValue.length);
				var unselectedPortion = searchField.val().substring(0, searchFieldElement.selectionStart);
				
				setTimeout(function() {
					var newValue = searchField.val();
					if (oldValue == newValue) return;
					if (selectionWasAtEnd
						&& searchFieldElement.selectionStart == newValue.length /* no selection now */
						&& newValue.length == unselectedPortion.length + 1 /* new value is one letter longer */
						&& newValue.indexOf(unselectedPortion) == 0 /* old unselected portion is a prefix of new value */
					) {
						/* autocomplete */
						cueLookup(true);
					} else {
						/* have made some other change (e.g. deletion, pasting text); do not autocomplete */
						cueLookup(false);
					}
				}, 1);
			});
			
			if ($('.byline_match_container .nick_match', bylineFieldElement).length == 0) {
				$('.byline_match_container', bylineFieldElement).hide();
			}
			$(this).addClass('ajaxified');
		});
	}
})(jQuery);
