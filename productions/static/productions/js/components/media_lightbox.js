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
		if (this.onClose) this.onClose();
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
			this.mediaItem.setSize(dims.maxMediaWidth, dims.maxMediaHeight);
		}
	};
	window.MediaLightbox.prototype.attach = function(mediaItemView) {
		this.mediaItem = mediaItemView;
		var dims = this.getAvailableDimensions();
		this.mediaItem.setSize(dims.maxMediaWidth, dims.maxMediaHeight);
	};
	window.MediaLightbox.prototype.detach = function() {
		if (this.mediaItem) {
			this.mediaItem.unload();
			this.mediaItem = null;
		}
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
	};

	window.ImageMediaItem.prototype.attachToLightbox = function(lightbox) {
		var self = this;

		var screenshotImg = $('<img />');
		var screenshot = new Image();

		screenshot.onload = function() {
			screenshotImg.get(0).src = screenshot.src;
			lightbox.mediaWrapper.append(screenshotImg);
			lightbox.attach(self);
		};

		self.setSize = function(maxImageWidth, maxImageHeight) {
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

			lightbox.setSize(finalWidth, finalHeight);
		};

		self.unload = function() {
			screenshotImg.remove();
		};

		screenshot.src = this.imageUrl;
	};

	$.fn.openImageInLightbox = function() {
		this.click(function(e) {
			if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
				/* probably means they want to open it in a new window, so let them... */
				return true;
			}

			var lightbox = new MediaLightbox();
			mediaItem = new ImageMediaItem(this.href);
			mediaItem.attachToLightbox(lightbox);

			return false;
		});
	};

	window.LightboxController = function() {
		this.lightbox = null;
		this.mediaItems = [];
		this.mediaItemsById = {};
		this.currentId = null;
		this.currentIndex = 0;
	};
	window.LightboxController.prototype.setMediaItems = function(mediaItems) {
		/* Assign a new mediaItems list to the lightbox controller. If the lightbox is
		currently open, and mediaItems contains an item with the current ID, ensure that
		currentIndex is updated to keep the lightbox at that item */
		this.mediaItems = [];
		var newMediaItemsById = {};
		var foundCurrentId = false;

		for (var i = 0; i < mediaItems.length; i++) {
			var newItem = mediaItems[i];
			/* look for an existing slide with this ID */
			var item = this.mediaItemsById[newItem.id];

			if (!item) {
				/* take the new item */
				item = newItem;
			}

			this.mediaItems[i] = item;
			newMediaItemsById[item.id] = item;

			/* if this item matches currentId, keep its place in the sequence */
			if (this.currentId == item.id) {
				foundCurrentId = true;
				this.currentIndex = i;
			}
		}
		this.mediaItemsById = newMediaItemsById;
	};
	window.LightboxController.prototype.openLightbox = function() {
		var self = this;
		if (!this.lightbox) {
			this.lightbox = new MediaLightbox();
			this.lightbox.onClose = function() {
				self.lightbox = null;
			};

			if (this.mediaItems.length > 1) {
				var prevLink = $('<a href="javascript:void(0);" class="nav prev">Previous</a>');
				prevLink.click(function() {
					self.currentIndex = (self.currentIndex + self.mediaItems.length - 1) % self.mediaItems.length;
					var item = self.mediaItems[self.currentIndex];
					self.currentId = item.id;
					self.lightbox.detach();
					item.attachToLightbox(self.lightbox);
				});
				this.lightbox.mediaWrapper.append(prevLink);
				var nextLink = $('<a href="javascript:void(0);" class="nav next">Next</a>');
				nextLink.click(function() {
					self.currentIndex = (self.currentIndex + 1) % self.mediaItems.length;
					var item = self.mediaItems[self.currentIndex];
					self.currentId = item.id;
					self.lightbox.detach();
					item.attachToLightbox(self.lightbox);
				});
				this.lightbox.mediaWrapper.append(nextLink);
			}

		}
	};
	window.LightboxController.prototype.openAtId = function(id) {
		item = this.mediaItemsById[id];
		if (item) {
			this.openLightbox();
			item.attachToLightbox(this.lightbox);
			this.currentId = id;
			for (var i = 0; i < this.mediaItems.length; i++) {
				if (this.mediaItems[i].id == id) {
					this.currentIndex = i;
					break;
				}
			}
		}
	};
})(jQuery);
