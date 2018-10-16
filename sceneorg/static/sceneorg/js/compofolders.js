$(function() {
	constructMatchingInterface({
		'initLeftButton': function() {
			var directoryId = this.value;

			$(this).wrap('<div class="button_wrapper"></div>');
			var expandButton = $('<button class="expand" title="Show contents">expand</button>');
			var expandPanel = $('<div class="details"></div>').hide();
			$(this).after(expandButton, expandPanel);
			expandButton.click(function() {
				if (expandPanel.is(':visible')) {
					expandPanel.slideUp();
				} else {
					expandPanel.load('/sceneorg/compofolders/directory/' + directoryId + '/', function() {
						expandPanel.slideDown();
					});
				}
			});
		},
		'initRightButton': function() {
			var competitionId = this.value;

			$(this).wrap('<div class="button_wrapper"></div>');
			var expandButton = $('<button class="expand" title="Show contents">expand</button>');
			var expandPanel = $('<div class="details"></div>').hide();
			$(this).after(expandButton, expandPanel);
			expandButton.click(function() {
				if (expandPanel.is(':visible')) {
					expandPanel.slideUp();
				} else {
					expandPanel.load('/sceneorg/compofolders/competition/' + competitionId + '/', function() {
						expandPanel.slideDown();
					});
				}
			});
		},
		'leftSelector': 'button.directory',
		'rightSelector': 'button.competition',
		'unlinkAction': function(leftVal, rightVal) {
			$.ajax({
				type: 'POST',
				url: '/sceneorg/compofolders/unlink/',
				data: {'directory_id': leftVal, 'competition_id': rightVal},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		},
		'leftListSelector': 'ul.unmatched_directories',
		'rightListSelector': 'ul.unmatched_competitions',
		'linkAction': function(leftVal, rightVal) {
			/* post the ID pair to the server */
			$.ajax({
				type: 'POST',
				url: '/sceneorg/compofolders/link/',
				data: {'directory_id': leftVal, 'competition_id': rightVal},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		}
	});
});
