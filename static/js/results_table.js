(function($) {
	$.fn.resultsTable = function(opts) { this.each(function() {
		var resultsTable = this;
		
		var platformIds = [];
		var platformsById = {};
		for (var i = 0; i < opts['platforms'].length; i++) {
			platformIds[i] = opts['platforms'][i][0];
			platformsById[opts['platforms'][i][0]] = opts['platforms'][i][1];
		}
		var productionTypeIds = [];
		var productionTypesById = {};
		for (var i = 0; i < opts['production_types'].length; i++) {
			productionTypeIds[i] = opts['production_types'][i][0];
			productionTypesById[opts['production_types'][i][0]] = opts['production_types'][i][1];
		}
		
		/* Field-type handlers */
		TextField = function() {
		}
		TextField.prototype.initField = function(field, position) {
			field.find('> .edit').append('<input type="text" value="" />');
		}
		TextField.prototype.getData = function(container) {
			return $(':input', container).val();
		}
		TextField.prototype.setData = function(container) {
			$(':input', container).val(data);
		}
		TextField.prototype.writeShowView = function(showContainer, data) {
			$(showContainer).text(data);
		}
		TextField.prototype.keydown = function(e) {
			//startEdit('capturedText');
		}
		TextField.prototype.keypress = function(e) {
			startEdit('uncapturedText');
		}
		TextField.prototype.escapable = true;
		
		PlacingField = function() {
		}
		PlacingField.prototype = new TextField();
		PlacingField.prototype.initField = function(field, position) {
			TextField.prototype.initField.call(this, field, position);
			var placing = placingForPosition(position, false);
			if (placing) {
				field.find('> .edit :input').val(placing);
				field.find('> .show').text(placing);
			}
		}
		
		SelectField = function(mapping, optionIds) {
			this.mapping = mapping;
			this.optionIds = optionIds;
		}
		SelectField.prototype.initField = function(field, position) {
			var select = $('<select><option value=""></option></select>');
			for (var i = 0; i < this.optionIds.length; i++) {
				var option = $('<option></option>');
				option.attr('value', this.optionIds[i]).text(this.mapping[this.optionIds[i]]);
				select.append(option);
			}
			field.find('> .edit').append(select);
		}
		SelectField.prototype.getData = function(container) {
			return $(':input', container).val();
		}
		SelectField.prototype.setData = function(container, data) {
			$(':input', container).val(data);
		}
		SelectField.prototype.writeShowView = function(showContainer, data) {
			$(showContainer).text(this.mapping[data]);
		}
		SelectField.prototype.keypress = function(e) {
			//startEdit('capturedText');
		}
		SelectField.prototype.keydown = function(e) {
			// respond to alphanumeric keys by focusing the dropdown
			// (all prod types and platforms start with alphanumerics)
			if ( (e.which >= 48 && e.which <= 57) || (e.which >= 65 && e.which <= 90) ) {
				startEdit('capturedText');
			}
		}
		SelectField.prototype.escapable = false;
		
		var fieldClasses = ['placing_field','title_field','by_field','platform_field','type_field','score_field'];
		var fieldsByContainerClass = {
			'placing_field': new PlacingField(),
			'title_field': new TextField(),
			'by_field': new TextField(),
			'platform_field': new SelectField(platformsById, platformIds),
			'type_field': new SelectField(productionTypesById, productionTypeIds),
			'score_field': new TextField()
		};
		
		var cells, rows, rowCount;
		var columnCount = 6;
		
		function constructCellLookups() {
			cells = [];
			rows = $('> li.results_row', resultsTable);
			rowCount = rows.length;
			rows.each(function(y) {
				cells[y] = [];
				$('ul.fields > li', this).each(function(x) {
					cells[y][x] = this;
				})
			})
		}
		constructCellLookups();
		
		$(resultsTable).sortable({
			'axis': 'y',
			'distance': 1,
			'items': 'li.results_row',
			'update': function(event, ui) {
				row = ui.item[0];
				//var originalIndex = rows.index(row);
				constructCellLookups();
				var newIndex = rows.index(row);
				cursorY = newIndex;
				/* fill in placing of just-dragged element, if empty */
				var placingField = $(row).find('> ul.fields > li.placing_field');
				var oldPlacing = placingField.find('> .edit :input').val();
				if (oldPlacing.match(/^\s*$/)) {
					var placing = placingForPosition(newIndex, true);
					if (placing) {
						placingField.find('> .edit :input').val(placing);
						placingField.find('> .show').text(placing);
					}
				}
			}
		})
		
		function prependInsertLink(li) {
			var insertLink = $('<a class="insert" tabindex="-1" title="Insert row here" href="javascript:void(0)">insert &rarr;</a>');
			$(li).prepend(insertLink);
			insertLink.click(function() {
				insertAndFocusRow(rows.index(li));
			})
		}
		
		function appendDeleteLink(li) {
			var deleteLink = $('<a href="javascript:void(0)" tabindex="-1" class="delete" title="Delete this row">Delete</a>');
			$(li).find('> ul.fields').after(deleteLink);
			deleteLink.click(function() {
				/* TODO: what happens if we're in edit mode? */
				$(li).fadeOut('fast', function() {
					$(li).remove();
					var position = rows.index(li);
					
					cells.splice(position, 1); /* remove row at position */
					rowCount--;
					rows = $('> li.results_row', resultsTable);
					if (cursorY > position) {
						cursorY--;
					} else if (cursorY == position) {
						if (rowCount == 0) {
							/* TODO: establish sensible behaviour for empty table / no cursor position */
						} else if (cursorY == rowCount) {
							setCursor(cursorY - 1, cursorX);
						} else {
							setCursor(cursorY, cursorX, true);
						}
					}
				});
			})
		}
		
		function insertAndFocusRow(position) {
			if (position == null || position < 0) position = rowCount;
			addRow(position, true);
			$(resultsTable).focus();
			setCursor(position, 1);
		}
		
		rows.each(function(y) {
			$('ul.fields > li > .edit', this).hide();
			prependInsertLink(this);
			appendDeleteLink(this);
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
		
		function placingForPosition(position, allowFirst) {
			var match;
			var newPlacing;
			if (position == 0) {
				return (allowFirst ? '1' : null);
			} else {
				var lastPlacing = rows.eq(position - 1).find('> ul.fields > li.placing_field > .edit :input').val();
				var lastPlacingNum = parseInt(lastPlacing, 10);
				if (!isNaN(lastPlacingNum)) {
					newPlacing = lastPlacingNum + 1;
				} else if (match = lastPlacing.match(/^\s*\=(\d+)/)) {
					lastPlacingNum = parseInt(match[1], 10);
					/* re-use this string, unless there's one above it and it also matches,
						in which case increment */
					newPlacing = lastPlacing;
					if (position > 1) {
						var lastLastPlacing = rows.eq(position - 2).find('> ul.fields > li.placing_field > .edit :input').val();
						if (match = lastLastPlacing.match(/^\s*\=(\d+)/)) {
							if (match[1] == lastPlacingNum) newPlacing = lastPlacingNum + 1;
						}
					}
				}
				return newPlacing;
			}
		}
		
		function addRow(position, animate) {
			if (position == null || position < 0) position = rowCount;
			var fields = $('<ul class="fields"></ul>');
			
			for (var i = 0; i < fieldClasses.length; i++) {
				field = $('<li><div class="show"></div><div class="edit"></div></li>');
				field.addClass(fieldClasses[i]);
				fields.append(field);
				fieldsByContainerClass[fieldClasses[i]].initField(field, position);
			}
			
			var row = $('<li class="results_row"></li>').append(fields, '<div style="clear: both;"></div>');
			if (position == rowCount) {
				$(resultsTable).append(row);
			} else {
				rows.eq(position).before(row);
			}
			if (animate) {
				/* can't use slideDown because it gets height wrong :-( */
				fields.css({'height': '0'}).animate({'height': '20px'}, {
					'duration': 'fast',
					'complete': function() {
						fields.css({'height': 'auto'});
						appendDeleteLink(row);
					}
				});
			}
			prependInsertLink(row);
			if (!animate) appendDeleteLink(row);
			
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
		
		function setCursor(y, x, skipShortcut) {
			if (!skipShortcut && y == cursorY && x == cursorX) return;
			if (cursorY != null && cursorX != null && cursorY < rowCount) {
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
				$(resultsTable).focus();
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
								return false;
								//setTimeout(function() {$(resultsTable.focus())}, 100);
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
								return false;
								//setTimeout(function() {$(resultsTable.focus())}, 100);
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
						case 86: /* V (for cmd+V=paste) */
							if (event.metaKey) {
								/* TODO: check whether we need to test event.ctrlKey instead on Windows */
								startEdit('uncapturedText');
							}
							return;
						default:
							/* handle other keys according to field type */
							var cell = cells[cursorY][cursorX];
							field = fieldsByContainerClass[getCellType(cell)];
							return field.keydown(event);
					}
					return;
				case 'capturedText':
					switch (event.which) {
						case 9: /* tab */
							finishEdit();
							return keydown(event); /* rerun event in 'moving' mode */
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
							return keydown(event); /* rerun event in 'moving' mode */
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
				/* handle other keys according to field type */
				var cell = cells[cursorY][cursorX];
				field = fieldsByContainerClass[getCellType(cell)];
				return field.keypress(event);
			}
		}
		
		function blur() {
			$(resultsTable).removeClass('focused');
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
				$(document).bind('keydown', keydown);
				$(document).bind('keypress', keypress);
			}
		})
	}) }
})(jQuery);
