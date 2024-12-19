$(function() {
    var reportName = $('.report').attr('data-report-name');
    $('.excludable').each(function() {
        var recordId = $(this).attr('data-record-id');
        var elem = this;
        
        var deleteButton = $('<a href="javascript:void(0)" class="exclude_button"><img src="/static/images/icons/delete.png" width="16" height="16" alt="Exclude record" title="Exclude record"></a>');
        if ($(this).is('tr')) {
            $(this).find('td:first').prepend(deleteButton);
        } else {
            $(this).prepend(deleteButton);
        }
        deleteButton.click(function() {
            $.post('/maintenance/exclude/', {
                'report_name': reportName,
                'record_id': recordId,
                'csrfmiddlewaretoken': $.cookie('csrftoken')
            }, function() {
                $(elem).fadeOut();
            })
        })
    })
})
