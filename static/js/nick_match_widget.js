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
				var selectedLi = $('li:has(input[checked])', context);
				if (selectedLi.length) {
					selectedResult.attr('class', 'selected_result ' + selectedLi.attr('class'));
					/* also copy label text from the data-name attribute */
					selectedResultInner.text(selectedLi.attr('data-name'));
				} else {
					selectedResult.attr('class', 'selected_result error');
				}
			}
			copyIconFromSelectedLi();
			
			suggestionsUl.hide();
			var wasFocusedOnLastMousedown = false;
			selectedResult.focus(function() {
				selectedResult.addClass('active');
				suggestionsUl.show();
			}).blur(function() {
				setTimeout(function() {
					selectedResult.removeClass('active');
					suggestionsUl.hide();
					copyIconFromSelectedLi();
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
