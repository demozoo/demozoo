function initTagEditing() {
    var editTagsUrl = $('form.tags_form').attr('action');
    if (editTagsUrl) {
        var addTagUrl = editTagsUrl.replace(/\/edit_tags\/$/, '/add_tag/');
        var removeTagUrl = editTagsUrl.replace(/\/edit_tags\/$/, '/remove_tag/');

        var tagField = $('#id_tags');
        tagField.tagit({
            'afterTagAdded': function(event, data) {
                if (data.duringInitialization) return;
                $.post(addTagUrl, {
                    'csrfmiddlewaretoken': $.cookie('csrftoken'),
                    'tag_name': data.tagLabel
                }, function(response) {
                    $('ul.tags').html(response['tags_list_html']);
                    if (response['clean_tag_name'] != data.tagLabel) {
                        tagField.tagit('removeTagByLabel', data.tagLabel, false, true);
                        if (response['clean_tag_name'] !== '') {
                            tagField.tagit('createTag', response['clean_tag_name'], null, true);
                        }
                    }
                    if (response['message']) {
                        $('#tags_message').addClass('error').text(
                            response['message']
                        ).stop().css(
                            {'backgroundColor': '#fbb'}
                        ).animate(
                            {'backgroundColor': 'white'}, 5000
                        );
                    }
                }, 'json');
            },
            'afterTagRemoved': function(event, data) {
                $.post(removeTagUrl, {
                    'csrfmiddlewaretoken': $.cookie('csrftoken'),
                    'tag_name': data.tagLabel
                }, function(response) {
                    $('ul.tags').html(response);
                });
            },
            'autocomplete': {
                'source': '/productions/autocomplete_tags/'
            }
        });
    }

    $('form.tags_form input:submit').remove();
    $('.tags_panel').on('panelEditEnable', function() {
        $('form.tags_form li.tagit-new input').focus();
    });
    $('.tags_panel a.tag_name').each(function() {
        var tag = this;
        var description = $(tag).data('description');
        if (description) {
            var hideDescriptionTimeout;

            tagOffset = $(tag).offset();
            var descriptionElem = $('<div class="tag_description"></div>').html(description).css({
                'position': 'absolute',
                'top': (tagOffset.top + 32) + 'px',
                'left': (tagOffset.left - 300) + 'px'
            }).hide();
            $('body').append(descriptionElem);
            $(tag).hover(function() {
                $('.tag_description').hide(); /* hide all other tag descriptions */
                descriptionElem.show();
                clearTimeout(hideDescriptionTimeout);
            }, function() {
                hideDescriptionTimeout = setTimeout(function() {
                    descriptionElem.hide();
                }, 750);
            });
            descriptionElem.hover(function() {
                clearTimeout(hideDescriptionTimeout);
            }, function() {
                hideDescriptionTimeout = setTimeout(function() {
                    descriptionElem.hide();
                }, 750);
            });
        }
    });
}
