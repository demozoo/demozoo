(function($) {

	/* Define carousel item types */

	function buildStandardScreenshotImage(data) {
		var img = $('<img>').attr({'src': data['standard_url']});
		if (data['standard_width'] < 200 && data['standard_height'] < 150) {
			/* tiny screen, e.g. GBC - scale to double size */
			img.attr({
				'width': data['standard_width'] * 2,
				'height': data['standard_height'] * 2,
				'class': 'pixelated'
			});
		} else {
			img.attr({'width': data['standard_width'], 'height': data['standard_height']});
		}
		return img;
	}

	function Screenshot(fullData) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
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
			var img = buildStandardScreenshotImage(this.data);
			link.append(img);
			container.html(link);
			link.openImageInLightbox();
		}
	};
	Screenshot.prototype.unload = function() {};

	function Ansi(fullData) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
		this.data = fullData.data;
	}
	Ansi.prototype.preload = function() {
		var src = this.data['standard_url'];
		var img = new Image();
		img.src = src;
	};
	Ansi.prototype.draw = function(container) {
		if (this.isProcessing) {
			container.html('<div class="screenshot"><img src="/static/images/screenshot_loading.gif" width="32" height="32" alt="" /></div>');
		} else {
			var link = $('<a class="screenshot"></a>').attr({'href': this.data['original_url']});
			var img = buildStandardScreenshotImage(this.data);
			link.append(img);
			container.html(link);

			var ansiUrl = this.data['ansi_url'];

			link.click(function() {
				AnsiLove.render(ansiUrl, function (canvas, sauce) {
					lightbox.mediaWrapper.append(canvas);
				}, {});
				var lightbox = MediaLightbox(function(maxWidth, maxHeight) {
					return [640, 480];
				});
				return false;
			});
		}
	};
	Ansi.prototype.unload = function() {};

	function buildMosaic(items, addLinks) {
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
		var mosaic = $('<div class="mosaic"></div>').css({'width': width + 'px', 'height': height + 'px'});
		for (i = 0; i < items.length; i++) {
			var imgData = items[i];
			var tile;
			if (addLinks) {
				tile = $('<a class="tile"></a>').attr({
					'href': imgData['original_url']
				});
				tile.openImageInLightbox();
			} else {
				tile = $('<div class="tile"></div>');
			}
			tile.css({
				'width': width/2 + 'px',
				'height': height/2 + 'px',
				'line-height': height/2 + 'px'
			});
			var img = $('<img>').attr({
				'src': imgData['standard_url'],
				'width': zoom ? imgData['standard_width'] : imgData['standard_width'] / 2,
				'height': zoom ? imgData['standard_height'] : imgData['standard_height'] / 2
			});
			if (zoom) img.addClass('pixelated');
			tile.append(img);
			mosaic.append(tile);
		}
		return mosaic;
	}

	function Mosaic(fullData) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
		this.data = fullData.data;
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
		var mosaic = buildMosaic(this.data, true);
		container.html(mosaic);
	};
	Mosaic.prototype.unload = function() {};

	function Video(fullData) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
		this.data = fullData.data;
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
			img = buildMosaic(videoData['mosaic'], false);
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

		link.click(function() {
			var videoElement = $(videoData['embed_code']);
			var lightbox = MediaLightbox(function(maxWidth, maxHeight) {
				var videoWidth = videoData['video_width'];
				var videoHeight = videoData['video_height'];

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

				videoElement.attr('width', finalWidth);
				videoElement.attr('height', finalHeight);
				return [finalWidth, finalHeight];
			});
			lightbox.mediaWrapper.append(videoElement);
			return false;
		});
	};
	Video.prototype.unload = function() {};

	function CowbellAudio(fullData) {
		this.isProcessing = fullData['is_processing'];
		this.id = fullData['id'];
		this.data = fullData.data;
		this.ui = null;
	}
	CowbellAudio.prototype.draw = function(container) {
		var cowbellPlayer = $('<div class="cowbell-player"></div>');
		container.html(cowbellPlayer);
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

	var itemTypes = {
		'screenshot': Screenshot,
		'mosaic': Mosaic,
		'video': Video,
		'cowbell-audio': CowbellAudio,
		'ansi': Ansi
	};

	/* Constructor for a carousel */

	$.fn.carousel = function(carouselData, reloadUrl) {
		if (carouselData.length === 0) return;

		var carouselItems = [];
		var carouselItemsById = {};
		var currentId = null;
		var currentIndex = 0;

		var viewport = this;
		var tray;
		var currentBucket;

		var hasInitialisedViewport = false;
		function initViewport() {
			viewport.html('<div class="viewport"><div class="tray"></div></div>');
			tray = $('.tray', viewport);
			currentBucket = $('<div class="bucket"></div>');
			tray.append(currentBucket);
			hasInitialisedViewport = true;
		}

		var hasPreloadedAllItems = true;
		var itemsNeedingPreload = [];

		function loadData(carouselData) {
			carouselItems = [];
			var newCarouselItemsById = {};

			var foundCurrentId = false;
			var needReload = false;
			var itemCount = 0;

			for (var i = 0; i < carouselData.length; i++) {
				/* look for an existing carousel item with this ID */
				var carouselItem = carouselItemsById[carouselData[i].id];

				if (!carouselItem || carouselItem.isProcessing) {
					/* item not already found, or was previously in processing, so create it as new */
					itemType = itemTypes[carouselData[i].type];
					if (itemType) {
						carouselItem = new itemType(carouselData[i]);
						if (carouselItem.preload) {
							itemsNeedingPreload.push(carouselItem);
							hasPreloadedAllItems = false;
						}
					} else {
						/* skip unidentified item types */
						continue;
					}
				}
				carouselItems[itemCount] = carouselItem;
				newCarouselItemsById[carouselData[i].id] = carouselItem;

				if (currentId == carouselData[i].id) {
					foundCurrentId = true;
					currentIndex = itemCount;
				}
				if (carouselData[i]['is_processing']) {
					needReload = true;
				}
				itemCount++;
			}

			if (itemCount === 0) return;

			if (!hasInitialisedViewport) initViewport();

			if (!foundCurrentId) {
				currentIndex = 0;
				currentId = carouselItems[0].id;
			}

			carouselItems[currentIndex].draw(currentBucket);
			carouselItemsById = newCarouselItemsById;

			if (needReload) {
				setTimeout(function() {
					$.getJSON(reloadUrl, loadData);
				}, 5000);
			}
		}
		loadData(carouselData);

		function preloadAllItems() {
			for (var i = 0; i < itemsNeedingPreload.length; i++) {
				itemsNeedingPreload[i].preload();
			}
			hasPreloadedAllItems = true;
			itemsNeedingPreload = [];
		}

		if (carouselItems.length > 1) {
			var prevLink = $('<a href="javascript:void(0);" class="nav prev">Previous</a>');
			viewport.append(prevLink);
			var nextLink = $('<a href="javascript:void(0);" class="nav next">Next</a>');
			viewport.append(nextLink);

			nextLink.click(function() {
				tray.stop(true, true);
				if (!hasPreloadedAllItems) preloadAllItems();

				var oldItem = carouselItems[currentIndex];
				currentIndex = (currentIndex + 1) % carouselItems.length;
				var currentItem = carouselItems[currentIndex];
				currentId = currentItem.id;
				var oldBucket = currentBucket;
				currentBucket = $('<div class="bucket"></div>');
				tray.append(currentBucket);
				currentItem.draw(currentBucket);
				tray.animate({'left': '-400px'}, function() {
					oldItem.unload();
					oldBucket.remove();
					tray.css({'left': 0});
				});

				return false;
			});

			prevLink.click(function() {
				tray.stop(true, true);
				if (!hasPreloadedAllItems) preloadAllItems();

				var oldItem = carouselItems[currentIndex];
				currentIndex = (currentIndex + carouselItems.length - 1) % carouselItems.length;
				var currentItem = carouselItems[currentIndex];
				currentId = currentItem.id;
				var newBucket = $('<div class="bucket"></div>');
				tray.css({'left': '-400px'});
				tray.prepend(newBucket);
				currentItem.draw(newBucket);
				tray.animate({'left': '0'}, function() {
					oldItem.unload();
					currentBucket.remove();
					currentBucket = newBucket;
				});

				return false;
			});
		}
	};
})(jQuery);
