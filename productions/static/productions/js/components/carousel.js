function initCarousel(carouselItems) {
	if (carouselItems.length < 2) return;
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
		for (var i = 0; i < carouselItems.length; i++) {
			if (carouselItems[i].type == 'screenshot') {
				var src = carouselItems[i].data['standard_url'];
				var img = new Image();
				img.src = src;
			}
		}
		hasPreloadedAllImages = true;
	}

	var currentIndex = 0;

	function setLeftScreenshot(screenshot) {
		leftScreenshot.attr({'href': screenshot['original_url']});
		leftImg.attr({'src': screenshot['standard_url'], 'width': screenshot['standard_width'], 'height': screenshot['standard_height']});
	}
	function setRightScreenshot(screenshot) {
		rightScreenshot.attr({'href': screenshot['original_url']});
		rightImg.attr({'src': screenshot['standard_url'], 'width': screenshot['standard_width'], 'height': screenshot['standard_height']});
	}

	$('.next', viewport).click(function() {
		if (!hasPreloadedAllImages) preloadAllImages();

		setLeftScreenshot(carouselItems[currentIndex].data);
		currentIndex = (currentIndex + 1) % carouselItems.length;
		setRightScreenshot(carouselItems[currentIndex].data);
		tray.stop().css({'left': '0'}).animate({'left': '-400px'});

		return false;
	});

	$('.prev', viewport).click(function() {
		if (!hasPreloadedAllImages) preloadAllImages();

		setRightScreenshot(carouselItems[currentIndex].data);
		currentIndex = (currentIndex + carouselItems.length - 1) % carouselItems.length;
		setLeftScreenshot(carouselItems[currentIndex].data);
		tray.stop().css({'left': '-400px'}).animate({'left': '0'});

		return false;
	});
}
