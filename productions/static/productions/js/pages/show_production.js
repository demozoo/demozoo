function initEditCreditLink(context) {
    $('a.edit_credit, a.add_credit', context).click(function() {
        ModalWorkflow({
            'url': this.href,
            'responses': {
                'creditsUpdated': replaceCreditsPanel
            },
            'onload': {
                'form': function(modal) {
                    modal.ajaxifyForm($('[data-edit-form]', modal.body));
                    modal.ajaxifyLink($('a.delete_credit', modal.body));
                },
                'done': function(modal, jsonData) {
                    modal.respond('creditsUpdated', jsonData.panel_html);
                    modal.close();
                },
                'confirm': function(modal) {
                    $('.yes_button', modal.body).click(function() {
                        var form = $('form.confirmation_form', modal.body);
                        modal.postForm(form.attr('action'), form.serialize() + '&yes=Yes');
                        return false;
                    });
                    $('.no_button', modal.body).click(function() {
                        modal.close();
                        return false;
                    });
                }
            }
        });
        return false;
    });
}

function replaceCreditsPanel(creditsHtml) {
    $('.secondary_panels').removeClass('hidden');
    $('#credits_panel').replaceWith(creditsHtml);
    var panel = $('#credits_panel');
    applyGlobalBehaviours(panel);
    initEditCreditLink(panel);
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
    initEditCreditLink();

    initTagEditing();
});
