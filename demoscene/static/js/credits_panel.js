$(function() {
	$('.credits_panel').each(function() {
		var panel = $(this);

		var addCreditButton = panel.find('a.add_credit');

		/* only proceed if we actually have an add credit button
			(i.e. user is logged in and site is in editable mode) */
		if (!addCreditButton.length) return;

		/* TODO: cut out the blatant copy-and-pasting between here and tags_panel.js */

		var actions = $('<ul class="actions"></ul>');
		var editButton = $('<a href="javascript:void(0);" class="action_button icon edit_chunk" title="Edit credits"></a>');

		function updateEditButtonState() {
			if (panel.hasClass('editing')) {
				editButton.removeClass('edit').addClass('done').text('Done');
			} else {
				editButton.removeClass('done').addClass('edit').text('Edit');
			}
		}
		updateEditButtonState();

		actions.append(editButton.wrap('<li></li>'));
		actions.insertAfter(panel.find('h3'));

		editButton.click(function() {
			panel.toggleClass('editing');
			updateEditButtonState();
		});

	});
});
