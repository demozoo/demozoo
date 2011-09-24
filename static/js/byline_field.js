(function($) {
	$.fn.bylineField = function() {
		this.each(function() {
			var bylineFieldElement = this;
			var bylineField = $(this);
			var uid = $.uid('byline');
			
			$('.byline_search input:submit', bylineFieldElement).hide();
			var searchField = $('.byline_search input:text', bylineFieldElement);
			var searchFieldElement = searchField.get(0);
			searchField.attr('autocomplete', 'off');
			
			searchField.typeahead(function(value, autocomplete) {
				if (value.match(/\S/)) {
					$.ajaxQueue(uid, function(release) {
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
							}
							release();
						})
					})
				} else {
					/* blank */
					$('.byline_match_container', bylineFieldElement).html('').hide();
				}
			});
			
			if ($('.byline_match_container .nick_match', bylineFieldElement).length == 0) {
				$('.byline_match_container', bylineFieldElement).hide();
			}
			$(this).addClass('ajaxified');
		});
	}
})(jQuery);
