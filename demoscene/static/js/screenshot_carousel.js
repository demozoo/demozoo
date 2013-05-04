function initScreenshotCarousel(screenshots) {
	var panel = $('.screenshots_panel');

	var leftScreenshot = $('a.screenshot', panel);
	var leftImg = leftScreenshot.find('img');

	var viewport = $('<div class="screenshot_carousel"><div class="viewport"><div class="tray"></div></div><a href="javascript:void(0);" class="nav prev">Previous</a><a href="javascript:void(0);" class="nav next">Next</a></div>');
	leftScreenshot.replaceWith(viewport);
	var tray = $('.tray', viewport);
	tray.append(leftScreenshot);

	var rightScreenshot = $('<a class="screenshot open_image_in_lightbox"><img></a>');
	tray.append(rightScreenshot);
	var rightImg = rightScreenshot.find('img');

	var hasPreloadedAllImages = false;
	function preloadAllImages() {
		for (var i = 0; i < screenshots.length; i++) {
			var src = screenshots[i].src;
			var img = new Image();
			img.src = src;
		}
		hasPreloadedAllImages = true;
	}

	var currentIndex = 0;

	function setLeftScreenshot(screenshot) {
		leftScreenshot.attr({'href': screenshot['original_url']});
		leftImg.attr({'src': screenshot.src, 'width': screenshot.width, 'height': screenshot.height});
	}
	function setRightScreenshot(screenshot) {
		rightScreenshot.attr({'href': screenshot['original_url']});
		rightImg.attr({'src': screenshot.src, 'width': screenshot.width, 'height': screenshot.height});
	}

	$('.next', viewport).click(function() {
		if (!hasPreloadedAllImages) preloadAllImages();

		setLeftScreenshot(screenshots[currentIndex]);
		currentIndex = (currentIndex + 1) % screenshots.length;
		setRightScreenshot(screenshots[currentIndex]);
		tray.stop().css({'left': '0'}).animate({'left': '-400px'});

		return false;
	});

	$('.prev', viewport).click(function() {
		if (!hasPreloadedAllImages) preloadAllImages();

		setRightScreenshot(screenshots[currentIndex]);
		currentIndex = (currentIndex + screenshots.length - 1) % screenshots.length;
		setLeftScreenshot(screenshots[currentIndex]);
		tray.stop().css({'left': '-400px'}).animate({'left': '0'});

		return false;
	});
}
