(function($) {
	$.fn.carousel = function(carouselData) {
		function Screenshot(fullData) {
			this.data = fullData.data;
		}
		Screenshot.prototype.preload = function() {
			var src = this.data['standard_url'];
			var img = new Image();
			img.src = src;
		};
		Screenshot.prototype.draw = function(container) {
			var link = $('<a class="screenshot"></a>').attr({'href': this.data['original_url']});
			var img = $('<img>').attr({'src': this.data['standard_url'], 'width': this.data['standard_width'], 'height': this.data['standard_height']});
			link.append(img);
			container.html(link);
			link.openImageInLightbox();
		};

		var itemTypes = {
			'screenshot': Screenshot
		};

		if (carouselData.length < 2) return;

		var carouselItems = [];
		for (var i = 0; i < carouselData.length; i++) {
			itemType = itemTypes[carouselData[i].type];
			carouselItems[i] = new itemType(carouselData[i]);
		}

		var viewport = this;
		viewport.html('<div class="viewport"><div class="tray"><div class="carousel_left"></div><div class="carousel_right"></div></div></div><a href="javascript:void(0);" class="nav prev">Previous</a><a href="javascript:void(0);" class="nav next">Next</a>');
		var tray = $('.tray', viewport);

		var leftItem = $('.carousel_left');
		carouselItems[0].draw(leftItem);

		var rightItem = $('.carousel_right');

		var hasPreloadedAllImages = false;
		function preloadAllImages() {
			for (var i = 0; i < carouselItems.length; i++) {
				carouselItems[i].preload();
			}
			hasPreloadedAllImages = true;
		}

		var currentIndex = 0;

		$('.next', viewport).click(function() {
			if (!hasPreloadedAllImages) preloadAllImages();

			carouselItems[currentIndex].draw(leftItem);
			currentIndex = (currentIndex + 1) % carouselItems.length;
			carouselItems[currentIndex].draw(rightItem);
			tray.stop().css({'left': '0'}).animate({'left': '-400px'});

			return false;
		});

		$('.prev', viewport).click(function() {
			if (!hasPreloadedAllImages) preloadAllImages();

			carouselItems[currentIndex].draw(rightItem);
			currentIndex = (currentIndex + carouselItems.length - 1) % carouselItems.length;
			carouselItems[currentIndex].draw(leftItem);
			tray.stop().css({'left': '-400px'}).animate({'left': '0'});

			return false;
		});
	}
})(jQuery);
