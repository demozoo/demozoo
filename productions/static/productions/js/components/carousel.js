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
		var currentId = null;
		var currentIndex = 0;

		var viewport = this;
		viewport.html('<div class="viewport"><div class="tray"></div></div>');
		var tray = $('.tray', viewport);
		var currentBucket = $('<div class="bucket"></div>');
		tray.append(currentBucket);

		function loadData(carouselData) {
			carouselItems = [];

			var foundCurrentId = false;

			for (var i = 0; i < carouselData.length; i++) {
				itemType = itemTypes[carouselData[i].type];
				carouselItems[i] = new itemType(carouselData[i]);
				if (currentId == carouselData[i].id) {
					foundCurrentId = true;
					currentIndex = i;
				}
			}

			if (!foundCurrentId) {
				currentIndex = 0;
				currentId = carouselData[0].id;
			}

			carouselItems[currentIndex].draw(currentBucket);
		}
		loadData(carouselData);

		var hasPreloadedAllImages = false;
		function preloadAllImages() {
			for (var i = 0; i < carouselItems.length; i++) {
				carouselItems[i].preload();
			}
			hasPreloadedAllImages = true;
		}

		if (carouselItems.length > 1) {
			var prevLink = $('<a href="javascript:void(0);" class="nav prev">Previous</a>');
			viewport.append(prevLink);
			var nextLink = $('<a href="javascript:void(0);" class="nav next">Next</a>');
			viewport.append(nextLink);

			nextLink.click(function() {
				tray.stop(true, true);
				if (!hasPreloadedAllImages) preloadAllImages();

				currentIndex = (currentIndex + 1) % carouselItems.length;
				var currentItem = carouselItems[currentIndex];
				var oldBucket = currentBucket;
				currentBucket = $('<div class="bucket"></div>');
				tray.append(currentBucket);
				currentItem.draw(currentBucket);
				tray.animate({'left': '-400px'}, function() {
					oldBucket.remove();
					tray.css({'left': 0});
				});

				return false;
			});

			prevLink.click(function() {
				tray.stop(true, true);
				if (!hasPreloadedAllImages) preloadAllImages();

				currentIndex = (currentIndex + carouselItems.length - 1) % carouselItems.length;
				var currentItem = carouselItems[currentIndex];
				var newBucket = $('<div class="bucket"></div>');
				tray.css({'left': '-400px'});
				tray.prepend(newBucket);
				currentItem.draw(newBucket);
				tray.animate({'left': '0'}, function() {
					currentBucket.remove();
					currentBucket = newBucket;
				});

				return false;
			});
		}
	};
})(jQuery);
