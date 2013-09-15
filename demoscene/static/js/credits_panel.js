$(function() {
	$('.credits_panel').each(function() {
		var panel = $(this);

		var addCreditButton = panel.find('a.add_credit');

		/* only proceed if we actually have an add credit button
			(i.e. user is logged in and site is in editable mode) */
		if (!addCreditButton.length) return;

		/* TODO: cut out the blatant copy-and-pasting between here and tags_panel.js */

		var actions = $('<ul class="actions"></ul>');
		var editButton = $('<a href="javascript:void(0);" class="action_button icon edit edit_chunk" title="Edit credits">Edit</a>');
		actions.append(editButton.wrap('<li></li>'));
		actions.insertAfter(panel.find('h3'));

		var isEditing = false;
		editButton.click(function() {
			if (isEditing) {
				isEditing = false;
				panel.removeClass('editing');
				editButton.removeClass('done').addClass('edit').text('Edit');
			} else {
				isEditing = true;
				panel.addClass('editing');
				editButton.removeClass('edit').addClass('done').text('Done');
			}
		});

	});
});
