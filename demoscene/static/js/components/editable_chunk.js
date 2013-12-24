function initEditChunkHover(context) {
	$('.edit_chunk', context).hover(function() {
		$(this).closest('.editable_chunk').addClass('hover');
	}, function() {
		$(this).closest('.editable_chunk').removeClass('hover');
	});
}

function initEditToggle(context) {
	$('.edit_toggle', context).each(function() {
		var panel = $(this);

		var actions = $('<ul class="actions"></ul>');
		var editButton = $('<a href="javascript:void(0);" class="action_button icon edit_chunk" title="Edit credits"></a>');

		function updateEditButtonState() {
			if (panel.hasClass('editing')) {
				panel.removeClass('hide_edit_controls');
				editButton.removeClass('edit').addClass('done').text('Done');
			} else {
				panel.addClass('hide_edit_controls');
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
}

$(function() {
	initEditToggle();
	initEditChunkHover();
});
