$(function() {
	$('.tags_panel').each(function() {
		var panel = $(this);

		var addTagForm = panel.find('form.add_tag');

		/* only proceed if we actually have an addTagForm
			(i.e. user is logged in and site is in editable mode) */
		if (!addTagForm.length) return;

		var actions = $('<ul class="actions"></ul>');
		var editButton = $('<a href="javascript:void(0);" class="action_button icon edit edit_chunk" title="Edit tags">Edit</a>');
		actions.append(editButton.wrap('<li></li>'));
		actions.insertAfter(panel.find('h3'));

		isEditing = false;
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
