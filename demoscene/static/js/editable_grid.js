function Event() {
    var self = {};
    var listeners = [];
    
    self.bind = function(callback) {
        listeners.push(callback);
    }
    self.unbind = function(callback) {
        for (var i = listeners.length - 1; i >= 0; i--) {
            if (listeners[i] == callback) listeners.splice(i, 1);
        }
    }
    self.trigger = function() {
        var args = arguments;
        /* event is considered 'cancelled' if any handler returned a value of false
            (specifically false, not just a falsy value). Exactly what this means is
            up to the caller - we just return false */
        var cancelled = false;
        for (var i = 0; i < listeners.length; i++) {
            cancelled = cancelled || (listeners[i].apply(null, args) === false);
        };
        return !cancelled;
    }
    
    return self;
}

function Property(initialValue) {
    var self = {};
    
    self._value = initialValue;
    
    self.change = Event();
    self.get = function() {
        return self._value;
    }
    self.set = function(newValue) {
        if (newValue === self._value) return;
        self._value = newValue;
        self.change.trigger(self._value);
    }
    
    return self;
}

function EditableGrid(elem) {
    var self = {};
    
    var $elem = $(elem);
    var gridElem = $elem.get(0);
    $elem.addClass('editable_grid');
    
    var cursorX = 0, cursorY = 0;
    var rows = [];
    var isFocused = false;
    
    function elementIsInGrid(childElem) {
        return $.contains(gridElem, childElem);
    }
    
    /* return the index of the GridRow object whose DOM element is, or contains, childElem,
        or null if childElement is not contained in a row of this grid
    */
    function rowIndexForElement(childElem) {
        /* walk up childElem's parent elements until we find an immediate child of
            the grid element */
        var elemToTest = childElem;
        while (elemToTest.parentNode && elemToTest.parentNode != gridElem) {
            elemToTest = elemToTest.parentNode;
        }
        if (elemToTest.parentNode) {
            /* check each row in turn to see if its element is the one we've found */
            for (var i = 0; i < rows.length; i++) {
                if (rows[i].elem == elemToTest) return i;
            }
        }
    }
    /* return the coordinates of the grid cell whose DOM element is, or contains, childElem,
        or null if childElem is not contained in a cell of this grid
    */
    function coordsForElement(childElem) {
        var y = rowIndexForElement(childElem);
        if (y != null) {
            var x = rows[y].cellIndexForElement(childElem);
            if (x != null) return [x,y];
        }
    }
    
    /* move cursor to next cell; return true if successful, false if there's no next cell */
    function moveCursorForward() {
        if (cursorX + 1 < rows[cursorY].getCellCount()) {
            self.setCursor(cursorX + 1, cursorY);
            return true;
        } else {
            /* scan forwards to next row with cells */
            for (var newY = cursorY + 1; newY < rows.length; newY++) {
                var cellCount = rows[newY].getCellCount();
                if (cellCount) {
                    self.setCursor(0, newY);
                    return true;
                }
            }
        }
        return false;
    }
    /* move cursor to previous cell; return true if successful, false if there's no previous cell */
    function moveCursorBackward() {
        if (cursorX > 0) {
            self.setCursor(cursorX - 1, cursorY);
            return true;
        } else {
            /* scan backwards to previous row with cells */
            for (var newY = cursorY - 1; newY >= 0; newY--) {
                var cellCount = rows[newY].getCellCount();
                if (cellCount) {
                    self.setCursor(cellCount - 1, newY);
                    return true;
                }
            }
        }
        return false;
    }
    
    /* try to move cursor forward to next cell; if there isn't one, create a new row */
    function advanceOrCreate() {
        if (!moveCursorForward()) {
            var row = self.addRow(null, false);
            self.onAddRow.trigger(row);
        }
    }
    self.advanceOrCreate = advanceOrCreate;
    
    function keydown(event) {
        /* current cell, if any, gets first dibs on handling events */
        var cell = getCell(cursorX, cursorY);
        if (cell) {
            var result = cell.keydown(event);
            /* cell's keydown handler can return:
                - null to let grid handle the event
                - false to terminate event handling immediately
                - true to pass control to the browser's default handlers */
            if (result != null) return result;
        }
        
        switch (event.which) {
            case 9: /* tab */
                if (event.shiftKey) {
                    if (moveCursorBackward()) {
                        return false;
                    } else {
                        /* no previous cell; allow tab to escape the grid */
                        blur();
                        return;
                    }
                } else {
                    if (moveCursorForward()) {
                        return false;
                    } else {
                        /* no next cell; allow tab to escape the grid */
                        blur();
                        return;
                    }
                }
            case 13: /* enter */
                advanceOrCreate();
                return false;
            case 37: /* cursor left */
                setCursorIfInRange(cursorX - 1, cursorY);
                //resultsTable.focus();
                return false;
            case 38: /* cursor up */
                setCursorIfInRange(cursorX, cursorY - 1);
                //resultsTable.focus();
                return false;
            case 39: /* cursor right */
                setCursorIfInRange(cursorX + 1, cursorY);
                //resultsTable.focus();
                return false;
            case 40: /* cursor down */
                setCursorIfInRange(cursorX, cursorY + 1);
                //resultsTable.focus();
                return false;
        }
    }
    
    function keypress(event) {
        /* pass event to current cell */
        var cell = getCell(cursorX, cursorY);
        if (cell) return cell.keypress(event);
    }
    
    if ($elem.attr('tabindex') == null) {
        $elem.attr('tabindex', 0);
    }
    self.focus = function() {
        $elem.focus();
    }
    $elem.focus(function() {
        if (!isFocused) {
            isFocused = true;
            $(this).addClass('focused');
            $(document).bind('keydown', keydown);
            $(document).bind('keypress', keypress);
            
            /* It isn't guaranteed that the cell at cursor position has
                been given the 'cursor' class (e.g. upon initial load,
                when cell (0,0) is created *after* the cursor is already
                set to 0,0) so do that now */
            var cell = getCell(cursorX, cursorY);
            if (cell) cell.receiveCursor();
        }
    })
    function blur() {
        var cell = getCell(cursorX, cursorY);
        if (cell) cell.blur();
        
        isFocused = false;
        $elem.removeClass('focused');
        /* TODO: also propagate blur event to the current GridRow */
        $(document).unbind('keydown', keydown);
        $(document).unbind('keypress', keypress);
    }
    
    function setCursorIfInRange(x, y) {
        var row = rows[y];
        if (!row || !row.getCell(x)) return;
        self.setCursor(x,y);
    }
    
    /* set cursor to position x,y */
    self.setCursor = function(x, y) {
        var oldCell = getCell(cursorX, cursorY);
        if (oldCell) oldCell.loseCursor();
        
        cursorX = x; cursorY = y;
        getCell(cursorX, cursorY).receiveCursor();
        /* TODO: possibly scroll page if cursor not in view */
    }
    
    $(document).mousedown(function(event) {
        if (elementIsInGrid(event.target)) {
            var coords = coordsForElement(event.target);
            if (coords && coords[0] == cursorX && coords[1] == cursorY && isFocused) {
                /* cursor is already here and grid is active; do nothing, so that
                    widgets within the cell can respond sensibly */
                return;
            }
            $elem.focus();
            if (coords) {
                /* mousedown is on a data cell; move to it */
                self.setCursor(coords[0], coords[1]);
            }
        } else { /* mousedown outside of grid */
            blur();
        }
    });
    
    var headerRowUl = $('<ul class="fields"></ul>')
    var headerRow = $('<li class="header_row"></li>').append(headerRowUl, '<div style="clear: both;"></div>');
    $elem.prepend(headerRow);
    
    self.onAddRow = Event() /* Fired when adding a row via the insert / add buttons.
        NOT fired when calling addRow from code */
    
    var insertButton = $('<input type="button" class="add" value="Add row" />');
    var insertButtonDiv = $('<div class="editable_grid_insert"></div>');
    insertButtonDiv.append(insertButton);
    $elem.after(insertButtonDiv);
    insertButton.click(function() {
        /* set timeout so that button acquires focus before we revert focus to the table */
        setTimeout(function() {
            var row = self.addRow(null, true);
            self.onAddRow.trigger(row);
        }, 10);
    })
    
    self.addHeader = function(title, className) {
        var li = $('<li></li>').attr('class', className).append(
            $('<div class="show"></div>').text(title)
        );
        headerRowUl.append(li);
    }
    
    self.addRow = function(index, animate) {
        if (index == null || index >= rows.length) {
            index = rows.length;
            var row = GridRow(index, self);
            $elem.append(row.elem);
            rows.push(row);
        } else {
            /* bump up all row indexes below this one */
            for (var i = index; i < rows.length; i++) {
                rows[i].index.set(i+1);
            }
            /* also bump up cursor position */
            if (cursorY >= index) cursorY++;
            
            var row = GridRow(index, self);
            $(row.elem).insertBefore(rows[index].elem);
            rows.splice(index, 0, row);
        }
        
        row.prependInsertLink(function() {
            var newRow = self.addRow(row.index.get(), true);
            self.onAddRow.trigger(newRow);
        })
        
        row.onDelete.bind(function() {
            var index = row.index.get();
            for (var i = index + 1; i < rows.length; i++) {
                rows[i].index.set(i-1);
            }
            rows.splice(index, 1);
            
            if (cursorY > index) {
                cursorY--;
            } else if (cursorY == index) {
                if (rows.length == 0) {
                    /* cursorY remains at 0,0 even if there's no cell to highlight there */
                } else if (cursorY == rows.length) {
                    self.setCursor(cursorX, cursorY - 1);
                } else {
                    self.setCursor(cursorX, cursorY);
                }
            }
        })
        
        if (animate) {
            row.slideDown();
        }
        
        return row;
    }
    
    getRow = function(index) {
        return rows[index];
    }
    getCell = function(x,y) {
        var row = getRow(y);
        if (row) return row.getCell(x);
    }
    
    self.onReorder = Event();
    $elem.sortable({
        'axis': 'y',
        'distance': 1,
        'items': 'li.data_row',
        'cancel': ':input,option,.byline_match_container', /* TODO: make into a config option to pass to EditableGrid */
        'update': function(event, ui) {
            var rowElem = ui.item[0];
            var row, oldIndex;
            for (var i = 0; i < rows.length; i++) {
                if (rows[i].elem == rowElem) {
                    oldIndex = i;
                    row = rows[i];
                    break;
                }
            }
            var newIndex = $elem.find('> li.data_row').index(rowElem);
            
            rows.splice(oldIndex, 1);
            rows.splice(newIndex, 0, row);
            if (oldIndex < newIndex) {
                /* moving down */
                for (var i = oldIndex; i < newIndex; i++) {
                    rows[i].index.set(i);
                }
                rows[newIndex].index.set(newIndex);
                
                if (cursorY == oldIndex) {
                    cursorY = newIndex;
                } else if (cursorY > oldIndex && cursorY <= newIndex) {
                    cursorY--;
                }
                
            } else {
                /* moving up */
                for (var i = newIndex+1; i <= oldIndex; i++) {
                    rows[i].index.set(i);
                }
                rows[newIndex].index.set(newIndex);
                
                if (cursorY == oldIndex) {
                    cursorY = newIndex;
                } else if (cursorY >= newIndex && cursorY < oldIndex) {
                    cursorY++;
                }
            }
            
            self.onReorder.trigger(row, oldIndex, newIndex);
            row.onReorder.trigger(oldIndex, newIndex);
        }
    });
    
    return self;
}

