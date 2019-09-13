function constructMatchingInterface(opts) {
    var selectedLeftButton = null;
    var selectedRightButton = null;

    /* counts how many buttons exist on the page for each left/right value */
    var buttonCountByLeftValue = {};
    var buttonCountByRightValue = {};

    /* extend jquery collections with an 'addLeftButtonBehaviour' function to make buttons selectable */
    $.fn.addLeftButtonBehaviour = function() {
        this.click(function() {
            if (this == selectedLeftButton) {
                /* deselect button if clicked a second time */
                $(this).removeClass('selected');
                selectedLeftButton = null;
            } else {
                if (selectedLeftButton) {
                    /* deselect any left button that's previously been selected */
                    $(selectedLeftButton).removeClass('selected');
                }
                selectedLeftButton = this;
                $(this).addClass('selected');
            }

            if (selectedLeftButton && selectedRightButton) {
                /* one on each side has been selected now, so form a link */
                makeLink(selectedLeftButton, selectedRightButton);
            }
        });
        this.each(function() {
            buttonCountByLeftValue[this.value] = (buttonCountByLeftValue[this.value] || 0) + 1;
            if (opts.initLeftButton) opts.initLeftButton.apply(this);
        });
    };

    /* extend jquery collections with an 'addRightButtonBehaviour' function to make buttons selectable */
    $.fn.addRightButtonBehaviour = function() {
        this.click(function() {
            if (this == selectedRightButton) {
                /* deselect button if clicked a second time */
                $(this).removeClass('selected');
                selectedRightButton = null;
            } else {
                if (selectedRightButton) {
                    /* deselect any right button that's previously been selected */
                    $(selectedRightButton).removeClass('selected');
                }
                selectedRightButton = this;
                $(this).addClass('selected');
            }

            if (selectedLeftButton && selectedRightButton) {
                /* one on each side has been selected now, so form a link */
                makeLink(selectedLeftButton, selectedRightButton);
            }
        });
        this.each(function() {
            buttonCountByRightValue[this.value] = (buttonCountByRightValue[this.value] || 0) + 1;
            if (opts.initRightButton) opts.initRightButton.apply(this);
        });
    };

    $.fn.addUnlinkButtonBehaviour = function() {
        this.click(function() {
            var li = $(this).closest('li');
            var leftButton = li.find(opts.leftSelector).get(0);
            var rightButton = li.find(opts.rightSelector).get(0);

            opts.unlinkAction(leftButton.value, rightButton.value);

            li.fadeOut('fast');
            /* if buttons were selected at the time of deletion, clear the selection */
            if (leftButton == selectedLeftButton) {
                selectedLeftButton = null;
            }
            if (rightButton == selectedRightButton) {
                selectedRightButton = null;
            }
            buttonCountByLeftValue[leftButton.value] -= 1;
            buttonCountByRightValue[rightButton.value] -= 1;

            /* add buttons back to the 'unmatched' sections if we've just removed the last one
                for that item */
            if (buttonCountByLeftValue[leftButton.value] === 0) {
                var newLeftButton = $(leftButton).clone().removeClass('selected matched').addClass('unmatched');
                $(opts.leftListSelector).append(
                    $('<li></li>').append(newLeftButton)
                );
                newLeftButton.addLeftButtonBehaviour();
            }
            if (buttonCountByRightValue[rightButton.value] === 0) {
                var newRightButton = $(rightButton).clone().removeClass('selected matched').addClass('unmatched');
                $(opts.rightListSelector).append(
                    $('<li></li>').append(newRightButton)
                );
                newRightButton.addRightButtonBehaviour();
            }
        });
    };

    /* apply these behaviours to the initial set of buttons */
    $(opts.leftSelector).addLeftButtonBehaviour();
    $(opts.rightSelector).addRightButtonBehaviour();
    $('button.unlink').addUnlinkButtonBehaviour();

    function removeLeftButton(leftButton) {
        $(leftButton).closest('li').fadeOut('fast');
        buttonCountByLeftValue[leftButton.value] -= 1;
    }
    function removeRightButton(rightButton) {
        $(rightButton).closest('li').fadeOut('fast');
        buttonCountByRightValue[rightButton.value] -= 1;
    }
    function addMatchElement(matchElement) {
        $('ul.matches').append(matchElement);
        $(opts.leftSelector, matchElement).addLeftButtonBehaviour();
        $(opts.rightSelector, matchElement).addRightButtonBehaviour();
        $('button.unlink', matchElement).addUnlinkButtonBehaviour();
    }

    function makeLink(leftButton, rightButton) {
        /* discard attempts to match two buttons that are already linked */
        var alreadyMatched = $(leftButton).closest('li').get(0) == $(rightButton).closest('li').get(0);

        var leftVal = leftButton.value;
        var rightVal = rightButton.value;
        if (!alreadyMatched) {
            opts.linkAction(leftVal, rightVal);
        }

        /* clear selection state so that the next button click won't be considered a link to one of these */
        selectedLeftButton = null;
        selectedRightButton = null;

        /* remove the buttons from the list, unless they're
            already in the 'matched' list in which they should remain (because that means the
            item is now linked to multiple partners) */
        if ($(leftButton).hasClass('unmatched')) {
            removeLeftButton(leftButton);
        } else {
            $(leftButton).removeClass('selected');
        }
        if ($(rightButton).hasClass('unmatched')) {
            removeRightButton(rightButton);
        } else {
            $(rightButton).removeClass('selected');
        }

        if (!alreadyMatched) {
            /* create new buttons for the 'matched' section. Should duplicate the original buttons,
                but not be selected and be labelled 'matched' */
            var newLeftButton = $(leftButton).clone().removeClass('selected unmatched').addClass('matched');
            var newRightButton = $(rightButton).clone().removeClass('selected unmatched').addClass('matched');
            var newUnlinkButton = $('<button class="unlink" title="Delete this match">unlink</button>');

            var matchElement = $('<li></li>').append(newLeftButton, ' = ', newRightButton, ' ', newUnlinkButton);
            addMatchElement(matchElement);
        }
    }

    return {
        'removeLeftButton': removeLeftButton,
        'removeRightButton': removeRightButton,
        'addMatchElement': addMatchElement
    }
}
