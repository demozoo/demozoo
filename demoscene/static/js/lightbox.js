(function() {
	var self = {};
	
	var isInitialised = false;
	var isShowing = false;
	var lightboxOuter, lightboxElem, lightboxContent, lightboxClose;
	
	function init() {
		if (isInitialised) return;
		
		lightboxOuter = $('<div id="lightbox_outer"></div>');
		var lightboxMiddle = $('<div id="lightbox_middle"></div>');
		lightboxElem = $('<div id="lightbox"></div>');
		lightboxClose = $('<a href="javascript:void(0);" class="lightbox_close" title="Close">Close</div>');
		lightboxContent = $('<div></div>');
		lightboxElem.append(lightboxClose, lightboxContent);
		lightboxMiddle.append(lightboxElem);
		lightboxOuter.append(lightboxMiddle);
		$('body').append(lightboxOuter);
		lightboxOuter.click(self.close);
		lightboxElem.click(function(e) {
			e.stopPropagation();
		});
		lightboxClose.click(self.close);
		lightboxOuter.hide();
		isInitialised = true;
	}
	
	function setSize() {
		var browserHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
		lightboxElem.css({'max-height': browserHeight - 48 + 'px'});
	}
	function checkForEscape(evt) {
		if (evt.keyCode == 27) self.close();
	}
	function show(opts) {
		if (isShowing) return;
		lightboxOuter.show();
		isShowing = true;

		if (opts && opts.focusEmptyInput) {
			/* focus on the first *empty* input field */
			try {$(':input:visible[value=""]', lightboxContent)[0].focus();}catch(_){}
		} else {
			try {$(':input:visible', lightboxContent)[0].focus();}catch(_){}
		}

		setSize();
		$(window).keydown(checkForEscape);
		$(window).resize(setSize);
	}
	
	self.openContent = function(content, onLoadCallback, opts) {
		init();
		lightboxContent.html(content);
		show(opts);
		if (onLoadCallback) onLoadCallback(lightboxElem);
	};

	self.openUrl = function(url, onLoadCallback, opts) {
		init();
		$('body').addClass('loading');
		lightboxContent.load(url, function() {
			$('body').removeClass('loading');
			show(opts);
			if (onLoadCallback) onLoadCallback(lightboxElem);
		});
	};
	self.close = function() {
		if (!isShowing) return;
		$(window).unbind('resize', setSize);
		$(window).unbind('keydown', checkForEscape);
		lightboxOuter.hide();
		isShowing = false;
	};

	window.Lightbox = self;
})();