function GridRow(index, grid) {
    var self = {};
    
    self.grid = grid;
    self.index = Property(index);
    self.onReorder = Event();
    
    var cells = [];
    
    var $elem = $('<li class="data_row"></li>');
    self.elem = $elem.get(0);
    var fieldsUl = $('<ul class="fields"></ul>');
    var fieldsUlElem = fieldsUl.get(0);
    var deleteLink = $('<a href="javascript:void(0)" tabindex="-1" class="delete" title="Delete this row">Delete</a>');
    var statusIcon = $('<div class="status"></div>');
    $elem.append(fieldsUl, deleteLink, statusIcon, '<div style="clear: both;"></div>');
    
    self.addCell = function(cell) {
        cells.push(cell);
        cell.row = self;
        cell.grid = self.grid;
        cell.constructElem();
        fieldsUl.append(cell.elem);
    }
    self.getCell = function(index) {
        return cells[index];
    }
    self.getCellCount = function() {
        return cells.length;
    }
    
    self.setStatus = function(status, titleText) {
        statusIcon.attr({'class': 'status status_' + status})
        if (titleText) {
            statusIcon.attr({'title': titleText});
        } else {
            statusIcon.removeAttr('title');
        }
    }
    
    /* return the index of the GridCell object whose DOM element is, or contains, childElem,
        or null if childElement is not contained in a cell of this row
    */
    self.cellIndexForElement = function(childElem) {
        /* walk up childElem's parent elements until we find an immediate child of
            the fieldsUlElem element */
        var elemToTest = childElem;
        while (elemToTest.parentNode && elemToTest.parentNode != fieldsUlElem) {
            elemToTest = elemToTest.parentNode;
        }
        if (elemToTest.parentNode) {
            /* check each cell in turn to see if its element is the one we've found */
            for (var i = 0; i < cells.length; i++) {
                if (cells[i].elem == elemToTest) return i;
            }
        }
    }
    
    self.slideDown = function() {
        $elem.css({'height': '0'}).animate({'height': '20px'}, {
            'duration': 'fast',
            'complete': function() {
                $elem.css({'height': 'auto'});
                //appendDeleteLink(row);
            }
        });
    }
    
    self.prependInsertLink = function(clickAction) {
        var insertLink = $('<a class="insert" tabindex="-1" title="Insert row here" href="javascript:void(0)">insert &rarr;</a>');
        $elem.prepend(insertLink);
        insertLink.click(clickAction);
    }
    
    self.onDelete = Event();
    deleteLink.click(function() {
        self.onDelete.trigger();
        /* TODO: what happens if we're in edit mode? */
        $elem.fadeOut('fast', function() {
            $elem.remove();
        })
    })
    
    return self;
}

