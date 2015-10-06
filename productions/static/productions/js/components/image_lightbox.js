(function($) {
	$.fn.openImageInLightbox = function() {
		this.click(function(e) {
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
				
				var maxImageWidth = browserWidth - 64;
				var maxImageHeight = browserHeight - 64;

				var finalWidth, finalHeight;

				if (
					imageWidth <= 400 && maxImageWidth >= imageWidth * 2 &&
					imageHeight <= 300 && maxImageHeight >= imageHeight * 2
				) {
					/* show image at double size */
					finalWidth = imageWidth * 2;
					finalHeight = imageHeight * 2;
					renderStyle = 'pixelated';
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
					renderStyle = 'auto';
				}

				screenshotImg.attr({
					'width': finalWidth, 'height': finalHeight
				}).css({
					'image-rendering': renderStyle
				});
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
			};
			
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
		});
	};
})(jQuery);
