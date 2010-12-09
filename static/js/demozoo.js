function htmlEncode(str) {
	return str.replace(/&/g,'&amp;').replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
}

function applyGlobalBehaviours(context) {
	$('ul.messages li', context).animate({'backgroundColor': 'white'}, 5000);
	
	var sortableFormsets = $('ul.sortable_formset', context);
	/* need to apply styling adjustments before spawningFormset to ensure the 'detached' LI gets styled too */
	$('li.sortable_item', sortableFormsets).prepend('<div class="ui-icon ui-icon-arrowthick-2-n-s" title="drag to reorder"></div>');
	$('li.sortable_item input[name$="-ORDER"]', sortableFormsets).hide();

	$('.spawning_formset', context).spawningFormset();
	
	sortableFormsets.sortable({
		'items': 'li.sortable_item',
		'update': function(event, ui) {
			$('input[name$="-ORDER"]', this).each(function(i) {
				$(this).val(i+1);
			})
		}
	}).disableSelection();
	
	function addAutocompleteRule(selector, url, idField, useNickId, context) {
		$(selector, context).autocomplete(url, {
			autoFill: true,
			formatItem: function(row) {return htmlEncode(decodeURIComponent(row[2]))},
			formatResult: function(row) {return decodeURIComponent(row[3])},
			selectFirst: true,
			matchSubset: false,
			matchCase: true,
			extraParams: {'new_option': true}
		}).result(function(evt, result) {
			$(idField).val(result[useNickId ? 1 : 0]);
		});
	}
	/* TODO: instead of hard-coding hidden field IDs, derive them from the text field ID (thus supporting prefixes -> multiple forms per page) */
	addAutocompleteRule('input.production_autocomplete', '/productions/autocomplete/', 'input#id_production_id', false, context);
	
	$('input.date', context).each(function() {
		var opts = {dateFormat: 'd M yy', constrainInput: false, showOn: 'button', dateParser: parseFuzzyDate};
		$(this).datepicker(opts);
	});
	
	function openUrlInLightbox(url) {
		$('body').addClass('loading');
		lightboxContent.load(url, function() {
			applyGlobalBehaviours(lightbox);
			$('body').removeClass('loading');
			showLightbox();
		});
	}
	$('a.open_in_lightbox', context).click(function(e) {
		if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
			/* probably means they want to open it in a new window, so let them... */
			return true;
		}
		openUrlInLightbox(this.href);
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
		openUrlInLightbox(this.action + '?' + $(this).serialize());
		return false;
	})
	
	$('form .nick_match', context).nickMatchWidget();
	
	$('form .nick_field', context).each(function() {
		var nickFieldElement = this;
		var nickField = $(this);
		
		var searchParams = {};
		if (nickField.hasClass('sceners_only')) searchParams['sceners_only'] = true;
		if (nickField.hasClass('groups_only')) searchParams['groups_only'] = true;
		
		$('.nick_search input:submit', nickFieldElement).hide();
		var searchField = $('.nick_search input:text', nickFieldElement);
		var searchFieldElement = searchField.get(0);
		searchField.attr('autocomplete', 'off');
		
		var lookupRunning = false;
		var lastSearchTerm = searchField.val();
		var nextSearchTerm;
		var autocompleteNextSearchTerm;
		
		function cueLookup(autocomplete) {
			var value = searchField.val();
			if (lookupRunning) {
				nextSearchTerm = value;
				autocompleteNextSearchTerm = autocomplete
			} else {
				lookup(value, autocomplete);
			}
		}
		
		function lookup(value, autocomplete) {
			if (value.match(/\S/)) {
				if (value == lastSearchTerm) return;
				lookupRunning = true;
				/* TODO: consider caching results in a JS variable */
				$.getJSON('/nicks/match/', $.extend({
					q: value,
					field_name: searchField.attr('name').replace(/_search$/, '_match'),
					autocomplete: autocomplete
				}, searchParams), function(data) {
					if (searchField.val() == data['initial_query']) {
						/* only update fields if search box contents have not changed since making this query */
						$('.nick_match_container', nickFieldElement).html(data.matches);
						$('.nick_match', nickFieldElement).nickMatchWidget();
						if (autocomplete) {
							searchField.val(data.query);
							if (searchFieldElement.setSelectionRange) {
								searchFieldElement.setSelectionRange(data['initial_query'].length, data.query.length);
								/* TODO: IE compatibility */
							}
						}
						lastSearchTerm = data.query;
					}
					lookupRunning = false;
					if (nextSearchTerm) {
						lookup(nextSearchTerm, autocompleteNextSearchTerm);
						nextSearchTerm = null;
					}
				})
			} else {
				/* blank */
				lastSearchTerm = '';
				$('.nick_match_container', nickFieldElement).html('');
			}
		}
		
		var keydownTimer;
		searchField.blur(function() {
			cueLookup(false);
		}).keydown(function(e) {
			/* compare current field contents to new field contents to decide what to do about autocompletion */
			var oldValue = searchField.val();
			var selectionWasAtEnd = (searchFieldElement.selectionEnd == oldValue.length);
			var unselectedPortion = searchField.val().substring(0, searchFieldElement.selectionStart);
			
			setTimeout(function() {
				var newValue = searchField.val();
				if (oldValue == newValue) return;
				if (selectionWasAtEnd
					&& searchFieldElement.selectionStart == newValue.length /* no selection now */
					&& newValue.length == unselectedPortion.length + 1 /* new value is one letter longer */
					&& newValue.indexOf(unselectedPortion) == 0 /* old unselected portion is a prefix of new value */
				) {
					/* autocomplete */
					cueLookup(true);
				} else {
					/* have made some other change (e.g. deletion, pasting text); do not autocomplete */
					cueLookup(false);
				}
			}, 1);
		});
		
		$(this).addClass('ajaxified');
	});
	
	$('form .byline_field', context).each(function() {
		var bylineFieldElement = this;
		var bylineField = $(this);
		
		$('.byline_search input:submit', bylineFieldElement).hide();
		var searchField = $('.byline_search input:text', bylineFieldElement);
		var searchFieldElement = searchField.get(0);
		searchField.attr('autocomplete', 'off');
		
		var lookupRunning = false;
		var lastSearchTerm = searchField.val();
		var nextSearchTerm;
		var autocompleteNextSearchTerm;
		
		function cueLookup(autocomplete) {
			var value = searchField.val();
			if (lookupRunning) {
				nextSearchTerm = value;
				autocompleteNextSearchTerm = autocomplete
			} else {
				lookup(value, autocomplete);
			}
		}
		
		function lookup(value, autocomplete) {
			if (value.match(/\S/)) {
				if (value == lastSearchTerm) return;
				lookupRunning = true;
				/* TODO: consider caching results in a JS variable */
				$.getJSON('/nicks/byline_match/', {
					q: value,
					field_name: searchField.attr('name').replace(/_search$/, ''),
					autocomplete: autocomplete
				}, function(data) {
					if (searchField.val() == data['initial_query']) {
						/* only update fields if search box contents have not changed since making this query */
						$('.byline_match_container', bylineFieldElement).html(data.matches);
						$('.nick_match', bylineFieldElement).nickMatchWidget();
						if (autocomplete) {
							searchField.val(data.query);
							if (searchFieldElement.setSelectionRange) {
								searchFieldElement.setSelectionRange(data['initial_query'].length, data.query.length);
								/* TODO: IE compatibility */
							}
						}
						lastSearchTerm = data.query;
					}
					lookupRunning = false;
					if (nextSearchTerm) {
						lookup(nextSearchTerm, autocompleteNextSearchTerm);
						nextSearchTerm = null;
					}
				})
			} else {
				/* blank */
				lastSearchTerm = '';
				$('.byline_match_container', bylineFieldElement).html('');
			}
		}
		
		var keydownTimer;
		searchField.blur(function() {
			cueLookup(false);
		}).keydown(function(e) {
			/* compare current field contents to new field contents to decide what to do about autocompletion */
			var oldValue = searchField.val();
			var selectionWasAtEnd = (searchFieldElement.selectionEnd == oldValue.length);
			var unselectedPortion = searchField.val().substring(0, searchFieldElement.selectionStart);
			
			setTimeout(function() {
				var newValue = searchField.val();
				if (oldValue == newValue) return;
				if (selectionWasAtEnd
					&& searchFieldElement.selectionStart == newValue.length /* no selection now */
					&& newValue.length == unselectedPortion.length + 1 /* new value is one letter longer */
					&& newValue.indexOf(unselectedPortion) == 0 /* old unselected portion is a prefix of new value */
				) {
					/* autocomplete */
					cueLookup(true);
				} else {
					/* have made some other change (e.g. deletion, pasting text); do not autocomplete */
					cueLookup(false);
				}
			}, 1);
		});
		
		$(this).addClass('ajaxified');
	});
}

