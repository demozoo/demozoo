(function($) {
	window.MediaLightbox = function() {
		this.mediaItem = null;

		this.overlay = $('<div class="media_lightbox_overlay"></div>');
		this.mediaWrapper = $('<div class="media_lightbox_wrapper"></div>');
		this.closeButton = $('<a href="javascript:void(0);" class="lightbox_close" title="Close">Close</div>');

		$('body').append(this.overlay, this.mediaWrapper);
		this.mediaWrapper.append(this.closeButton);

		this.overlay.css({
			'opacity': 0.5
		});

		var self = this;
		this.overlay.click(function() {
			self.close();
		});
		this.closeButton.click(function() {
			self.close();
		});
		this.onResize = function() {
			self.refreshSize();
		};
		$(window).resize(this.onResize);
		this.onKeydown = function(evt) {
			/* check for escape key */
			if (evt.keyCode == 27) self.close();
		};
		$(window).keydown(this.onKeydown);

		this.refreshSize();
	};

	window.MediaLightbox.prototype.close = function() {
		$(window).unbind('resize', this.onResize);
		$(window).unbind('keydown', this.onKeydown);
		this.overlay.remove();
		this.mediaWrapper.remove();
	};
	window.MediaLightbox.prototype.getAvailableDimensions = function() {
		var browserWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
		var browserHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;

		var maxMediaWidth = browserWidth - 64;
		var maxMediaHeight = browserHeight - 64;

		return {
			browserWidth: browserWidth,
			browserHeight: browserHeight,
			maxMediaWidth: maxMediaWidth,
			maxMediaHeight: maxMediaHeight
		};
	};
	window.MediaLightbox.prototype.refreshSize = function() {
		/* Adjust element sizes to fit browser size. Called on initial load and on resize. */
		var dims = this.getAvailableDimensions();

		this.overlay.css({
			'width': dims.browserWidth,
			'height': dims.browserHeight
		});

		if (this.mediaItem) {
			this.mediaItem.resizeLightboxContent(this, dims.maxMediaWidth, dims.maxMediaHeight);
		}
	};
	window.MediaLightbox.prototype.attachMediaItem = function(mediaItem) {
		this.closeButton.siblings().remove();
		this.mediaItem = mediaItem;
		var dims = this.getAvailableDimensions();
		this.mediaItem.drawLightboxContent(this, this.mediaWrapper, dims.maxMediaWidth, dims.maxMediaHeight);
	};
	window.MediaLightbox.prototype.setSize = function(width, height) {
		var dims = this.getAvailableDimensions();
		this.mediaWrapper.css({
			'left': (dims.browserWidth - (width + 32)) / 2 + 'px',
			'top': (dims.browserHeight - (height + 32)) / 2 + 'px',
			'width': width + 'px',
			'height': height + 24 + 'px'
		});
	};

	window.ImageMediaItem = function(imageUrl) {
		this.imageUrl = imageUrl;
		this.screenshotImg = $('<img />');
		this.screenshot = new Image();
		this.isLoaded = false;
	};

	window.ImageMediaItem.prototype.drawLightboxContent = function(lightbox, container, maxImageWidth, maxImageHeight) {
		var self = this;

		this.screenshot.onload = function() {
			self.isLoaded = true;
			self.screenshotImg.get(0).src = self.screenshot.src;
			container.append(self.screenshotImg);
			self.setImageSize(lightbox, maxImageWidth, maxImageHeight);
		};

		this.screenshot.src = this.imageUrl;
	};

	window.ImageMediaItem.prototype.setImageSize = function(lightbox, maxImageWidth, maxImageHeight) {
		var imageWidth = this.screenshot.width || 480;
		var imageHeight = this.screenshot.height || 340;

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

		this.screenshotImg.attr({
			'width': finalWidth, 'height': finalHeight, 'class': (pixelated ? 'pixelated' : '')
		});

		lightbox.setSize(finalWidth, finalHeight);
	};

	window.ImageMediaItem.prototype.resizeLightboxContent = function(lightbox, maxImageWidth, maxImageHeight) {
		if (!this.isLoaded) return;
		this.setImageSize(lightbox, maxImageWidth, maxImageHeight);
	};

	$.fn.openImageInLightbox = function() {
		this.click(function(e) {
			if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
				/* probably means they want to open it in a new window, so let them... */
				return true;
			}

			var lightbox = new MediaLightbox();
			mediaItem = new ImageMediaItem(this.href);
			lightbox.attachMediaItem(mediaItem);

			return false;
		});
	};
})(jQuery);
