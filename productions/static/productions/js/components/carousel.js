(function($) {
	$.fn.carousel = function(carouselData) {
		if (carouselData.length === 0) return;

		function Screenshot(fullData) {
			this.isProcessing = fullData['is_processing'];
			this.data = fullData.data;
		}
		Screenshot.prototype.preload = function() {
			var src = this.data['standard_url'];
			var img = new Image();
			img.src = src;
		};
		Screenshot.prototype.draw = function(container) {
			if (this.isProcessing) {
				container.html('<div class="screenshot"><img src="/static/images/screenshot_loading.gif" width="32" height="32" alt="" /></div>');
			} else {
				var link = $('<a class="screenshot"></a>').attr({'href': this.data['original_url']});
				var img = $('<img>').attr({'src': this.data['standard_url'], 'width': this.data['standard_width'], 'height': this.data['standard_height']});
				link.append(img);
				container.html(link);
				link.openImageInLightbox();
			}
		};

		var itemTypes = {
			'screenshot': Screenshot
		};

		var carouselItems = [];
		for (var i = 0; i < carouselData.length; i++) {
			itemType = itemTypes[carouselData[i].type];
			carouselItems[i] = new itemType(carouselData[i]);
		}

		var viewport = this;
		viewport.html('<div class="viewport"><div class="tray"></div></div>');
		var tray = $('.tray', viewport);

		var hasPreloadedAllImages = false;
		function preloadAllImages() {
			for (var i = 0; i < carouselItems.length; i++) {
				carouselItems[i].preload();
			}
			hasPreloadedAllImages = true;
		}

		var currentIndex = 0;
		var currentItem = $('<div class="carousel_item"></div>');
		tray.append(currentItem);
		carouselItems[currentIndex].draw(currentItem);

		if (carouselItems.length > 1) {
			var prevLink = $('<a href="javascript:void(0);" class="nav prev">Previous</a>');
			viewport.append(prevLink);
			var nextLink = $('<a href="javascript:void(0);" class="nav next">Next</a>');
			viewport.append(nextLink);

			nextLink.click(function() {
				tray.stop(true, true);
				if (!hasPreloadedAllImages) preloadAllImages();

				currentIndex = (currentIndex + 1) % carouselItems.length;
				var newItem = $('<div class="carousel_item"></div>');
				tray.append(newItem);
				carouselItems[currentIndex].draw(newItem);
				tray.animate({'left': '-400px'}, function() {
					currentItem.remove();
					currentItem = newItem;
					tray.css({'left': 0});
				});

				return false;
			});

			prevLink.click(function() {
				tray.stop(true, true);
				if (!hasPreloadedAllImages) preloadAllImages();

				currentIndex = (currentIndex + carouselItems.length - 1) % carouselItems.length;
				var newItem = $('<div class="carousel_item"></div>');
				tray.css({'left': '-400px'});
				tray.prepend(newItem);
				carouselItems[currentIndex].draw(newItem);
				tray.animate({'left': '0'}, function() {
					currentItem.remove();
					currentItem = newItem;
				});

				return false;
			});
		}
	};
})(jQuery);
