function(modal) {
    $('.choose-image', modal.body).click(function() {
        var elem = $(this);
        modal.respond('imageChosen', {
            'id': elem.data('id'),
            'url': elem.data('url')
        });
        modal.close();
    });
}