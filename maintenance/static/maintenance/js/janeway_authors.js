$(function() {
	$('li.match').each(function() {
		var li = this;
		var demozooId = $(li).data('demozoo-id');
		var janewayId = $(li).data('janeway-id');

		var sameButton = $('<button>same</button>');
		sameButton.click(function() {
			$.post('janeway_unique_author_name_matches/same/' + demozooId + '/' + janewayId + '/', {
				'csrfmiddlewaretoken': $.cookie('csrftoken')
			}, function() {
				$(li).fadeOut();
			});
		});

		var differentButton = $('<button>different</button>');
		differentButton.click(function() {
			$.post('janeway_unique_author_name_matches/different/' + demozooId + '/' + janewayId + '/', {
				'csrfmiddlewaretoken': $.cookie('csrftoken')
			}, function() {
				$(li).fadeOut();
			});
		});

		$('a.info-link', li).click(function() {
			var infoPanel = $('.info-panel', li);
			if (!infoPanel.length) {
				infoPanel = $('<div class="info-panel" style="border: 1px solid #888; padding: 10px;"></div>');
				$(li).append(infoPanel);
			}
			infoPanel.load(this.href);
			return false;
		});

		$(li).append(sameButton, differentButton);
	});
});
