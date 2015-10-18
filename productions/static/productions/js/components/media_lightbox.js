(function($) {
	window.MediaLightbox = function(getNaturalSize) {
		var self = {};

		var overlay = $('<div class="media_lightbox_overlay"></div>');
		var mediaWrapper = $('<div class="media_lightbox_wrapper"></div>');
		var closeButton = $('<a href="javascript:void(0);" class="lightbox_close" title="Close">Close</div>');

		$('body').append(overlay, mediaWrapper);
		mediaWrapper.append(closeButton);

		var browserWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
		var browserHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
		overlay.css({
			'opacity': 0.5,
			'width': browserWidth,
			'height': browserHeight
		});

		function setSize() {
			var browserWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
			var browserHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;

			var maxMediaWidth = browserWidth - 64;
			var maxMediaHeight = browserHeight - 64;

			var mediaSize = getNaturalSize(maxMediaWidth, maxMediaHeight);

			var finalWidth = mediaSize[0];
			var finalHeight = mediaSize[1];

			mediaWrapper.css({
				'left': (browserWidth - (finalWidth + 32)) / 2 + 'px',
				'top': (browserHeight - (finalHeight + 32)) / 2 + 'px',
				'width': finalWidth + 'px',
				'height': finalHeight + 24 + 'px'
			});
			overlay.css({
				'width': browserWidth,
				'height': browserHeight
			});

		}

		setSize();

		$(window).resize(setSize);

		function checkForEscape(evt) {
			if (evt.keyCode == 27) close();
		}
		function close() {
			$(window).unbind('resize', setSize);
			$(window).unbind('keydown', checkForEscape);
			overlay.remove();
			mediaWrapper.remove();
		}
		overlay.click(close);
		closeButton.click(close);
		$(window).keydown(checkForEscape);

		self.setSize = setSize;
		self.mediaWrapper = mediaWrapper;

		return self;
	};

	$.fn.openImageInLightbox = function() {
		this.click(function(e) {
			if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
				/* probably means they want to open it in a new window, so let them... */
				return true;
			}

			var screenshotImg = $('<img />');
			var screenshot = new Image();

			var lightbox = MediaLightbox(function(maxImageWidth, maxImageHeight) {

				var imageWidth = screenshot.width || 480;
				var imageHeight = screenshot.height || 340;

				var finalWidth, finalHeight, pixelated;

				if (
					imageWidth <= 400 && maxImageWidth >= imageWidth * 2 &&
					imageHeight <= 300 && maxImageHeight >= imageHeight * 2
				) {
					/* show image at double size */
					finalWidth = imageWidth * 2;
					finalHeight = imageHeight * 2;
					pixelated = true;
				} else {
					var fullWidth = Math.min(imageWidth, maxImageWidth);
					var fullHeight = Math.min(imageHeight, maxImageHeight);

					var heightAtFullWidth = (fullWidth * imageHeight/imageWidth);
					var widthAtFullHeight = (fullHeight * imageWidth/imageHeight);

					if (heightAtFullWidth <= maxImageHeight) {
						finalWidth = fullWidth;
						finalHeight = Math.round(heightAtFullWidth);
					} else {
						finalWidth = Math.round(widthAtFullHeight);
						finalHeight = fullHeight;
					}
					pixelated = false;
				}

				screenshotImg.attr({
					'width': finalWidth, 'height': finalHeight, 'class': (pixelated ? 'pixelated' : '')
				});

				return [finalWidth, finalHeight];

			});

			screenshot.onload = function() {
				lightbox.setSize();

				screenshotImg.get(0).src = screenshot.src;
				lightbox.mediaWrapper.append(screenshotImg);
			};
			
			screenshot.src = this.href;
			
			
			return false;
		});
	};
})(jQuery);
