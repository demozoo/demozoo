(function($) {
	var popup;

	$.fn.thumbPreview = function() {
		$(this).hover(function() {
			if (!popup) {
				popup = $('<div class="thumb_preview_popup"><img></div>');
				$('body').append(popup);
				popup.css({
					'position': 'absolute', 'z-index': 100,
					'height': '100px', 'width': '133px', 'margin-top': '-125px', 'margin-left': '-76px',
					'padding': '10px',
					'line-height': '36px', 'text-align': 'center',
					'background-color': '#eee', 'border': '1px solid #ccc', 'border-radius': '4px'
				});
			}
			var thumbPos = $(this).offset();
			var thumbImg = $(this).find('img');
			var left = Math.max(thumbPos.left + $(this).width() / 2, 76);

			var thumbWidth = thumbImg.data('natural-width');
			var thumbHeight = thumbImg.data('natural-height');
			/* scale down by whatever factor is required to get both width and height within 133x100 */
			var widthScale = Math.min(133 / thumbWidth, 1);
			var heightScale = Math.min(100 / thumbHeight, 1);
			var scale = Math.min(widthScale, heightScale);

			width = Math.floor(thumbWidth * scale);
			height = Math.floor(thumbHeight * scale);

			popup.find('img').attr({'src': thumbImg.attr('src'), 'width': width, 'height': height});
			popup.css({'top': thumbPos.top + 'px', 'left': left + 'px'}).show();
		}, function() {
			popup.hide();
		});
	};
})(jQuery);
