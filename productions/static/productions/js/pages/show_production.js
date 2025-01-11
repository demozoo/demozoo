function initPanelRefresh(context) {
    $('a[data-panel-refresh]', context).click(function() {
        const panelId = this.dataset.panelRefresh;

        ModalWorkflow({
            'url': this.href,
            'responses': {
                'updated': (html) => {replacePanel(panelId, html);}
            },
            'onload': {
                'form': function(modal) {
                    modal.ajaxifyForm($('[data-edit-form]', modal.body));
                    modal.ajaxifyLink($('a[data-delete-link]', modal.body));
                },
                'done': function(modal, jsonData) {
                    modal.respond('updated', jsonData.panel_html);
                    modal.close();
                },
                'confirm': function(modal) {
                    $('[data-confirm-yes]', modal.body).click(function() {
                        var form = $('form.confirmation_form', modal.body);
                        modal.postForm(form.attr('action'), form.serialize() + '&yes=Yes');
                        return false;
                    });
                    $('[data-confirm-no]', modal.body).click(function() {
                        modal.close();
                        return false;
                    });
                }
            }
        });
        return false;
    });
}

function replacePanel(panelId, html) {
    $('#' + panelId).replaceWith(html);
    if (document.querySelector('.secondary_panels > :not(.hidden)')) {
        $('.secondary_panels').removeClass('hidden');
    } else {
        $('.secondary_panels').addClass('hidden');
    }
    var panel = $('#' + panelId);
    applyGlobalBehaviours(panel);
    initPanelRefresh(panel);
    initEditToggle(panel.get(0));
    initEditChunkHover(panel);
}

$(function() {
    $('.tell_us_something_panel').each(function() {
        var heading = $('.tell_us_something_title', this);
        var list = $('.tell_us_something_options', this);

        if (list.length) {
            heading.wrapInner('<a href="javascript:void(0);" class="dropdown"></a>');
            var dropdownLink = heading.find('a');

            list.hide();
            dropdownLink.click(function() {
                if (dropdownLink.hasClass('active')) {
                    list.slideUp('fast');
                    dropdownLink.removeClass('active');
                } else {
                    list.slideDown('fast');
                    dropdownLink.addClass('active');
                }
            });
        }
        list.find('a').click(function() {
            list.slideUp('fast');
            dropdownLink.removeClass('active');
        });
    });
    initPanelRefresh();

    initTagEditing();
});
