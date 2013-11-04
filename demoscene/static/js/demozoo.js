function htmlEncode(str) {
	return str.replace(/&/g,'&amp;').replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
}

function applyGlobalBehaviours(context) {
	$('ul.messages li', context).animate({'backgroundColor': 'white'}, 5000);

	$('a.open_in_lightbox', context).click(function(e) {
		if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
			/* probably means they want to open it in a new window, so let them... */
			return true;
		}
		var focusEmptyInput = $(this).hasClass('focus_empty_input');
		Lightbox.openUrl(this.href, applyGlobalBehaviours, {'focusEmptyInput': focusEmptyInput});
		return false;
	});
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
	$('form.open_in_lightbox', context).submit(function() {
		/* only use this for forms with method="get"! */
		Lightbox.openUrl(this.action + '?' + $(this).serialize(), applyGlobalBehaviours);
		return false;
	})

	$('.microthumb', context).thumbPreview();
}

$(function() {
	var loginLinks = $('#login_status_panel .login_links');
	
	loginLinks.hide();
	var loginLinksVisible = false;
	
	function hideLoginLinksOnBodyClick(e) {
		if (loginLinksVisible && !loginLinks.has(e.target).length) {
			loginLinks.hide(); loginLinksVisible = false;
		}
	}
	function showLoginLinks() {
		loginLinks.slideDown(100);
		loginLinksVisible = true;
		$('body').bind('click', hideLoginLinksOnBodyClick);
	}
	function hideLoginLinks() {
		loginLinks.hide();
		loginLinksVisible = false;
		$('body').unbind('click', hideLoginLinksOnBodyClick);
	}
	
	$('#login_status_panel .login_status').wrapInner('<a href="javascript:void(0)"></a>');
	$('#login_status_panel .login_status a').click(function() {
		if (loginLinksVisible) {
			hideLoginLinks();
		} else {
			showLoginLinks();
		}
		return false;
	});

	var searchPlaceholderText = 'Type in keyword';
	var searchField = $('#global_search #id_q');
	if (searchField.val() === '' || searchField.val() === searchPlaceholderText) {
		searchField.val(searchPlaceholderText).addClass('placeholder');
	}
	searchField.focus(function() {
		if (searchField.hasClass('placeholder')) {
			searchField.val('').removeClass('placeholder');
		}
	}).blur(function() {
		if (searchField.val() === '') {
			searchField.val(searchPlaceholderText).addClass('placeholder');
		}
	});
	$('#global_search').submit(function() {
		if (searchField.hasClass('placeholder') || searchField.val() === '') {
			searchField.focus(); return false;
		}
	});

	searchField.autocomplete({
		'html': true,
		'source': function(request, response) {
			$.getJSON('/search/live/', {'q': request.term}, function(data) {
				for (var i = 0; i < data.length; i++) {
					var thumbnail = '';
					if (data[i].thumbnail) {
						thumbnail = '<div class="microthumb"><img src="' + htmlEncode(data[i].thumbnail.url) + '" width="' + data[i].thumbnail.width + '" height="' + data[i].thumbnail.height + '" alt="" /></div>';
					}
					data[i].label = '<div class="autosuggest_result ' + htmlEncode(data[i].type) + '">' + thumbnail + htmlEncode(data[i].value) + '</div>';
				}
				response(data);
			});
		},
		'select': function(event, ui) {
			document.location.href = ui.item.url;
		}
	});

	applyGlobalBehaviours();
});
