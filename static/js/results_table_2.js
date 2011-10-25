function ResultsTable(elem, opts) {
	var self = {};
	
	var grid = EditableGrid(elem);
	grid.addHeader('Placing', 'placing_field');
	grid.addHeader('Title', 'title_field');
	grid.addHeader('By', 'by_field');
	grid.addHeader('Platform', 'platform_field');
	grid.addHeader('Type', 'type_field');
	grid.addHeader('Score', 'score_field');
	
	var rowOptions = {
		'platforms': opts.platforms,
		'productionTypes': opts.productionTypes
	};
	
	/* Suggest a value for the 'placing' field of the row in position 'position', based on the
		'placing' values of its neighbours. If allowFirst is true, suggest '1' as a placing at the
		top of the table (which is appropriate when reordering, but not for inserting new rows) */
	self.placingForPosition = function(position, allowFirst) {
		var match;
		var newPlacing;
		
		if (position == 0) {
			return (allowFirst ? '1' : null);
		} else {
			var lastPlacing = placings[position - 1].getPlacing();
			var lastPlacingNum = parseInt(lastPlacing, 10);
			if (!isNaN(lastPlacingNum)) {
				newPlacing = lastPlacingNum + 1;
			} else if (match = lastPlacing.match(/^\s*\=(\d+)/)) {
				lastPlacingNum = parseInt(match[1], 10);
				/* re-use this string, unless there's one above it and it also matches,
					in which case increment */
				newPlacing = lastPlacing;
				if (position > 1) {
					var lastLastPlacing = placings[position - 2].getPlacing();
					if (match = lastLastPlacing.match(/^\s*\=(\d+)/)) {
						if (match[1] == lastPlacingNum) newPlacing = lastPlacingNum + 1;
					}
				}
			}
			return newPlacing;
		}
	}
	
	var placings = [];
	
	if (opts.competitionPlacings.length) {
		for (var i = 0; i < opts.competitionPlacings.length; i++) {
			var row = grid.addRow();
			placings[i] = CompetitionPlacing(opts.competitionPlacings[i], self, row, rowOptions);
		}
	} else {
		/* add an initial empty row */
		var row = grid.addRow();
		placings[0] = CompetitionPlacing(null, self, row, rowOptions);
	}
	
	grid.onAddRow.bind(function(row) {
		var rowIndex = row.index.get();
		var competitionPlacing = CompetitionPlacing({
			'ranking': self.placingForPosition(rowIndex, false)
		}, self, row, rowOptions);
		placings.splice(rowIndex, 0, competitionPlacing);
		grid.setCursor(1, rowIndex);
		grid.focus();
	})
	
	grid.onReorder.bind(function(row, oldIndex, newIndex) {
		var placing = placings[oldIndex];
		placings.splice(oldIndex, 1);
		placings.splice(newIndex, 0, placing);
	})
	
	return self;
}

