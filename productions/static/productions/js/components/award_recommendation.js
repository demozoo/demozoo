$(function() {
    $('.award-recommendation').each(function() {
        var container = $(this);
        var header = container.find('.award-recommendation__header');
        var inner = container.find('.award-recommendation__inner');
        if (inner.length) {
            container.addClass('is-closed is-expandable');

            header.click(function() {
                container.hasClass('is-closed') ? container.removeClass('is-closed') : container.addClass('is-closed');
            })
        }
    });
});