function GridCell(opts) {
    if (!opts) opts = {};
    var self = {};
    
    self.value = Property(opts.value);
    
    var $elem, editElem;
    
    /* edit modes:
        null = not editing
        'capturedText' = do not select on focus; cursor keys move caret
        'uncapturedText' = select on focus; cursor keys move cell
    */
    self._editMode = null;

    self.isEditing = function() {
        return (self._editMode !== null);
    }

    self.constructElem = function() {
        $elem = $('<li></li>');
        self.elem = $elem.get(0);
        if (opts['class']) $elem.addClass(opts['class']);
        
        self._showElem = $('<div class="show"></div>');
        $elem.append(self._showElem);
        self._initShowElem(self._showElem);
        self._refreshShowElem(self._showElem, opts.value);
        
        editElem = $('<div class="edit"></div>');
        $elem.append(editElem);
        self._initEditElem(editElem);
        self._refreshEditElem(editElem, opts.value);
        editElem.hide();
        
        self.value.change.bind(function(newValue) {
            self._refreshShowElem(self._showElem, newValue);
            self._refreshEditElem(editElem, newValue);
        })
        
        $elem.dblclick(function() {
            if (!self._editMode) self._startEdit('capturedText');
        })
        
    }
    
    self._initShowElem = function(showElem) {
    }
    self._initEditElem = function(editElem) {
    }
    self._refreshShowElem = function(showElem, value) {
        if (value == null) {
            showElem.text('');
        } else {
            showElem.text(value);
        }
    }
    self._refreshEditElem = function(editElem, value) {
    }
    self._valueFromEditElem = function(editElem) {
        return null;
    }
    self._prepareEditElem = function(editElem) {
    }
    self._unprepareEditElem = function(editElem) {
    }
    
    self.receiveCursor = function() {
        $elem.addClass('cursor');
    }
    self.blur = function() {
        if (self._editMode) self._finishEdit();
    }
    self.loseCursor = function() {
        $elem.removeClass('cursor');
        self.blur();
    }
    
    self.onStartEdit = Event();
    self.onFinishEdit = Event();
    self.onCancelEdit = Event();
    
    self._finishEdit = function() {
        self.value.set(self._valueFromEditElem(editElem));
        self._unprepareEditElem(editElem);
        editElem.hide();
        self._showElem.show();
        self._editMode = null;
        self.onFinishEdit.trigger();
    }
    var originalValue;
    self._cancelEdit = function() {
        self._refreshEditElem(editElem, originalValue);
        self._unprepareEditElem(editElem);
        editElem.hide();
        self._showElem.show();
        self._editMode = null;
        self.onCancelEdit.trigger();
    }
    self._startEdit = function(newMode) {
        if (self._isLocked) return;
        originalValue = self.value.get();
        self._showElem.hide();
        editElem.show();
        self._editMode = newMode;
        self._prepareEditElem(editElem);
        self.onStartEdit.trigger();
    }
    
    self.keydown = function(event) {
    }
    self.keypress = function(event) {
    }
    var isMac = /Mac OS/.test(navigator.userAgent);
    self.eventIsCommandKey = function(event) {
        /* helper function for subclasses to test whether a keyboard event has the OS's native
        'command' key pressed (command on Mac, ctrl on other platforms). We used to be able to
        use event.metaKey, but jquery 1.7 broke that: http://bugs.jquery.com/ticket/3368 */
        return (isMac ? event.metaKey : event.ctrlKey);
    }
    
    self._isLocked = false;
    self.lock = function(text) {
        if (text != null) self._showElem.text(text);
        $elem.addClass('locked');
        self._isLocked = true;
    }
    self.unlock = function() {
        $elem.removeClass('locked');
        self.value.set(null);
        self._refreshShowElem(self._showElem, null);
        self._refreshEditElem(editElem, null);
        self._isLocked = false;
    }
    
    return self;
}

