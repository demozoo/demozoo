(function($) {
	$.fn.nickMatchWidget = function() {
		this.each(function() {
			var context = this;
			var searchTermField = $('input[type=hidden]', context);
			if (!searchTermField.length) return; /* no input field; this div is an empty placeholder */
			var searchTerm = searchTermField.val();
			
			var selectedResult = $('<a href="javascript:void(0)" tabindex="0" class="selected_result"></a>');
			/* tabindex ensures that a click causes it to be focused on Chrome */
			var selectedResultInner = $('<span></span>');
			selectedResult.append(selectedResultInner);
			selectedResultInner.text(searchTerm);
			$(context).prepend(selectedResult);
			
			var suggestionsUl = $('ul', context);
			
			function copyIconFromSelectedLi() {
				/* inherit icon for selectedResult from the li with the selected radio button,
				or 'error' icon if there is none */
				var selectedLi = $('li:has(input[checked])', suggestionsUl);
				if (selectedLi.length) {
					var classNames = 'selected_result ' + selectedLi.attr('class');
					if (selectedResult.hasClass('active')) classNames += ' active';
					selectedResult.attr('class', classNames);
					/* also copy label text from the data-name attribute */
					selectedResultInner.text(selectedLi.attr('data-name'));
				} else {
					selectedResult.attr('class', 'selected_result error');
				}
			}
			copyIconFromSelectedLi();
			
			function highlightSelectedLi() {
				$('li', suggestionsUl).removeClass('selected');
				$('li:has(input[checked])', suggestionsUl).addClass('selected');
			}
			
			function keypress(e) {
				if (e.which == 40) { /* cursor down */
					if (suggestionsUl.is(':visible')) {
						var nextElem = $('li:has(input[checked])', suggestionsUl).next();
						if (nextElem.length) {
							$('input', nextElem).attr('checked', 'checked');
						} else {
							$('li:first input', suggestionsUl).attr('checked', 'checked')
						}
						highlightSelectedLi();
						copyIconFromSelectedLi();
					} else {
						suggestionsUl.show();
					}
					return false;
				} else if (e.which == 38) { /* cursor up */
					if (suggestionsUl.is(':visible')) {
						suggestionsUl.show();
						var prevElem = $('li:has(input[checked])', suggestionsUl).prev();
						if (prevElem.length) {
							$('input', prevElem).attr('checked', 'checked');
						} else {
							$('li:last input', suggestionsUl).attr('checked', 'checked')
						}
						highlightSelectedLi();
						copyIconFromSelectedLi();
					} else {
						suggestionsUl.show();
					}
					return false;
				} else if (e.which == 13) { /* enter */
					/* show/hide the dropdown.
						Serves no purpose, but seems to be psychologically important. UI design, eh? */
					if (suggestionsUl.is(':visible')) {
						suggestionsUl.hide();
					} else {
						suggestionsUl.show();
					}
				}
			}
			
			suggestionsUl.hide();
			var wasFocusedOnLastMousedown = false;
			selectedResult.focus(function() {
				selectedResult.addClass('active');
				suggestionsUl.show();
				highlightSelectedLi();
				$(document).bind('keydown', keypress);
			}).blur(function() {
				setTimeout(function() {
					selectedResult.removeClass('active');
					suggestionsUl.hide();
					copyIconFromSelectedLi();
					$(document).unbind('keydown', keypress);
				}, 100);
			}).click(function() {
				if (selectedResult.hasClass('active') && wasFocusedOnLastMousedown) {
					selectedResult.blur();
				}
			}).mousedown(function() {
				wasFocusedOnLastMousedown = selectedResult.hasClass('active');
			})
		});
		$(this).addClass('ajaxified');
	}
})(jQuery);
