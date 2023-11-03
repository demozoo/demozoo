function initEditChunkHover(context) {
    $('.edit_chunk', context).hover(function() {
        $(this).closest('.editable_chunk').addClass('hover');
    }, function() {
        $(this).closest('.editable_chunk').removeClass('hover');
    });
}

function initEditToggle(elem) {
    var panel = $(elem);
    var actions = $('<div class="o-actions"></div>');
    var editButton = $('<a href="javascript:void(0);" class="m-button -iconOnly"></a>');

    function updateEditButtonState() {
        if (panel.hasClass('editing')) {
            panel.removeClass('hide_edit_controls');
            editButton.text('Done');
            panel.trigger('panelEditEnable')
        } else {
            panel.addClass('hide_edit_controls');
            editButton.text('Edit');
            panel.trigger('panelEditDisable')
        }
    }

    actions.append(editButton);
    actions.insertAfter(panel.find('h3'));
    updateEditButtonState();

    editButton.click(function() {
        panel.toggleClass('editing');
        updateEditButtonState();
    });
}

$(function() {
    $('.edit_toggle').each(function() {
        initEditToggle(this);
    });
    initEditChunkHover();
});
