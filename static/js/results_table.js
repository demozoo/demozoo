(function($) {
	$.fn.resultsTable = function() {
		var resultsTable = this;
		
		var textField = {
			getData: function(container) {
				return $(':input', container).val();
			},
			setData: function(container, data) {
				$(':input', container).val(data);
			},
			writeShowView: function(showContainer, data) {
				$(showContainer).text(data);
			},
			escapable: true
		};
		var selectField = {
			getData: function(container) {
				return $(':input', container).val();
			},
			setData: function(container, data) {
				$(':input', container).val(data);
			},
			writeShowView: function(showContainer, data) {
				$(showContainer).text(data);
			},
			escapable: false
		};
		
		var fieldsByContainerClass = {
			'placing_field': textField,
			'title_field': textField,
			'by_field': textField,
			'platform_field': selectField,
			'type_field': selectField,
			'score_field': textField
		};
		
		var cells = [];
		var rows = $('> li.results_row', resultsTable);
		var rowCount = rows.length;
		var columnCount = 6;
		
		function prependInsertLink(li) {
			var insertLink = $('<a class="insert" tabindex="-1" title="Insert row here" href="javascript:void(0)">insert &rarr;</a>');
			$(li).prepend(insertLink);
			insertLink.click(function() {
				insertAndFocusRow(rows.index(li));
			})
		}
		
		function insertAndFocusRow(position) {
			if (position == null || position < 0) position = rowCount;
			addRow(position, true);
			$(resultsTable).focus();
			setCursor(position, 1);
		}
		
		rows.each(function(y) {
			cells[y] = [];
			$('ul.fields > li', this).each(function(x) {
				cells[y][x] = this;
				$('> .edit', this).hide();
			})
			prependInsertLink(this);
		})
		/* add button for appending to the list */
		var insertButton = $('<input type="button" class="add" value="Add row" />');
		var insertButtonDiv = $('<div class="results_table_insert"></div>');
		insertButtonDiv.append(insertButton);
		$(resultsTable).after(insertButtonDiv);
		
		insertButton.click(function() {
			/* set timeout so that button acquires focus before we revert focus to the table */
			setTimeout(function() {
				insertAndFocusRow();
			}, 10);
		});
		
		function addRow(position, animate) {
			if (position == null || position < 0) position = rowCount;
			var fields = $('<ul class="fields"></ul>');
			var placingField = $('<li class="placing_field"><div class="show"></div><div class="edit"><input type="text" value="" /></div></li>');
			var match;
			var newPlacing;
			if (position > 0) {
				var lastPlacing = rows.eq(position - 1).find(':input').val();
				var lastPlacingNum = parseInt(lastPlacing, 10);
				if (!isNaN(lastPlacingNum)) {
					newPlacing = lastPlacingNum + 1;
				} else if (match = lastPlacing.match(/^\s*\=(\d+)/)) {
					lastPlacingNum = parseInt(match[1], 10);
					/* re-use this string, unless there's one above it and it also matches,
						in which case increment */
					newPlacing = lastPlacing;
					if (position > 1) {
						var lastLastPlacing = rows.eq(position - 2).find(':input').val();
						if (match = lastLastPlacing.match(/^\s*\=(\d+)/)) {
							if (match[1] == lastPlacingNum) newPlacing = lastPlacingNum + 1;
						}
					}
				}
				placingField.find(':input').val(newPlacing);
				placingField.find('.show').text(newPlacing);
			}
			fields.append(placingField);
			fields.append('<li class="title_field"><div class="show"></div><div class="edit"><input type="text" value="" /></div></li>');
			fields.append('<li class="by_field"><div class="show"></div><div class="edit"><input type="text" value="" /></div></li>');
			fields.append('<li class="platform_field"><div class="show"></div><div class="edit"><select><option selected="selected">Spectrum</option><option>Commodore 64</option></select></div></li>');
			fields.append('<li class="type_field"><div class="show"></div><div class="edit"><select><option selected="selected">Demo</option><option>Intro</option></select></div></li>');
			fields.append('<li class="score_field"><div class="show"></div><div class="edit"><input type="text" value="" /></div></li>');
			var row = $('<li class="results_row"></li>').append(fields, '<div style="clear: both;"></div>');
			if (position == rowCount) {
				$(resultsTable).append(row);
			} else {
				rows.eq(position).before(row);
			}
			if (animate) {
				/* can't use slideDown because it gets height wrong :-( */
				fields.css({'height': '0'}).animate({'height': '20px'});
			}
			prependInsertLink(row);
			cells.splice(position, 0, []); /* insert [] at position */
			$('ul.fields > li', row).each(function(x) {
				cells[position][x] = this;
				$('> .edit', this).hide();
			})
			rowCount++;
			if (cursorY >= position) cursorY++;
			rows = $('> li.results_row', resultsTable);
		}
		
		var cursorX, cursorY;
		
		function setCursorIfInRange(y,x) {
			if (y < 0 || y >= rowCount || x < 0 || x >= columnCount) {
				/* out of range */
			} else {
				setCursor(y,x);
			}
		}
		
		function setCursor(y, x, finishEditIfMoving) {
			if (y == cursorY && x == cursorX) return;
			if (cursorY != null && cursorX != null) {
				$(cells[cursorY][cursorX]).removeClass('cursor');
			}
			cursorY = y;
			cursorX = x;
			$(cells[cursorY][cursorX]).addClass('cursor');
		}
		
		/* edit modes:
			null = not editing
			'capturedText' = do not select on focus; cursor keys move caret
			'uncapturedText' = select on focus; cursor keys move cell
		*/
		var editMode = null;
		var initialFieldData = null;
		
		function startEdit(mode) {
			var cell = cells[cursorY][cursorX];
			$('> .show', cell).hide();
			$('> .edit', cell).show();
			editMode = mode;
			field = fieldsByContainerClass[getCellType(cell)];
			initialFieldData = field.getData(cell);
			var input = $(':input:visible', cell)[0];
			if (input) {
				input.focus();
				if (mode == 'uncapturedText') {
					if (input.select) input.select();
				} else {
					input.value = input.value; /* set caret to end */
				}
				/* TODO: make select boxes respond to the initial keypress as if
				they'd received it themselves */
			}
		}
		
		function getCellType(cell) {
			var classes = $(cell).attr('class').split(/\s+/);
			for (var i = 0; i < classes.length; i++) {
				if (classes[i].match(/_field$/)) return classes[i];
			}
		}
		
		function finishEdit() {
			var cell = cells[cursorY][cursorX];
			var input = $(':input:visible', cell)[0];
			$('> .show', cell).show();
			$('> .edit', cell).hide();
			if (input) {
				/* quick + dirty method to set show text to form field */
				field = fieldsByContainerClass[getCellType(cell)];
				field.writeShowView($('> .show', cell), field.getData(cell));
			}
			editMode = null;
		}
		
		function finishEditAndAdvance() {
			finishEdit();
			if (cursorX == columnCount - 1) {
				if (cursorY == rowCount - 1) {
					/* need to create next row before moving there */
					addRow();
				}
				setCursorIfInRange(cursorY + 1, 1); /* NB skip column 0 */
			} else {
				setCursorIfInRange(cursorY, cursorX + 1);
			}
		}
		
		function cancelEdit() {
			var cell = cells[cursorY][cursorX];
			$('> .show', cell).show();
			$('> .edit', cell).hide();
			field = fieldsByContainerClass[getCellType(cell)];
			field.setData(cell, initialFieldData);
			// field.writeShowView($('> .show', cell), initialFieldData);
			editMode = null;
		}
		
		function getElementCoordinates(element) {
			/* check that element is a field li */
			if (!$(element).is('li.results_row ul.fields > li')) {
				/* see if element is a child of a field li instead */
				var fieldLiArray = $(element).parents('li.results_row ul.fields > li');
				/* if so, work with that parent */
				if (fieldLiArray[0]) {
					element = fieldLiArray[0];
				} else {
					return null;
				}
			}
			return [rows.index($(element).parent().parent()), $(element).index()];
		}
		
		/* TODO: add an initial row if cells[0] is undefined */
		setCursor(0, 1);
		
		$(document).mousedown(function(event) {
			c = getElementCoordinates(event.target);
			if (c) {
				if (c[0] == cursorY && c[1] == cursorX) return; /* continue editing if cursor is already here */
				finishEdit();
				setCursor(c[0], c[1]);
			} else if (editMode) {
				finishEdit();
			}
		}).click(function(event) {
			if ($(event.target).parents('ul.results_table').length) {
				/* clicking within table */
			} else {
				blur();
			}
		}).dblclick(function(event) {
			c = getElementCoordinates(event.target);
			if (c) {
				setCursor(c[0], c[1]);
				startEdit('capturedText');
			}
		});
		
		function keydown(event) {
			switch(editMode) {
				case null:
					switch (event.which) {
						case 9: /* tab */
							if (event.shiftKey) {
								if (cursorX == 0 && cursorY == 0) {
									/* allow tab to escape the grid */
									blur();
									return;
								} else if (cursorX == 0) {
									setCursorIfInRange(cursorY - 1, columnCount - 1);
								} else {
									setCursorIfInRange(cursorY, cursorX - 1);
								}
								setTimeout(function() {$(resultsTable.focus())}, 100);
							} else {
								if (cursorX == columnCount - 1 && cursorY == rowCount - 1) {
									/* allow tab to escape the grid */
									blur();
									return;
								} else if (cursorX == columnCount - 1) {
									setCursorIfInRange(cursorY + 1, 0);
								} else {
									setCursorIfInRange(cursorY, cursorX + 1);
								}
								setTimeout(function() {$(resultsTable.focus())}, 100);
							}
							return;
						case 13: /* enter */
							startEdit('capturedText');
							return;
						case 37: /* cursor left */
							setCursorIfInRange(cursorY, cursorX - 1);
							resultsTable.focus();
							return;
						case 38: /* cursor up */
							setCursorIfInRange(cursorY - 1, cursorX);
							resultsTable.focus();
							return;
						case 39: /* cursor right */
							setCursorIfInRange(cursorY, cursorX + 1);
							resultsTable.focus();
							return;
						case 40: /* cursor down */
							setCursorIfInRange(cursorY + 1, cursorX);
							resultsTable.focus();
							return;
					}
					return;
				case 'capturedText':
					switch (event.which) {
						case 9: /* tab */
							finishEdit();
							keydown(event); /* rerun event in 'moving' mode */
							return;
						case 13: /* enter */
							finishEditAndAdvance();
							return;
						case 27: /* escape */
							cancelEdit();
							return;
					}
					return;
				case 'uncapturedText':
					switch (event.which) {
						case 9: /* tab */
							finishEdit();
							keydown(event); /* rerun event in 'moving' mode */
							return;
						case 13: /* enter */
							finishEditAndAdvance();
							return;
						case 27: /* escape */
							cancelEdit();
							return;
						case 37: /* cursor left */
						case 38: /* cursor up */
						case 39: /* cursor right */
						case 40: /* cursor down */
							finishEdit();
							keydown(event); /* rerun event in 'moving' mode */
							return;
					}
					return;
				
				//default:
				//	console.log(event);
			}
		}
		function keypress(event) {
			/* printable characters */
			if (editMode == null) {
				if (event.which == 13) return; /* enter is handled as a special case in keydown */
				/* see if we can edit in 'uncapturedText' mode */
				var cell = cells[cursorY][cursorX];
				field = fieldsByContainerClass[getCellType(cell)];
				if (field.escapable) {
					startEdit('uncapturedText');
				} else {
					startEdit('capturedText');
				}
			}
		}
		
		/* dummy input fields to hide the flicker of focus on other elements after tabbing */
		var tabBuffer1 = $('<input disabled="disabled" style="position: absolute; width: 1px; left: -5000px;">');
		var tabBuffer2 = $('<input disabled="disabled" style="position: absolute; width: 1px; left: -5000px;">');
		$(resultsTable).before(tabBuffer1);
		$(resultsTable).after(tabBuffer2);
		
		function blur() {
			$(resultsTable).removeClass('focused');
			tabBuffer1.attr('disabled', 'disabled');
			tabBuffer2.attr('disabled', 'disabled');
			if (editMode) finishEdit(); /* TODO: also send to server */
			$(document).unbind('keydown', keydown);
			$(document).unbind('keypress', keypress);
		}
		
		if ($(resultsTable).attr('tabindex') == null) {
			$(resultsTable).attr('tabindex', 0);
		}
		
		$(resultsTable).focus(function() {
			if (!$(this).hasClass('focused')) {
				$(this).addClass('focused');
				tabBuffer1.removeAttr('disabled');
				tabBuffer2.removeAttr('disabled');
				$(document).bind('keydown', keydown);
				$(document).bind('keypress', keypress);
			}
		})
	}
})(jQuery);
