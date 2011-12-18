function htmlEncode(str) {
	return str.replace(/&/g,'&amp;').replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
}

function applyGlobalBehaviours(context) {
	$('ul.messages li', context).animate({'backgroundColor': 'white'}, 5000);
	
	var sortableFormsets = $('ul.sortable_formset', context);
	/* need to apply styling adjustments before spawningFormset to ensure the 'detached' LI gets styled too */
	$('li.sortable_item', sortableFormsets).prepend('<div class="ui-icon ui-icon-arrowthick-2-n-s" title="drag to reorder"></div>');
	$('li.sortable_item input[name$="-ORDER"]', sortableFormsets).hide();

	$('.spawning_formset', context).spawningFormset({onShow: applyGlobalBehaviours});
	$('select[multiple]', context).asmSelect();
	
	$('.carousel_panel .carousel', context).jCarouselLite({
		btnPrev: ".carousel_panel .prev",
		btnNext: ".carousel_panel .next"
	})
	
	sortableFormsets.sortable({
		'items': 'li.sortable_item',
		'update': function(event, ui) {
			$('input[name$="-ORDER"]', this).each(function(i) {
				$(this).val(i+1);
			})
		},
		'cancel': ':input,option,a,label'
	}).disableSelection();
	
	$('input.production_autocomplete', context).autocomplete({
		'source': function(request, response) {
			$.getJSON('/productions/autocomplete/', {'term': request.term}, function(data) {
				response(data);
			});
		},
		'autoFocus': true,
		'select': function(event, ui) {
			$('input#id_production_id').val(ui.item.id);
		}
	});
	
	$('input.date', context).each(function() {
		var opts = {dateFormat: 'd M yy', constrainInput: false, showOn: 'button', dateParser: parseFuzzyDate};
		$(this).datepicker(opts);
	});
	
	$('a.open_in_lightbox', context).click(function(e) {
		if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
			/* probably means they want to open it in a new window, so let them... */
			return true;
		}
		Lightbox.openUrl(this.href, applyGlobalBehaviours);
		return false;
	})
	$('a.open_image_in_lightbox', context).click(function(e) {
		if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
			/* probably means they want to open it in a new window, so let them... */
			return true;
		}
		var screenshotOverlay = $('<div class="screenshot_overlay"></div>');
		var screenshotWrapper = $('<div class="screenshot_wrapper"></div>');
		var screenshotCloseButton = $('<a href="javascript:void(0);" class="lightbox_close" title="Close">Close</div>');
		var screenshotImg = $('<img />');
		$('body').append(screenshotOverlay, screenshotWrapper);
		screenshotWrapper.append(screenshotCloseButton);
		var browserWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
		var browserHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
		screenshotOverlay.css({
			'opacity': 0.5,
			'width': browserWidth,
			'height': browserHeight
		});
		var screenshot = new Image();
		
		function setScreenshotSize() {
			var browserWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
			var browserHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
			
			var imageWidth = screenshot.width || 480;
			var imageHeight = screenshot.height || 340;
			
			maxImageWidth = browserWidth - 64;
			maxImageHeight = browserHeight - 64;
			
			fullWidth = Math.min(imageWidth, maxImageWidth)
			fullHeight = Math.min(imageHeight, maxImageHeight)
			
			heightAtFullWidth = (fullWidth * imageHeight/imageWidth)
			widthAtFullHeight = (fullHeight * imageWidth/imageHeight)
			
			if (heightAtFullWidth <= maxImageHeight) {
				finalWidth = fullWidth;
				finalHeight = Math.round(heightAtFullWidth);
			} else {
				finalWidth = Math.round(widthAtFullHeight);
				finalHeight = fullHeight;
			}
			
			screenshotImg.attr({'width': finalWidth, 'height': finalHeight});
			screenshotWrapper.css({
				'left': (browserWidth - (finalWidth + 32)) / 2 + 'px',
				'top': (browserHeight - (finalHeight + 32)) / 2 + 'px',
				'width': finalWidth + 'px',
				'height': finalHeight + 24 + 'px'
			});
			screenshotOverlay.css({
				'width': browserWidth,
				'height': browserHeight
			});
		}
		
		setScreenshotSize(); /* set size for initial 'loading' popup */
		
		screenshot.onload = function() {
			setScreenshotSize();
			
			screenshotImg.get(0).src = screenshot.src;
			screenshotWrapper.append(screenshotImg);
		}
		
		screenshot.src = this.href;
		
		$(window).resize(setScreenshotSize);
		
		function checkForEscape(evt) {
			if (evt.keyCode == 27) closeScreenshot();
		}
		function closeScreenshot() {
			$(window).unbind('resize', setScreenshotSize);
			$(window).unbind('keydown', checkForEscape);
			screenshotOverlay.remove();
			screenshotWrapper.remove();
		}
		screenshotOverlay.click(closeScreenshot);
		screenshotCloseButton.click(closeScreenshot);
		$(window).keydown(checkForEscape);
		
		return false;
	})
	$('a.replace_main_image', context).click(function(e) {
		if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
			/* probably means they want to open it in a new window, so let them... */
			return true;
		}
		$('#main_image img').attr({
			'src': $(this).attr('data-main-image'),
			'width': $(this).attr('data-main-image-width'),
			'height': $(this).attr('data-main-image-height')
		});
		$('#main_image').attr({'href': $(this).attr('data-original-image')});
		return false;
	})
	$('form.open_in_lightbox', context).submit(function() {
		/* only use this for forms with method="get"! */
		Lightbox.openUrl(this.action + '?' + $(this).serialize(), applyGlobalBehaviours);
		return false;
	})
	
	$('form .nick_match', context).nickMatchWidget();
	
	$('form .nick_field', context).each(function() {
		var nickFieldElement = this;
		var nickField = $(this);
		var uid = $.uid('nickfield');
		
		var searchParams = {};
		if (nickField.hasClass('sceners_only')) searchParams['sceners_only'] = true;
		if (nickField.hasClass('groups_only')) searchParams['groups_only'] = true;
		
		$('.nick_search input:submit', nickFieldElement).hide();
		var searchField = $('.nick_search input:text', nickFieldElement);
		var searchFieldElement = searchField.get(0);
		searchField.attr('autocomplete', 'off');
		var fieldPrefix = searchField.attr('name').replace(/_search$/, '_match_');
		var nickMatchContainer = $('.nick_match_container', nickFieldElement);
		
		searchField.typeahead(function(value, autocomplete) {
			if (value.match(/\S/)) {
				$.ajaxQueue(uid, function(release) {
					/* TODO: consider caching results in a JS variable */
					$.getJSON('/nicks/match/', $.extend({
						q: value,
						autocomplete: autocomplete
					}, searchParams), function(data) {
						if (searchField.val() == data['initial_query']) {
							/* only update fields if search box contents have not changed since making this query */
							nickMatchContainer.html('<div class="nick_match"></div>');
							NickMatchWidget(
								nickMatchContainer.find('.nick_match'),
								data.match.selection, data.match.choices, fieldPrefix);
							if (autocomplete) {
								searchField.val(data.query);
								if (searchFieldElement.setSelectionRange) {
									searchFieldElement.setSelectionRange(data['initial_query'].length, data.query.length);
									/* TODO: IE compatibility */
								}
							}
						}
						release();
					})
				})
			} else {
				/* blank */
				nickMatchContainer.html('');
			}
		});
		
		$(this).addClass('ajaxified');
	});
	
	$('.byline_field', context).bylineField();
	
	$('.production_field', context).each(function() {
		var staticView = $("> .static_view", this);
		var formView = $("> .form_view", this);
		var idField = $("> .form_view > input[type='hidden'][name$='_id']", this);
		if (idField.val() != '') {
			formView.hide();
			staticView.show();
		} else {
			formView.show();
			staticView.hide();
		}
		var clearButton = $('<a href="javascript:void(0);" class="clear_button">clear</a>');
		clearButton.click(function() {
			staticView.hide();
			$(':input', formView).val('');
			$('.byline_search input:text', formView).blur(); /* force refresh */
			formView.show();
			try {$(':input:visible', formView)[0].focus();}catch(_){}
		})
		staticView.append(clearButton);
		
		var titleField = $('input.title_field', this);
		titleField.autocomplete({
			'source': function(request, response) {
				$.getJSON('/productions/autocomplete/',
					{'term': request.term, 'supertype': titleField.attr('data-supertype')},
					function(data) {
						response(data);
					});
			},
			'autoFocus': true,
			'select': function(event, ui) {
				var title = $('<b></b>');
				title.text(ui.item.value);
				$('.static_view_text', staticView).html(title);
				idField.val(ui.item.id);
				formView.hide();
				staticView.show();
			}
		});
	})
}

$(function() {
	applyGlobalBehaviours();
});
