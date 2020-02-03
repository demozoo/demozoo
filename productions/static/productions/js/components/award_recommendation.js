$(function() {
    $('.award-recommendation').each(function() {
        var container = $(this);
        var header = container.find('.header');
        var inner = container.find('.inner');
        if (inner.length) {
            container.addClass('closed expandable');

            header.click(function() {
                if (container.hasClass('closed')) {
                    inner.slideDown(function() {container.removeClass('closed');});
                } else {
                    inner.slideUp('fast', function() {container.addClass('closed');});
                }
            })
        }
    });
});
