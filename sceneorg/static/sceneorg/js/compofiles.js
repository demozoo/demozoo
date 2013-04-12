$(function() {
	var selectedFileButton = null;
	var selectedProductionButton = null;

	/* counts how many buttons exist on the page for each file / prod */
	var buttonCountByFile = {};
	var buttonCountByProduction = {};

	/* extend jquery collections with an 'addFileButtonBehaviour' function to make buttons selectable */
	$.fn.addFileButtonBehaviour = function() {
		this.click(function() {
			if (this == selectedFileButton) {
				/* deselect button if clicked a second time */
				$(this).removeClass('selected');
				selectedFileButton = null;
			} else {
				if (selectedFileButton) {
					/* deselect any file button that's previously been selected */
					$(selectedFileButton).removeClass('selected');
				}
				selectedFileButton = this;
				$(this).addClass('selected');
			}

			if (selectedFileButton && selectedProductionButton) {
				/* one on each side has been selected now, so form a link */
				makeLink(selectedFileButton, selectedProductionButton);
			}
		});
		this.each(function() {
			buttonCountByFile[this.value] = (buttonCountByFile[this.value] || 0) + 1;
		});
	};

	/* extend jquery collections with an 'addProductionButtonBehaviour' function to make buttons selectable */
	$.fn.addProductionButtonBehaviour = function() {
		this.click(function() {
			if (this == selectedProductionButton) {
				/* deselect button if clicked a second time */
				$(this).removeClass('selected');
				selectedProductionButton = null;
			} else {
				if (selectedProductionButton) {
					/* deselect any production button that's previously been selected */
					$(selectedProductionButton).removeClass('selected');
				}
				selectedProductionButton = this;
				$(this).addClass('selected');
			}

			if (selectedFileButton && selectedProductionButton) {
				/* one on each side has been selected now, so form a link */
				makeLink(selectedFileButton, selectedProductionButton);
			}
		});
		this.each(function() {
			buttonCountByProduction[this.value] = (buttonCountByProduction[this.value] || 0) + 1;
		});
	};

	$.fn.addUnlinkButtonBehaviour = function() {
		this.click(function() {
			var li = $(this).closest('li');
			var fileButton = li.find('button.file').get(0);
			var productionButton = li.find('button.production').get(0);

			$.ajax({
				type: 'POST',
				url: '/sceneorg/compofiles/unlink/',
				data: {'file_id': fileButton.value, 'production_id': productionButton.value},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});

			li.fadeOut('fast');
			/* if buttons were selected at the time of deletion, clear the selection */
			if (fileButton == selectedFileButton) {
				selectedFileButton = null;
			}
			if (productionButton == selectedProductionButton) {
				selectedProductionButton = null;
			}
			buttonCountByFile[fileButton.value] -= 1;
			buttonCountByProduction[productionButton.value] -= 1;

			/* add buttons back to the 'unmatched' sections if we've just removed the last one
				for that file / production */
			if (buttonCountByFile[fileButton.value] === 0) {
				var newFileButton = $(fileButton).clone().removeClass('selected matched').addClass('unmatched');
				$('ul.unmatched_files').append(
					$('<li></li>').append(newFileButton)
				);
				newFileButton.addFileButtonBehaviour();
			}
			if (buttonCountByProduction[productionButton.value] === 0) {
				var newProductionButton = $(productionButton).clone().removeClass('selected matched').addClass('unmatched');
				$('ul.unmatched_productions').append(
					$('<li></li>').append(newProductionButton)
				);
				newProductionButton.addProductionButtonBehaviour();
			}
		});
	};

	/* apply these behaviours to the initial set of buttons */
	$('button.file').addFileButtonBehaviour();
	$('button.production').addProductionButtonBehaviour();
	$('button.unlink').addUnlinkButtonBehaviour();

	function makeLink(fileButton, productionButton) {
		/* discard attempts to match two buttons that are already linked */
		var alreadyMatched = $(fileButton).parent().get(0) == $(productionButton).parent().get(0);

		var fileId = fileButton.value;
		var productionId = productionButton.value;
		if (!alreadyMatched) {
			/* post the ID pair to the server */
			$.ajax({
				type: 'POST',
				url: '/sceneorg/compofiles/link/',
				data: {'file_id': fileId, 'production_id': productionId},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		}

		/* clear selection state so that the next button click won't be considered a link to one of these */
		selectedProductionButton = null;
		selectedFileButton = null;

		/* remove the file / production buttons from the list, unless they're
			already in the 'matched' list in which they should remain (because that means the
			file / production is now linked to multiple partners) */
		if ($(fileButton).hasClass('unmatched')) {
			$(fileButton).closest('li').fadeOut('fast');
			buttonCountByFile[fileButton.value] -= 1;
		} else {
			$(fileButton).removeClass('selected');
		}
		if ($(productionButton).hasClass('unmatched')) {
			$(productionButton).closest('li').fadeOut('fast');
			buttonCountByProduction[productionButton.value] -= 1;
		} else {
			$(productionButton).removeClass('selected');
		}

		if (!alreadyMatched) {
			/* create new buttons for the 'matched' section. Should duplicate the original buttons,
				but not be selected and be labelled 'matched' */
			var newFileButton = $(fileButton).clone().removeClass('selected unmatched').addClass('matched');
			var newProductionButton = $(productionButton).clone().removeClass('selected unmatched').addClass('matched');
			var newUnlinkButton = $('<button class="unlink" title="Delete this match">unlink</button>');

			var matchElement = $('<li></li>').append(newFileButton, ' = ', newProductionButton, ' ', newUnlinkButton);
			$('ul.matches').append(matchElement);
			newFileButton.addFileButtonBehaviour();
			newProductionButton.addProductionButtonBehaviour();
			newUnlinkButton.addUnlinkButtonBehaviour();
		}
	}
});
