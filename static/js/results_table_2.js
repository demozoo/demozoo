function Event() {
	var self = {};
	var listeners = [];
	
	self.bind = function(callback) {
		listeners.push(callback);
	}
	self.unbind = function(callback) {
		listeners = _.without(listeners, callback);
	}
	self.trigger = function() {
		var args = arguments;
		_.each(listeners, function(callback) {
			callback.apply(null, args);
		});
	}
	
	return self;
}

function EditableGrid(elem) {
	var self = {};
	
	var $elem = $(elem);
	var gridElem = $elem.get(0);
	$elem.addClass('editable_grid');
	
	/* edit modes:
		null = not editing
		'capturedText' = do not select on focus; cursor keys move caret
		'uncapturedText' = select on focus; cursor keys move cell
	*/
	var editMode = null;
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
		while (elemToTest.parentElement && elemToTest.parentElement != gridElem) {
			elemToTest = elemToTest.parentElement;
		}
		if (elemToTest.parentElement) {
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
	
	function keydown(event) {
		switch(editMode) {
			case null:
				switch (event.which) {
					case 9: /* tab */
						if (event.shiftKey) {
							if (cursorX > 0) {
								setCursor(cursorX - 1, cursorY);
								return false;
							} else {
								/* scan backwards to previous row with cells */
								for (var newY = cursorY - 1; newY >= 0; newY--) {
									var cellCount = rows[newY].getCellCount();
									if (cellCount) {
										setCursor(cellCount - 1, newY);
										return false;
									}
								}
								/* no previous cell; allow tab to escape the grid */
								blur();
								return;
							}
						} else {
							if (cursorX + 1 < rows[cursorY].getCellCount()) {
								setCursor(cursorX + 1, cursorY);
								return false;
							} else {
								/* scan forwards to next row with cells */
								for (var newY = cursorY + 1; newY < rows.length; newY++) {
									var cellCount = rows[newY].getCellCount();
									if (cellCount) {
										setCursor(0, newY);
										return false;
									}
								}
								/* no next cell; allow tab to escape the grid */
								blur();
								return;
							}
						}
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
	}
	function keypress(event) {
	}
	
	if ($elem.attr('tabindex') == null) {
		$elem.attr('tabindex', 0);
	}
	$elem.focus(function() {
		if (!isFocused) {
			isFocused = true;
			$(this).addClass('focused');
			$(document).bind('keydown', keydown);
			$(document).bind('keypress', keypress);
			
			var cell = getCell(cursorX, cursorY);
			if (cell) cell.receiveCursor();
		}
	})
	function blur() {
		isFocused = false;
		$elem.removeClass('focused');
		/* TODO: also propagate blur event to the current GridRow */
		$(document).unbind('keydown', keydown);
		$(document).unbind('keypress', keypress);
	}
	
	function setCursorIfInRange(x, y) {
		var row = rows[y];
		if (!row || !row.getCell(x)) return;
		setCursor(x,y);
	}
	
	/* set cursor to position x,y */
	function setCursor(x, y) {
		var oldCell = getCell(cursorX, cursorY);
		if (oldCell) oldCell.loseCursor();
		
		cursorX = x; cursorY = y;
		getCell(cursorX, cursorY).receiveCursor();
		/* TODO: possibly scroll page if cursor not in view */
	}
	
	$(document).mousedown(function(event) {
		var coords = coordsForElement(event.target);
		if (coords) {
			if (coords[0] == cursorX && coords[1] == cursorY) {
				return; /* continue editing if cursor is already here */
			}
			$elem.focus();
			//if (editMode) finishEdit();
			setCursor(coords[0], coords[1]);
		} else if (editMode) {
			//finishEdit();
		}
	}).click(function(event) {
		if (elementIsInGrid(event.target)) {
			$elem.focus();
		} else {
			blur();
		}
	});
	
	var headerRowUl = $('<ul class="fields"></ul>')
	var headerRow = $('<li class="header_row"></li>').append(headerRowUl, '<div style="clear: both;"></div>');
	$elem.prepend(headerRow);
	
	var insertButton = $('<input type="button" class="add" value="Add row" />');
	var insertButtonDiv = $('<div class="editable_grid_insert"></div>');
	insertButtonDiv.append(insertButton);
	$elem.after(insertButtonDiv);
	
	self.addHeader = function(title, className) {
		var li = $('<li></li>').attr('class', className).append(
			$('<div class="show"></div>').text(title)
		);
		headerRowUl.append(li);
	}
	
	self.addRow = function(row) {
		rows.push(row);
		$elem.append(row.elem);
	}
	getRow = function(index) {
		return rows[index];
	}
	getCell = function(x,y) {
		var row = getRow(y);
		if (row) return row.getCell(x);
	}
	
	return self;
}

function GridRow() {
	var self = {};
	
	var cells = [];
	
	var $elem = $('<li class="data_row"></li>');
	self.elem = $elem.get(0);
	var fieldsUl = $('<ul class="fields"></ul>');
	var fieldsUlElem = fieldsUl.get(0);
	$elem.append(fieldsUl, '<div style="clear: both;"></div>');
	
	self.addCell = function(cell) {
		cells.push(cell);
		fieldsUl.append(cell.elem);
	}
	self.getCell = function(index) {
		return cells[index];
	}
	self.getCellCount = function() {
		return cells.length;
	}
	
	/* return the index of the GridCell object whose DOM element is, or contains, childElem,
		or null if childElement is not contained in a cell of this row
	*/
	self.cellIndexForElement = function(childElem) {
		/* walk up childElem's parent elements until we find an immediate child of
			the fieldsUlElem element */
		var elemToTest = childElem;
		while (elemToTest.parentElement && elemToTest.parentElement != fieldsUlElem) {
			elemToTest = elemToTest.parentElement;
		}
		if (elemToTest.parentElement) {
			/* check each cell in turn to see if its element is the one we've found */
			for (var i = 0; i < cells.length; i++) {
				if (cells[i].elem == elemToTest) return i;
			}
		}
	}
	
	return self;
}

function GridCell(opts) {
	if (!opts) opts = {};
	var self = {};
	
	var $elem = $('<li></li>')
	self.elem = $elem.get(0);
	if (opts['class']) $elem.addClass(opts['class']);
	
	var showElem = $('<div class="show"></div>');
	$elem.append(showElem);
	if (opts.value) showElem.text(opts.value);
	
	self.receiveCursor = function() {
		$elem.addClass('cursor');
	}
	self.loseCursor = function() {
		$elem.removeClass('cursor');
	}
	
	return self;
}

function ResultsTable(elem, opts) {
	var grid = EditableGrid(elem);
	grid.addHeader('Placing', 'placing_field');
	grid.addHeader('Title', 'title_field');
	grid.addHeader('By', 'by_field');
	grid.addHeader('Platform', 'platform_field');
	grid.addHeader('Type', 'type_field');
	grid.addHeader('Score', 'score_field');
	
	if (opts.competitionPlacings.length) {
		for (var i = 0; i < opts.competitionPlacings.length; i++) {
			var competitionPlacing = CompetitionPlacing(opts.competitionPlacings[i]);
			grid.addRow(competitionPlacing.row);
		}
	} else {
		/* add an initial empty row */
		var competitionPlacing = CompetitionPlacing();
		grid.addRow(competitionPlacing.row);
	}
}

function CompetitionPlacing(data) {
	if (!data) data = {};
	if (!data.production) data.production = {};
	if (!data.production.byline) data.production.byline = {};
	
	var self = {};
	
	self.row = GridRow();
	
	var cellOrder = ['placing', 'title', 'by', 'platform', 'type', 'score'];
	var cells = {
		'placing': GridCell({'class': 'placing_field', 'value': data.ranking}),
		'title': GridCell({'class': 'title_field', 'value': data.production.title}),
		'by': GridCell({'class': 'by_field', 'value': data.production.byline.search_term}),
		'platform': GridCell({'class': 'platform_field'}),
		'type': GridCell({'class': 'type_field'}),
		'score': GridCell({'class': 'score_field', 'value': data.score})
	}
	for (var i = 0; i < cellOrder.length; i++) {
		self.row.addCell(cells[cellOrder[i]]);
	}
	
	return self;
}