function TextGridCell(opts) {
    var self = GridCell(opts);
    
    var input;
    self._initEditElem = function(editElem) {
        input = $('<input type="text" />');
        self._input = input;
        editElem.append(input);
    }
    self._refreshEditElem = function(editElem, value) {
        input.val(value);
    }
    self._valueFromEditElem = function(editElem) {
        return input.val();
    }
    self._prepareEditElem = function(editElem) {
        input.focus();
        if (self._editMode == 'uncapturedText' && input.select) input.select();
    }
    self.keydown = function(event) {
        switch (self._editMode) {
            case null:
                switch (event.which) {
                    case 13:
                        self._startEdit('capturedText');
                        return false;
                    case 8: /* backspace */
                        self._startEdit('uncapturedText');
                        input.val('');
                        return false;
                    case 86: /* V */
                        if (self.eventIsCommandKey(event)) { /* cmd+V = paste */
                            self._startEdit('uncapturedText');
                            return true; /* override grid event handler, defer to browser's own */
                        }
                        break;
                }
                break;
            case 'capturedText':
                switch(event.which) {
                    case 13: /* enter */
                        self._finishEdit();
                        return false;
                    case 27: /* escape */
                        self._cancelEdit();
                        return false;
                    case 37: /* cursors */
                    case 38:
                    case 39:
                    case 40:
                        return true; /* override grid event handler, defer to browser's own */
                }
                break;
            case 'uncapturedText':
                switch(event.which) {
                    case 13: /* enter */
                        self._finishEdit();
                        return null; /* grid's event handler for the enter key will advance to next cell */
                    case 27: /* escape */
                        self._cancelEdit();
                        return false;
                    case 37: /* cursors */
                    case 38:
                    case 39:
                    case 40:
                        self._finishEdit();
                        return null; /* let grid event handler process the cursor movement */
                }
                break;
        }
    }
    self.keypress = function(event) {
        switch (self._editMode) {
            case null:
                self._startEdit('uncapturedText');
                break;
        }
    }
    
    return self;
}

