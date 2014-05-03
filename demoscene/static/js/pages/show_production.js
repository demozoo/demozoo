function initEditCreditLink(context) {
	$('a.edit_credit, a.add_credit', context).click(function() {
		ModalWorkflow({
			'url': this.href,
			'responses': {
				'creditsUpdated': replaceCreditsPanel
			}
		});
		return false;
	});
}

function replaceCreditsPanel(creditsHtml) {
	$('.secondary_panels').removeClass('hidden');
	$('#credits_panel').replaceWith(creditsHtml);
	var panel = $('#credits_panel');
	applyGlobalBehaviours(panel);
	initEditCreditLink(panel);
	initEditToggle(panel);
	initEditChunkHover(panel);
}

$(function() {
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
		list.find('a').click(function() {
			list.slideUp('fast');
			dropdownLink.removeClass('active');
		});
	});
	initEditCreditLink();

	$('.comment_form_trigger').each(function() {
		var commentForm = $('.comment_form');
		commentForm.hide();
		$(this).wrapInner('<a href="javascript:void(0)"></a>');
		$('a', this).click(function() {
			if (commentForm.is(':visible')) {
				commentForm.slideUp();
			} else {
				commentForm.slideDown(function() {
					commentForm.find('textarea').focus();
				});
			}
		});
	});

	if (location.hash.match(/\#comment-\d+/)) {
		$(location.hash).css({'background-color': '#dfd'}).animate({'backgroundColor': '#eee'}, 3000);
	}

	var editTagsUrl = $('form.tags_form').attr('action');
	var addTagUrl = editTagsUrl.replace(/\/edit_tags\/$/, '/add_tag/');
	var removeTagUrl = editTagsUrl.replace(/\/edit_tags\/$/, '/remove_tag/');

	$('#id_tags').tagit({
		'afterTagAdded': function(event, data) {
			if (data.duringInitialization) return;
			$.post(addTagUrl, {
				'csrfmiddlewaretoken': $.cookie('csrftoken'),
				'tag_name': data.tagLabel
			}, function(response) {
				$('ul.tags').html(response);
			});
		},
		'afterTagRemoved': function(event, data) {
			$.post(removeTagUrl, {
				'csrfmiddlewaretoken': $.cookie('csrftoken'),
				'tag_name': data.tagLabel
			}, function(response) {
				$('ul.tags').html(response);
			});
		},
		'autocomplete': {
			'source': '/productions/autocomplete_tags/'
		}
	});

	$('form.tags_form input:submit').remove();
	$('.tags_panel').on('panelEditEnable', function() {
		$('form.tags_form li.tagit-new input').focus();
	});
	$('.tags_panel a.tag_name').each(function() {
		var tag = this;
		var description = $(tag).data('description');
		if (description) {
			var hideDescriptionTimeout;

			tagOffset = $(tag).offset();
			var descriptionElem = $('<div class="tag_description"></div>').html(description).css({
				'position': 'absolute',
				'top': (tagOffset.top + 32) + 'px',
				'left': (tagOffset.left - 300) + 'px'
			}).hide();
			$('body').append(descriptionElem);
			$(tag).hover(function() {
				$('.tag_description').hide(); /* hide all other tag descriptions */
				descriptionElem.show();
				clearTimeout(hideDescriptionTimeout);
			}, function() {
				hideDescriptionTimeout = setTimeout(function() {
					descriptionElem.hide();
				}, 750);
			});
			descriptionElem.hover(function() {
				clearTimeout(hideDescriptionTimeout);
			}, function() {
				hideDescriptionTimeout = setTimeout(function() {
					descriptionElem.hide();
				}, 750);
			});
		}
	});
});