function BylineGridCell(opts) {
	var self = GridCell(opts);
	
	var bylineField;
	
	function valueIsValid(value) {
		/* consider invalid if any of the authors/affiliations have unspecified (null) IDs */
		for (var i = 0; i < value.author_matches.length; i++) {
			if (value.author_matches[i].selection.id == null) {
				return false;
				break;
			}
		}
		for (var i = 0; i < value.affiliation_matches.length; i++) {
			if (value.affiliation_matches[i].selection.id == null) {
				return false;
				break;
			}
		}
		return true;
	}
	
	self._initEditElem = function(editElem) {
		var bylineFieldElem = $('<div class="byline_field"></div>');
		editElem.append(bylineFieldElem);
		bylineField = BylineField(bylineFieldElem, '', [], [], $.uid('bylineGridCell'));
	}
	self._refreshShowElem = function(showElem, value) {
		showElem.text(value.search_term); /* TODO: get properly capitalised / primary-nick-varianted text from bylineField */
		if (valueIsValid(value)) {
			showElem.removeClass('invalid');
		} else {
			showElem.addClass('invalid');
		}
	}
	self._refreshEditElem = function(editElem, value) {
		bylineField.setValue(value);
	}
	self._valueFromEditElem = function(editElem) {
		return bylineField.getValue();
	}
	self._prepareEditElem = function(editElem) {
		var selectAll = (self._editMode == 'uncapturedText')
		bylineField.focus(selectAll);
		/* ensure that typeahead autocompletion captures the initial keypress even if
		the real keydown event doesn't reach it */
		bylineField.triggerFakeKeydown();
	}
	/* BylineField must capture cursors and tab in all cases,
		but enter can have the standard 'finish edit' behaviour */
	self.keydown = function(event) {
		switch (self._editMode) {
			case null:
				switch (event.which) {
					case 13:
						self._startEdit('capturedText');
						return false;
				}
				break;
			case 'capturedText':
			case 'uncapturedText': /* no distinction between captured and uncaptured text here */
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
						/* let bylineField handle cursor keys, unimpeded by EditableGrid behaviour */
						return true;
					case 9: /* tab */
						if (
							(bylineField.firstFieldIsFocused() && event.shiftKey)
							|| (bylineField.lastFieldIsFocused() && !event.shiftKey)
						) {
							/* let default gridcell handler kick in and escape the cell */
							return null;
						} else {
							/* fall back to default browser handler to allow tabbing between bylineField sub-fields */
							return true;
						}
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

function ProductionTitleGridCell(opts) {
	var self = TextGridCell(opts);
	
	var initEditElemWithoutAutocomplete = self._initEditElem;
	
	self.autocomplete = Event();
	
	self._initEditElem = function(editElem) {
		initEditElemWithoutAutocomplete(editElem);
		editElem.find('input').autocomplete({
			'source': function(request, response) {
				$.getJSON('/productions/autocomplete/',
					{'term': request.term},
					function(data) {
						response(data);
					});
			},
			'appendTo': editElem,
			'autoFocus': false,
			/* don't fill in text field on focus, as this makes it look like the item has been chosen
				already, when actually they might leave the cell without selecting it */
			'focus': function() {return false},
			'select': function(event, ui) {
				setTimeout(function() {
					self._finishEdit();
					self.autocomplete.trigger(ui.item);
				}, 1);
			}
		})
	}
	
	var prepareEditElemWithoutAutocomplete = self._prepareEditElem;
	self._prepareEditElem = function(editElem) {
		prepareEditElemWithoutAutocomplete(editElem);
	}
	
	self._unprepareEditElem = function(editElem) {
		editElem.find('input').autocomplete('close');
		editElem.find('input').blur();
	}
	
	self.keydown = function(event) {
		switch (self._editMode) {
			case null:
				switch (event.which) {
					case 13:
						self._startEdit('capturedText');
						return false;
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
					case 37: /* cursors left/right */
					case 39:
						self._finishEdit();
						return null; /* let grid event handler process the cursor movement */
					case 38: /* cursors up/down */
					case 40:
						return true; /* override grid event handler, defer to browser's own */
				}
				break;
		}
	}
	
	return self;
}

function CompetitionPlacing(data, table, row, opts) {
	if (!data) data = {};
	if (!data.production) data.production = {};
	if (!data.production.byline) {
		data.production.byline = {
			'search_term': '', 'author_matches': [], 'affiliation_matches': []
		};
	}
	
	var self = {};
	self.row = row;
	
	var cellOrder = ['placing', 'title', 'by', 'platform', 'type', 'score'];
	var cells = {
		'placing': TextGridCell({'class': 'placing_field', 'value': data.ranking}),
		'title': ProductionTitleGridCell({'class': 'title_field', 'value': data.production.title}),
		'by': BylineGridCell({'class': 'by_field', 'value': data.production.byline}),
		'platform': SelectGridCell({'class': 'platform_field', 'options': opts.platforms, 'value': data.production.platform}),
		'type': SelectGridCell({'class': 'type_field', 'options': opts.productionTypes, 'value': data.production.production_type}),
		'score': TextGridCell({'class': 'score_field', 'value': data.score})
	}
	for (var i = 0; i < cellOrder.length; i++) {
		self.row.addCell(cells[cellOrder[i]]);
	}
	if (data.production.stable) {
		cells.title.lock();
		cells.by.lock();
		cells.platform.lock();
		cells.type.lock();
	}
	
	self.getPlacing = function() {
		var placing = cells.placing.value.get();
		return (placing == null ? '' : String(placing));
	}
	row.onReorder.bind(function(oldIndex, newIndex) {
		if (self.getPlacing().match(/^\s*$/)) {
			/* placing field not previously populated; auto-populate it now */
			cells.placing.value.set(table.placingForPosition(newIndex, true));
		}
	})
	
	cells.title.autocomplete.bind(function(production) {
		cells.title.lock(production.value);
		cells.by.lock(production.byline);
		cells.platform.lock(production.platform_name);
		cells.type.lock(production.production_type_name);
	})
	
	return self;
}
