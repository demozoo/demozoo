function initAddCreditLink(context) {
	$('a.add_credit', context).click(function() {
		ModalWorkflow({
			'url': this.href,
			'responses': {
				'creditAdded': replaceCreditsPanel
			}
		});
		return false;
	});
}

function initEditCreditLink(context) {
	$('a.edit_credit', context).click(function() {
		ModalWorkflow({
			'url': this.href,
			'responses': {
				'creditUpdated': replaceCreditsPanel
			}
		});
		return false;
	});
}

function replaceCreditsPanel(creditsHtml) {
	$('#credits_panel').replaceWith(creditsHtml);
	var panel = $('#credits_panel');
	applyGlobalBehaviours(panel);
	initAddCreditLink(panel);
	initEditCreditLink(panel);
	initCreditsPanel(panel);
	initEditChunkHover(panel);
}

function initEditChunkHover(context) {
	$('.edit_chunk', context).hover(function() {
		$(this).closest('.editable_chunk').addClass('hover');
	}, function() {
		$(this).closest('.editable_chunk').removeClass('hover');
	});
}

$(function() {
	initEditChunkHover();

	$('.tell_us_something_panel').each(function() {
		var heading = $('.tell_us_something_title', this);
		var list = $('.tell_us_something_options', this);

		if (list.length) {
			heading.wrapInner('<a href="javascript:void(0);" class="dropdown"></a>');
			var dropdownLink = heading.find('a');

			list.hide();
			dropdownLink.click(function() {
				if (dropdownLink.hasClass('active')) {
					list.slideUp('fast');
					dropdownLink.removeClass('active');
				} else {
					list.slideDown('fast');
					dropdownLink.addClass('active');
				}
			});
		}
	});
	initAddCreditLink();
	initEditCreditLink();
});
