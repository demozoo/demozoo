function initEditChunkHover(context) {
    $('.edit_chunk', context).hover(function() {
        $(this).closest('.editable_chunk').addClass('hover');
    }, function() {
        $(this).closest('.editable_chunk').removeClass('hover');
    });
}

function initEditToggle(context) {
    $('.edit_toggle', context).each(function() {
        var panel = $(this);

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
        updateEditButtonState();

        actions.append(editButton);
        actions.insertAfter(panel.find('h3'));

        editButton.click(function() {
            panel.toggleClass('editing');
            updateEditButtonState();
        });
    });
}

$(function() {
    initEditToggle();
    initEditChunkHover();
});
