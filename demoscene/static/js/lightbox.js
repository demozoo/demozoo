(function() {
    var self = {};

    var isInitialised = false;
    var isShowing = false;
    var lightboxOuter, lightboxElem, lightboxContent;

    function init() {
        if (isInitialised) return;

        var template = $('[data-lightbox-template]');
        $('body').append(template.html());

        lightboxOuter = $('#lightbox_outer');
        lightboxOuter.hide();
        lightboxElem = $('#lightbox');
        lightboxElem.find('[data-lightbox-close]').click(self.close);
        lightboxContent = lightboxElem.find('[data-lightbox-content]');
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
            const spawnedForms = lightboxContent.find('.spawned_form');
            if (spawnedForms.length) {
                /* focus on the first spawned form whose first visible input is empty */
                spawnedForms.each(function() {
                    const firstInput = $(':input:visible', this).first();
                    if (firstInput.length && firstInput.val() === '') {
                        firstInput.focus();
                        return false; // stop the each loop
                    }
                });
            } else {
                /* focus on the first empty input field */
                try {$(':input:visible[value=""]', lightboxContent)[0].focus();}catch(_){}
            }
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
