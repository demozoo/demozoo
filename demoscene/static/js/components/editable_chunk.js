function initEditChunkHover(context) {
    $('.edit_chunk', context).hover(function() {
        $(this).closest('.editable_chunk').addClass('hover');
    }, function() {
        $(this).closest('.editable_chunk').removeClass('hover');
    });
}

function initEditToggle(elem) {
    var panel = $(elem);
    var actionsTemplate = $('[data-edit-toggle-actions]', elem);
    actionsTemplate.replaceWith(actionsTemplate.html());
    var editLi = $('[data-edit-toggle-edit]', elem);
    var doneLi = $('[data-edit-toggle-done]', elem);

    function updateEditButtonState() {
        if (panel.hasClass('editing')) {
            panel.removeClass('hide_edit_controls');
            editLi.hide();
            doneLi.show();
            panel.trigger('panelEditEnable')
        } else {
            panel.addClass('hide_edit_controls');
            doneLi.hide();
            editLi.show();
            panel.trigger('panelEditDisable')
        }
    }

    updateEditButtonState();

    editLi.find('button').click(function() {
        panel.addClass('editing');
        updateEditButtonState();
    });
    doneLi.find('button').click(function() {
        panel.removeClass('editing');
        updateEditButtonState();
    });
}

$(function() {
    $('[data-edit-toggle]').each(function() {
        initEditToggle(this);
    });
    initEditChunkHover();
});