var lightboxOuter, lightbox, lightboxContent, lightboxClose;
function setLightboxSize() {
	var browserHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
	lightbox.css({'max-height': browserHeight - 48 + 'px'});
}
function lightboxCheckForEscape(evt) {
	if (evt.keyCode == 27) closeLightbox();
}
function closeLightbox() {
	$(window).unbind('resize', setLightboxSize);
	$(window).unbind('keydown', lightboxCheckForEscape);
	lightboxOuter.hide();
}
function showLightbox() {
	lightboxOuter.show();
	
	setLightboxSize();
	$(window).keydown(lightboxCheckForEscape);
	$(window).resize(setLightboxSize);
}
$(function() {
	lightboxOuter = $('<div id="lightbox_outer"></div>');
	var lightboxMiddle = $('<div id="lightbox_middle"></div>');
	lightbox = $('<div id="lightbox"></div>');
	lightboxClose = $('<a href="javascript:void(0);" class="lightbox_close" title="Close">Close</div>');
	lightboxContent = $('<div></div>');
	lightbox.append(lightboxClose, lightboxContent);
	lightboxMiddle.append(lightbox);
	lightboxOuter.append(lightboxMiddle);
	$('body').append(lightboxOuter);
	lightboxOuter.click(closeLightbox);
	lightbox.click(function(e) {
		e.stopPropagation();
	});
	lightboxClose.click(closeLightbox);
	lightboxOuter.hide();
	applyGlobalBehaviours();
});
