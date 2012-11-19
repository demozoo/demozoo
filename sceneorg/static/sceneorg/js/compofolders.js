$(function() {
	var selectedDirectoryButton = null;
	var selectedCompetitionButton = null;

	/* counts how many buttons exist on the page for each directory / compo */
	var buttonCountByDirectory = {};
	var buttonCountByCompetition = {};

	/* extend jquery collections with an 'addDirectoryButtonBehaviour' function to make buttons selectable */
	$.fn.addDirectoryButtonBehaviour = function() {
		this.click(function() {
			if (this == selectedDirectoryButton) {
				/* deselect button if clicked a second time */
				$(this).removeClass('selected');
				selectedDirectoryButton = null;
			} else {
				if (selectedDirectoryButton) {
					/* deselect any directory button that's previously been selected */
					$(selectedDirectoryButton).removeClass('selected');
				}
				selectedDirectoryButton = this;
				$(this).addClass('selected');
			}

			if (selectedDirectoryButton && selectedCompetitionButton) {
				/* one on each side has been selected now, so form a link */
				makeLink(selectedDirectoryButton, selectedCompetitionButton);
			}
		});
		this.each(function() {
			var directoryId = this.value;
			buttonCountByDirectory[this.value] = (buttonCountByDirectory[this.value] || 0) + 1;

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
		});
	};

	/* extend jquery collections with an 'addCompetitionButtonBehaviour' function to make buttons selectable */
	$.fn.addCompetitionButtonBehaviour = function() {
		this.click(function() {
			if (this == selectedCompetitionButton) {
				/* deselect button if clicked a second time */
				$(this).removeClass('selected');
				selectedCompetitionButton = null;
			} else {
				if (selectedCompetitionButton) {
					/* deselect any competition button that's previously been selected */
					$(selectedCompetitionButton).removeClass('selected');
				}
				selectedCompetitionButton = this;
				$(this).addClass('selected');
			}

			if (selectedDirectoryButton && selectedCompetitionButton) {
				/* one on each side has been selected now, so form a link */
				makeLink(selectedDirectoryButton, selectedCompetitionButton);
			}
		});
		this.each(function() {
			var competitionId = this.value;
			buttonCountByCompetition[this.value] = (buttonCountByCompetition[this.value] || 0) + 1;

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
		});
	};

	$.fn.addUnlinkButtonBehaviour = function() {
		this.click(function() {
			var li = $(this).closest('li');
			var directoryButton = li.find('button.directory').get(0);
			var competitionButton = li.find('button.competition').get(0);

			$.ajax({
				type: 'POST',
				url: '/sceneorg/compofolders/unlink/',
				data: {'directory_id': directoryButton.value, 'competition_id': competitionButton.value},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});

			li.fadeOut('fast');
			/* if buttons were selected at the time of deletion, clear the selection */
			if (directoryButton == selectedDirectoryButton) {
				selectedDirectoryButton = null;
			}
			if (competitionButton == selectedCompetitionButton) {
				selectedCompetitionButton = null;
			}
			buttonCountByDirectory[directoryButton.value] -= 1;
			buttonCountByCompetition[competitionButton.value] -= 1;

			/* add buttons back to the 'unmatched' sections if we've just removed the last one
				for that directory / competition */
			if (buttonCountByDirectory[directoryButton.value] === 0) {
				var newDirectoryButton = $(directoryButton).clone().removeClass('selected matched').addClass('unmatched');
				$('ul.unmatched_directories').append(
					$('<li></li>').append(newDirectoryButton)
				);
				newDirectoryButton.addDirectoryButtonBehaviour();
			}
			if (buttonCountByCompetition[competitionButton.value] === 0) {
				var newCompetitionButton = $(competitionButton).clone().removeClass('selected matched').addClass('unmatched');
				$('ul.unmatched_competitions').append(
					$('<li></li>').append(newCompetitionButton)
				);
				newCompetitionButton.addCompetitionButtonBehaviour();
			}
		});
	};

	/* apply these behaviours to the initial set of buttons */
	$('button.directory').addDirectoryButtonBehaviour();
	$('button.competition').addCompetitionButtonBehaviour();
	$('button.unlink').addUnlinkButtonBehaviour();

	function makeLink(directoryButton, competitionButton) {
		var directoryId = directoryButton.value;
		var competitionId = competitionButton.value;
		/* post the ID pair to the server */
		$.ajax({
			type: 'POST',
			url: '/sceneorg/compofolders/link/',
			data: {'directory_id': directoryId, 'competition_id': competitionId},
			beforeSend: function(xhr) {
				/* need to add CSRF token to the request so that Django will accept it */
				xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
			}
		});

		/* clear selection state so that the next button click won't be considered a link to one of these */
		selectedCompetitionButton = null;
		selectedDirectoryButton = null;

		/* remove the directory / competition buttons from the list, unless they're
			already in the 'matched' list in which they should remain (because that means the
			directory / competition is now linked to multiple partners) */
		if ($(directoryButton).hasClass('unmatched')) {
			$(directoryButton).closest('li').fadeOut('fast');
			buttonCountByDirectory[directoryButton.value] -= 1;
		} else {
			$(directoryButton).removeClass('selected');
		}
		if ($(competitionButton).hasClass('unmatched')) {
			$(competitionButton).closest('li').fadeOut('fast');
			buttonCountByCompetition[competitionButton.value] -= 1;
		} else {
			$(competitionButton).removeClass('selected');
		}

		/* create new buttons for the 'matched' section. Should duplicate the original buttons,
			but not be selected and be labelled 'matched' */
		var newDirectoryButton = $(directoryButton).clone().removeClass('selected unmatched').addClass('matched');
		var newCompetitionButton = $(competitionButton).clone().removeClass('selected unmatched').addClass('matched');
		var newUnlinkButton = $('<button class="unlink" title="Delete this match">unlink</button>');

		var matchElement = $('<li></li>').append(newDirectoryButton, ' = ', newCompetitionButton, ' ', newUnlinkButton);
		$('ul.matches').append(matchElement);
		newDirectoryButton.addDirectoryButtonBehaviour();
		newCompetitionButton.addCompetitionButtonBehaviour();
		newUnlinkButton.addUnlinkButtonBehaviour();
	}
});