function SelectGridCell(opts) {
    var self = GridCell(opts);
    
    var optionLabelsById = {};
    for (var i = 0; i < opts.options.length; i++) {
        var option = opts.options[i];
        optionLabelsById[option[0]] = option[1];
    }
    
    var input;
    self._initEditElem = function(editElem) {
        input = $('<select><option value="">--------</option></select>');
        for (var i = 0; i < opts.options.length; i++) {
            var option = opts.options[i];
            optionElem = $('<option></option>').attr({'value': option[0]}).text(option[1]);
            input.append(optionElem);
        }
        editElem.append(input);
    }
    self._refreshShowElem = function(showElem, value) {
        var label = optionLabelsById[value];
        if (label == null) label = '';
        showElem.text(label);
    }
    self._refreshEditElem = function(editElem, value) {
        input.val(value);
    }
    self._valueFromEditElem = function(editElem) {
        return input.val();
    }
    self._prepareEditElem = function(editElem) {
        input.focus();
    }
    
    self.keydown = function(event) {
        switch (self._editMode) {
            case null:
                if ( (event.which >= 48 && event.which <= 57) || (event.which >= 65 && event.which <= 90) ) {
                    // respond to alphanumeric keys and enter by focusing the dropdown
                    // (all prod types and platforms start with alphanumerics)
                    self._startEdit('uncapturedText');
                    return true; /* allow select box to handle the keypress */
                } else {
                    switch (event.which) {
                        case 13:
                            self._startEdit('capturedText');
                            return false;
                        case 8: /* backspace */
                            self._startEdit('uncapturedText');
                            input.val('');
                            return false;
                    }
                }
                break;
            case 'capturedText':
                switch(event.which) {
                    case 13: /* enter */
                        self._finishEdit();
                        input.blur();
                        return false;
                    case 27: /* escape */
                        self._cancelEdit();
                        return false;
                    case 37: /* cursors */
                    case 38:
                    case 39:
                    case 40:
                        return true; /* override grid event handler, defer to browser's own */
                }
                break;
            case 'uncapturedText':
                switch(event.which) {
                    case 13: /* enter */
                        self._finishEdit();
                        input.blur();
                        return null; /* grid's event handler for the enter key will advance to next cell */
                    case 27: /* escape */
                        self._cancelEdit();
                        input.blur();
                        return false;
                    case 38: /* cursors */
                    case 40:
                    case 37:
                    case 39:
                        self._finishEdit();
                        input.blur();
                        return null; /* let grid event handler process the cursor movement */
                }
                break;
        }
    }
    
    return self;
}
