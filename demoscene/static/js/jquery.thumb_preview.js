(function($) {
    var popup;

    var WIDTH = 200;
    var HEIGHT = 150;

    $.fn.thumbPreview = function() {
        $(this).hover(function() {
            if (!popup) {
                popup = $('<div class="thumb_preview_popup"><img></div>');
                $('body').append(popup);
                popup.css({
                    'position': 'absolute', 'z-index': 100,
                    'height': HEIGHT + 'px', 'width': WIDTH + 'px', 'margin-top': -(HEIGHT + 25) + 'px', 'margin-left': -(WIDTH / 2) + 'px',
                    'padding': '10px',
                    'line-height': HEIGHT + 'px', 'text-align': 'center',
                    'background-color': '#eee', 'border': '1px solid #ccc', 'border-radius': '4px'
                });
                popup.find('img').css({'vertical-align': 'middle'});
            }
            var thumbPos = $(this).offset();
            var thumbImg = $(this).find('img');
            var left = Math.max(thumbPos.left + $(this).width() / 2, WIDTH / 2);

            var thumbWidth = thumbImg.data('natural-width');
            var thumbHeight = thumbImg.data('natural-height');
            /* scale down by whatever factor is required to get both width and height within the bounding box */
            var widthScale = Math.min(WIDTH / thumbWidth, 1);
            var heightScale = Math.min(HEIGHT / thumbHeight, 1);
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
