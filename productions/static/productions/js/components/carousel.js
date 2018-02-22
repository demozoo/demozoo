(function($) {

	/* Define carousel item types */

	function Screenshot(fullData, carouselController) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
		this.data = fullData.data;
		this.carouselController = carouselController;

		this.lightboxItem = new ImageMediaItem(this.data['original_url']);
	}

	Screenshot.prototype.preload = function() {
		var src = this.data['standard_url'];
		var img = new Image();
		img.src = src;
	};

	Screenshot.prototype.attachToLightbox = function(lightbox, autoplay) {
		this.lightboxItem.attachToLightbox(lightbox, autoplay);
	};

	Screenshot.prototype.draw = function(container) {
		if (this.isProcessing) {
			container.html('<div class="screenshot"><img src="/static/images/screenshot_loading.gif" width="32" height="32" alt="" /></div>');
		} else {
			var link = $('<a class="screenshot"></a>').attr({'href': this.data['original_url']});
			var img = $('<img />').attr({'src': this.data['standard_url']});
			if (this.data['standard_width'] < 200 && this.data['standard_height'] < 150) {
				/* tiny screen, e.g. GBC - scale to double size */
				img.attr({
					'width': this.data['standard_width'] * 2,
					'height': this.data['standard_height'] * 2,
					'class': 'pixelated'
				});
			} else {
				img.attr({'width': this.data['standard_width'], 'height': this.data['standard_height']});
			}
			link.append(img);
			container.html(link);

			var self = this;
			link.click(function(e) {
				if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
					/* probably means they want to open it in a new window, so let them... */
					return true;
				}

				self.carouselController.openLightboxAtId(self.id);
				return false;
			});
		}
	};

	Screenshot.prototype.unload = function() {};

	function buildMosaic(items, addLinks, carouselController) {
		var width = 0, height = 0, i;
		for (i = 0; i < items.length; i++) {
			width = Math.max(width, items[i]['standard_width']);
			height = Math.max(height, items[i]['standard_height']);
		}
		var zoom = false;
		if (width < 200 & height < 150) {
			/* tiny screen, e.g. GBC - scale to double size */
			zoom = true;
			width *= 2; height *= 2;
		}
		var mosaic = $('<figure class="mosaic" />');

		function addTileLightboxAction(tile, id) {
			tile.click(function(e) {
				if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
					/* probably means they want to open it in a new window, so let them... */
					return true;
				}

				carouselController.openLightboxAtId(id);
				return false;
			});
		}

		for (i = 0; i < items.length; i++) {
			var imgData = items[i];
			var tile;

			if (addLinks) {
				tile = $('<a class="tile"></a>').attr({
					'href': imgData['original_url']
				});
				addTileLightboxAction(tile, imgData['id']);
			} else {
				tile = $('<div class="mosaic__tile"></div>');
			}

			var img = $('<img>').attr({
				'src': imgData['standard_url'],
				'class': 'mosaic__image',
			});

			if (zoom) img.addClass('pixelated');

			tile.append(img);
			mosaic.append(tile);
		}
		return mosaic;
	}

	function Mosaic(fullData, carouselController) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
		this.data = fullData.data;
		this.carouselController = carouselController;
	}

	Mosaic.prototype.preload = function() {
		for (var i = 0; i < this.data.length; i++) {
			var src = this.data[i]['standard_url'];
			var img = new Image();
			img.src = src;
		}
	};

	Mosaic.prototype.draw = function(container) {
		/* use the largest screenshot dimension as the mosaic size;
		each tile will be half this in each direction, padded as necessary.
		If all screenshots are equal size (hopefully the most common case),
		no padding will be needed. */
		var mosaic = buildMosaic(this.data, true, this.carouselController);
		container.html(mosaic);
	};

	Mosaic.prototype.unload = function() {};

	function Video(fullData, carouselController) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
		this.data = fullData.data;
		this.carouselController = carouselController;
	}
	Video.prototype.preload = function() {
		for (var i = 0; i < this.data.length; i++) {
			var src = this.data['thumbnail_url'];
			var img = new Image();
			img.src = src;
		}
	};

	Video.prototype.draw = function(container) {
		var videoData = this.data;

		var link = $('<a class="video"><div class="play"></div></a>').attr({'href': this.data['url']});
		var img;
		if (videoData['mosaic']) {
			img = buildMosaic(videoData['mosaic'], false, null);
		} else {
			img = $('<img>').attr({'src': this.data['thumbnail_url']});
			if (this.data['thumbnail_width'] < 200 && this.data['thumbnail_height'] < 150) {
				img.attr({
					'width': this.data['thumbnail_width'] * 2,
					'height': this.data['thumbnail_height'] * 2,
					'class': 'pixelated'
				});
			} else {
				img.attr({
					'width': this.data['thumbnail_width'],
					'height': this.data['thumbnail_height']
				});
			}
		}
		link.prepend(img);
		container.html(link);

		var self = this;

		link.click(function(e) {
			if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
				/* probably means they want to open it in a new window, so let them... */
				return true;
			}

			self.carouselController.openLightboxAtId(self.id);
			return false;
		});
	};

	Video.prototype.attachToLightbox = function(lightbox, autoplay) {
		var self = {};

		var videoWidth = this.data['video_width'];
		var videoHeight = this.data['video_height'];

		var videoElement = $(this.data[autoplay ? 'embed_code' : 'embed_code_without_autoplay']);
		lightbox.mediaWrapper.append(videoElement);

		self.setSize = function(maxWidth, maxHeight) {
			var fullWidth = Math.min(videoWidth, maxWidth);
			var fullHeight = Math.min(videoHeight, maxHeight);

			var heightAtFullWidth = (fullWidth * videoHeight/videoWidth);
			var widthAtFullHeight = (fullHeight * videoWidth/videoHeight);

			if (heightAtFullWidth <= maxHeight) {
				finalWidth = fullWidth;
				finalHeight = Math.round(heightAtFullWidth);
			} else {
				finalWidth = Math.round(widthAtFullHeight);
				finalHeight = fullHeight;
			}

			lightbox.setSize(finalWidth, finalHeight);
			videoElement.attr('width', finalWidth);
			videoElement.attr('height', finalHeight);
		};

		self.unload = function() {
			videoElement.remove();
		};
		lightbox.attach(self);
	};

	Video.prototype.unload = function() {};

	function CowbellAudio(fullData, carouselController) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
		this.data = fullData.data;
		this.ui = null;
		this.carouselController = carouselController;
	}

	CowbellAudio.prototype.draw = function(container) {
		var cowbellPlayer = $('<div class="cowbell-player"></div>');
		container.html(cowbellPlayer);
		if (this.data.image) {
			cowbellPlayer.css({'background-image': 'url(' + this.data.image.url + ')'});
		} else {
			cowbellPlayer.addClass('no-artwork');
		}
		this.ui = Cowbell.createPlayer(cowbellPlayer.get(0), {
			'url': this.data.url,
			'player': eval(this.data.player),
			'playerOpts': this.data.playerOpts,
			'ui': Cowbell.UI.Roundel
		});
	};

	CowbellAudio.prototype.unload = function() {
		if (this.ui) {
			this.ui.open(null);
		}
	};

	var slideTypes = {
		'screenshot': Screenshot,
		'mosaic': Mosaic,
		'video': Video,
		'cowbell-audio': CowbellAudio
	};

	/* Constructor for a carousel */

	function CarouselView(viewport) {
		this.viewport = viewport;
		this.viewport.html('<div class="viewport"><div class="tray"></div></div>');
		this.tray = $('.tray', this.viewport);
		this.currentBucket = $('<div class="bucket"></div>');
		this.tray.append(this.currentBucket);

		this.prevLink = $('<a href="javascript:void(0);" class="nav prev">Previous</a>');
		this.viewport.append(this.prevLink);
		this.nextLink = $('<a href="javascript:void(0);" class="nav next">Next</a>');
		this.viewport.append(this.nextLink);

		var self = this;
		this.prevLink.click(function() {
			if (self.onClickPrev) self.onClickPrev();
			return false;
		});
		this.nextLink.click(function() {
			if (self.onClickNext) self.onClickNext();
			return false;
		});

		this.currentSlide = null;
	}

	CarouselView.prototype.hidePrevNextLinks = function() {
		this.prevLink.hide();
		this.nextLink.hide();
	};

	CarouselView.prototype.showPrevNextLinks = function() {
		this.prevLink.show();
		this.nextLink.show();
	};

	CarouselView.prototype.drawSlide = function(slide) {
		if (this.currentSlide) this.currentSlide.unload();
		slide.draw(this.currentBucket);
		this.currentSlide = slide;
	};

	CarouselView.prototype.scrollSlideInFromRight = function(newSlide) {
		this.tray.stop(true, true);

		var oldSlide = this.currentSlide;
		var oldBucket = this.currentBucket;
		this.currentBucket = $('<div class="bucket"></div>');
		this.tray.append(this.currentBucket);
		newSlide.draw(this.currentBucket);
		this.currentSlide = newSlide;
		var self = this;
		this.tray.animate({'left': '-400px'}, function() {
			if (oldSlide) oldSlide.unload();
			oldBucket.remove();
			self.tray.css({'left': 0});
		});
	};

	CarouselView.prototype.scrollSlideInFromLeft = function(newSlide) {
		this.tray.stop(true, true);

		var oldSlide = this.currentSlide;
		var newBucket = $('<div class="bucket"></div>');
		this.tray.css({'left': '-400px'});
		this.tray.prepend(newBucket);
		newSlide.draw(newBucket);
		var self = this;
		this.tray.animate({'left': '0'}, function() {
			if (oldSlide) oldSlide.unload();
			self.currentBucket.remove();
			self.currentBucket = newBucket;
			self.currentSlide = newSlide;
		});
	};

	function CarouselController(viewport) {
		this.view = new CarouselView(viewport);
		this.lightboxController = new LightboxController();
		this.slides = [];
		this.slidesById = {};
		this.currentId = null;
		this.currentIndex = 0;

		this.slidesNeedingPreload = [];

		var self = this;
		this.view.onClickNext = function() {
			self.preloadSlides();

			self.currentIndex = (self.currentIndex + 1) % self.slides.length;
			var newSlide = self.slides[self.currentIndex];
			self.currentId = newSlide.id;
			self.view.scrollSlideInFromRight(newSlide);
		};

		this.view.onClickPrev = function() {
			self.preloadSlides();

			self.currentIndex = (self.currentIndex + self.slides.length - 1) % self.slides.length;
			var newSlide = self.slides[self.currentIndex];
			self.currentId = newSlide.id;
			self.view.scrollSlideInFromLeft(newSlide);
		};

		this.lightboxController.onNavigateToItem = function(item) {
			var newSlide = self.slidesById[item.id];
			if (newSlide) {
				self.currentId = newSlide.id;
				for (var i = 0; i < self.slides.length; i++) {
					if (self.slides[i].id == newSlide.id) {
						self.currentIndex = i;
						break;
					}
				}
				self.view.drawSlide(newSlide);
			}
		}
	}

	CarouselController.prototype.unpackCarouselData = function(carouselData) {
		/* unpack JSON into a list of slide objects */
		var slides = [];

		for (var i = 0; i < carouselData.length; i++) {
			slideType = slideTypes[carouselData[i].type];
			if (slideType) {
				slide = new slideType(carouselData[i], this);
				slides.push(slide);
			} else {
				/* skip unidentified item types */
				continue;
			}
		}

		return slides;
	};

	CarouselController.prototype.loadSlides = function(newSlides) {
		/* Build a new slides list based on the passed newSlides list, but
		preserving existing instances if they have a matching ID and were not previously in processing */

		this.slides = [];
		var newSlidesById = {};
		var foundCurrentId = false;
		var lightboxItems = [];

		for (var i = 0; i < newSlides.length; i++) {
			var newSlide = newSlides[i];
			/* look for an existing slide with this ID */
			var slide = this.slidesById[newSlide.id];

			if (!slide || slide.isProcessing) {
				/* item not found, or was previously in processing, so take the new one */
				slide = newSlide;
				/* add new item to 'things that need preloading', if applicable */
				if (slide.preload) {
					this.slidesNeedingPreload.push(slide);
				}
			}

			/* add old or new item to the final slides list */
			this.slides[i] = slide;
			newSlidesById[slide.id] = slide;

			if (slide.attachToLightbox && !slide.isProcessing) {
				lightboxItems.push(slide);
			}

			/* if this item matches currentId, keep its place in the sequence */
			if (this.currentId == slide.id) {
				foundCurrentId = true;
				this.currentIndex = i;
			}
		}

		if (!foundCurrentId) {
			this.currentIndex = 0;
			this.currentId = this.slides[0].id;
		}

		this.slidesById = newSlidesById;
		this.lightboxController.setMediaItems(lightboxItems);

		if (this.slides.length > 1) {
			this.view.showPrevNextLinks();
		} else {
			this.view.hidePrevNextLinks();
		}

		this.view.drawSlide(this.slides[this.currentIndex]);
	};

	CarouselController.prototype.preloadSlides = function() {
		for (var i = 0; i < this.slidesNeedingPreload.length; i++) {
			this.slidesNeedingPreload[i].preload();
		}
		this.slidesNeedingPreload = [];
	};

	CarouselController.prototype.openLightboxAtId = function(id) {
		this.lightboxController.openAtId(id);
	};

	$.fn.carousel = function(carouselData, reloadUrl) {
		if (carouselData.length === 0) return;

		function needReload(slides) {
			/* return true iff any of the passed slides have isProcessing = true */
			for (var i = 0; i < slides.length; i++) {
				if (slides[i].isProcessing) return true;
			}
			return false;
		}

		var controller = new CarouselController(this);

		function scheduleReload() {
			setTimeout(function() {
				$.getJSON(reloadUrl, function(carouselData) {
					var slides = controller.unpackCarouselData(carouselData);
					controller.loadSlides(slides);
					if (needReload(slides)) scheduleReload();
				});
			}, 5000);
		}

		var slides = controller.unpackCarouselData(carouselData);
		controller.loadSlides(slides);
		if (needReload(slides)) scheduleReload();
	};
})(jQuery);
