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
	
	var input, bylineField, matchContainer;
	self._initEditElem = function(editElem) {
		bylineField = $('<div class="byline_field"><div class="byline_search"><input type="text" /></div><div class="byline_match_container"></div></div>')
		editElem.append(bylineField);
		input = bylineField.find('input');
		matchContainer = bylineField.find('.byline_match_container');
		bylineField.bylineField();
	}
	self._refreshShowElem = function(showElem, value) {
		showElem.text(value.search_term);
	}
	var originalMatchHtml;
	self._refreshEditElem = function(editElem, value) {
		input.val(value.search_term);
		originalMatchHtml = value.matches;
		refreshBylineMatchFields(bylineField, value.matches);
	}
	self._valueFromEditElem = function(editElem) {
		return {
			'search_term': input.val(),
			'matches': originalMatchHtml
			/* TODO: either reduce this to the HTML fragment prior to applying nickMatchWidget decoration,
				or make nickMatchWidget smart enough to not do it twice */
		};
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
	
	self.constructElem();
	return self;
}

function CompetitionPlacing(data, table, row, opts) {
	if (!data) data = {};
	if (!data.production) data.production = {};
	if (!data.production.byline) data.production.byline = {};
	
	var self = {};
	self.row = row;
	
	var cellOrder = ['placing', 'title', 'by', 'platform', 'type', 'score'];
	var cells = {
		'placing': TextGridCell({'class': 'placing_field', 'value': data.ranking}),
		'title': TextGridCell({'class': 'title_field', 'value': data.production.title}),
		'by': BylineGridCell({'class': 'by_field', 'value': data.production.byline}),
		'platform': SelectGridCell({'class': 'platform_field', 'options': opts.platforms, 'value': data.production.platform}),
		'type': SelectGridCell({'class': 'type_field', 'options': opts.productionTypes, 'value': data.production.productionTypes}),
		'score': TextGridCell({'class': 'score_field', 'value': data.score})
	}
	for (var i = 0; i < cellOrder.length; i++) {
		self.row.addCell(cells[cellOrder[i]]);
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
	
	return self;
}
