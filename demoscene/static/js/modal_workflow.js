/* A framework for modal popups that are loaded via AJAX, allowing navigation to other
subpages to happen within the lightbox, and returning a response to the calling page,
possibly after several navigation steps
*/

function ModalWorkflow(opts) {
    /* options passed in 'opts':
        'url' (required): initial
        'onload' (optional): dict of callbacks to be called on loading a subpage, keyed by step name
        'responses' (optional): dict of callbacks to be called when the modal content
            calls modal.respond(callbackName, params)
    */

    var self = {};
    var responseCallbacks = opts.responses || {};
    var onLoadCallbacks = opts.onload || {};

    self.loadUrl = function(url, urlParams) {
        $.get(url, urlParams, self.loadResponseText, 'text');
    };

    self.postForm = function(url, formData) {
        $.post(url, formData, self.loadResponseText, 'text');
    };

    self.ajaxifyForm = function(formSelector) {
        $(formSelector).each(function() {
            var action = this.action;
            if (this.method.toLowerCase() == 'get') {
                $(this).submit(function() {
                    self.loadUrl(action, $(this).serialize());
                    return false;
                });
            } else {
                $(this).submit(function() {
                    self.postForm(action, $(this).serialize());
                    return false;
                });
            }
        });
    };
    self.ajaxifyLink = function(linkSelector) {
        $(linkSelector).click(function() {
            self.loadUrl(this.href);
            return false;
        });
    };

    self.loadResponseText = function(responseText) {
        var response = JSON.parse(responseText);
        self.loadBody(response);
    };

    self.loadBody = function(body) {
        var onload;
        if (body.step) {
            onload = onLoadCallbacks[body.step];
        } else {
            onload = body.onload;
        }
        if (onload && body.html) {
            Lightbox.openContent(body.html, function(elem) {
                self.body = elem;
                onload(self, body);
            });
        } else if (body.html) {
            Lightbox.openContent(body.html);
        } else if (onload) {
            onload(self, body);
        }
    };

    self.respond = function(responseType) {
        if (responseType in responseCallbacks) {
            args = Array.prototype.slice.call(arguments, 1);
            responseCallbacks[responseType].apply(self, args);
        }
    };

    self.close = function() {
        Lightbox.close();
    };

    self.loadUrl(opts.url, opts.urlParams);

    return self;
}
