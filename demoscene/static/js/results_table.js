function ResultsTable(elem, opts) {
	var self = {};

	var grid = EditableGrid(elem);
	self.grid = grid;
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

	self.competition = opts.competition;

	/* Suggest a value for the 'placing' field of the row in position 'position', based on the
		'placing' values of its neighbours. If allowFirst is true, suggest '1' as a placing at the
		top of the table (which is appropriate when reordering, but not for inserting new rows) */
	self.placingForPosition = function(position, allowFirst) {
		var match;
		var newPlacing;

		if (position === 0) {
			/* entry is at the top of the table. Give it a placing of '1' or leave it blank, according to allowFirst */
			return (allowFirst ? '1' : null);
		} else {
			/* try to interpret the placing of the entry above as a number */
			var lastPlacing = self.placings[position - 1].getPlacing();
			var lastPlacingNum = parseInt(lastPlacing, 10);
			if (!isNaN(lastPlacingNum)) {
				/* The placing above parses as a number, so set this placing to be one more */
				newPlacing = lastPlacingNum + 1;
			} else {
				/* see if the placing above is of the format '=7', indicating a tied placing */
				match = lastPlacing.match(/^\s*\=(\d+)/);
				if (match) {
					lastPlacingNum = parseInt(match[1], 10);
					/* re-use this string, unless there's one above it and it also matches,
						in which case increment */
					newPlacing = lastPlacing;
					if (position > 1) {
						var lastLastPlacing = self.placings[position - 2].getPlacing();
						match = lastLastPlacing.match(/^\s*\=(\d+)/);
						if (match && match[1] == lastPlacingNum) {
							newPlacing = lastPlacingNum + 1;
						}
					}
				}
			}
			return newPlacing;
		}
	};

	self.placings = [];

	var row;
	if (opts.competitionPlacings.length) {
		for (var i = 0; i < opts.competitionPlacings.length; i++) {
			row = grid.addRow();
			self.placings[i] = CompetitionPlacing(opts.competitionPlacings[i], self, row, rowOptions);
		}
	} else {
		/* add an initial empty row */
		row = grid.addRow();
		self.placings[0] = CompetitionPlacing(null, self, row, rowOptions);
	}

	grid.onAddRow.bind(function(row) {
		var rowIndex = row.index.get();
		var competitionPlacing = CompetitionPlacing({
			'ranking': self.placingForPosition(rowIndex, false)
		}, self, row, rowOptions);
		self.placings.splice(rowIndex, 0, competitionPlacing);
		grid.setCursor(1, rowIndex);
		grid.focus();
	});

	grid.onReorder.bind(function(row, oldIndex, newIndex) {
		var placing = self.placings[oldIndex];
		self.placings.splice(oldIndex, 1);
		self.placings.splice(newIndex, 0, placing);
	});

	return self;
}

function BylineGridCell(opts) {
	var self = GridCell(opts);

	var bylineField;

	function valueIsValid(value) {
		var i;
		if (value === null) return true; /* null value is equivalent to empty byline */
		/* consider invalid if any of the authors/affiliations have unspecified (null) IDs */
		for (i = 0; i < value.author_matches.length; i++) {
			if (value.author_matches[i].selection.id === null) {
				return false;
			}
		}
		for (i = 0; i < value.affiliation_matches.length; i++) {
			if (value.affiliation_matches[i].selection.id === null) {
				return false;
			}
		}
		return true;
	}

	self.isValid = function() {
		return valueIsValid(self.value.get());
	};

	self._initEditElem = function(editElem) {
		var bylineFieldElem = $('<div class="byline_field"></div>');
		editElem.append(bylineFieldElem);
		bylineField = BylineField(bylineFieldElem, '', [], [], $.uid('bylineGridCell'));
	};
	self._refreshShowElem = function(showElem, value) {
		if (value) {
			showElem.text(value.search_term || ''); /* TODO: get properly capitalised / primary-nick-varianted text from bylineField */
		} else {
			showElem.text('');
		}
		if (valueIsValid(value)) {
			showElem.removeClass('invalid');
		} else {
			showElem.addClass('invalid');
		}
	};
	self._refreshEditElem = function(editElem, value) {
		bylineField.setValue(value);
	};
	self._valueFromEditElem = function(editElem) {
		return bylineField.getValue();
	};
	self._prepareEditElem = function(editElem) {
		var selectAll = (self._editMode == 'uncapturedText');
		bylineField.focus(selectAll);
		/* ensure that typeahead autocompletion captures the initial keypress even if
		the real keydown event doesn't reach it */
		bylineField.triggerFakeKeydown();
	};
	/* BylineField must capture cursors and tab in all cases,
		but enter can have the standard 'finish edit' behaviour */
	self.keydown = function(event) {
		switch (self._editMode) {
			case null:
				switch (event.which) {
					case 13:
						self._startEdit('capturedText');
						return false;
					case 8: /* backspace */
						self._startEdit('uncapturedText');
						bylineField.setValue(null);
						return false;
					case 86: /* V */
						if (self.eventIsCommandKey(event)) { /* cmd+V = paste */
							self._startEdit('uncapturedText');
							setTimeout(function() {bylineField.lookUpMatches();}, 10);
							return true; /* override grid event handler, defer to browser's own */
						}
						break;
				}
				break;
			case 'capturedText':
			case 'uncapturedText': /* no distinction between captured and uncaptured text here (except for
			whether to cancel default 'advance' event on enter) */
				switch(event.which) {
					case 13: /* enter */
						self._finishEdit();
						return (self._editMode == 'capturedText' ? false : null);
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
							(bylineField.firstFieldIsFocused() && event.shiftKey) ||
							(bylineField.lastFieldIsFocused() && !event.shiftKey)
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
	};
	self.keypress = function(event) {
		switch (self._editMode) {
			case null:
				self._startEdit('uncapturedText');
				break;
		}
	};

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
			'focus': function() {return false;},
			'select': function(event, ui) {
				setTimeout(function() {
					var proceed = self.autocomplete.trigger(ui.item);
					if (proceed) self._finishEdit();
				}, 1);
			}
		});
	};

	var prepareEditElemWithoutAutocomplete = self._prepareEditElem;
	self._prepareEditElem = function(editElem) {
		prepareEditElemWithoutAutocomplete(editElem);
	};

	self._unprepareEditElem = function(editElem) {
		editElem.find('input').autocomplete('close');
		editElem.find('input').blur();
	};

	self.cancelUnlock = Event();

	self.keydown = function(event) {
		switch (self._editMode) {
			case null:
				switch (event.which) {
					case 13:
						self._startEdit('capturedText');
						return false;
					case 8: /* backspace */
						if (self._isLocked) {
							self.requestUnlock.trigger();
						} else {
							self._startEdit('uncapturedText');
							self._input.val('');
						}
						return false;
					case 86: /* V */
						if (self.eventIsCommandKey(event)) { /* cmd+V = paste */
							self._startEdit('uncapturedText');
							setTimeout(function() {
								self._input.autocomplete('search');
							}, 10);
							return true; /* override grid event handler, defer to browser's own */
						}
						break;
				}
				break;
			case 'capturedText':
			case 'unlock':
				switch(event.which) {
					case 13: /* enter */
						/* we want to finish edit UNLESS this keypress causes an autocomplete item to be
						selected, in which case we want the autocomplete's select event to fire and trigger
						the finishEdit call *after* having processed the autocomplete event handler which
						populates the competitionplacing's productionId field */
						setTimeout(function() {
							/* if we're still in edit mode after autocomplete.select has had chance to fire,
								assume we're finishing the edit in the regular way */
							if (self._editMode) self._finishEdit();
						}, 1);
						return false;
					case 27: /* escape */
						var wasUnlocking = (self._editMode == 'unlock');
						self._cancelEdit();
						if (wasUnlocking) self.cancelUnlock.trigger();
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
						setTimeout(function() {
							/* if we're still in edit mode after autocomplete.select has had chance to fire,
								assume we're finishing the edit in the regular way */
							if (self._editMode) {
								self._finishEdit();
								self.grid.advanceOrCreate();
							}
						}, 1);
						return false;
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
	};

	var originalLock = self.lock;
	self.requestUnlock = Event();
	self.lock = function(name, url) {
		originalLock(name);
		self._showElem.wrapInner($('<a></a>').attr({'href': url}));
		var clearButton = $('<a href="javascript:void(0)" class="clear_button">(clear)</a>');
		self._showElem.prepend(clearButton);
		clearButton.click(function() {
			self.requestUnlock.trigger();
		});
	};

	return self;
}

function CompetitionPlacing(data, table, row, opts) {
	var self = {};
	self.row = row;

	if (!data) data = {};
	if (!data.production) data.production = {
		'platform': table.competition.platformId,
		'production_type': table.competition.productionTypeId
	};
	if (!data.production.byline) {
		data.production.byline = {
			'search_term': '', 'author_matches': [], 'affiliation_matches': []
		};
	}

	var productionId = data.production.id;
	var placingId = data.id;

	var isLocked = false;
	var lastLockedData;
	function populateProductionAndLock(production) {
		lastLockedData = production;
		productionId = production.id;
		cells.title.lock(production.title, production.url);
		cells.by.lock(production.byline);
		cells.platform.lock(production.platform_name);
		cells.type.lock(production.production_type_name);
		isLocked = true;
	}

	function isValid() {
		/* Locked productions are always valid;
			unlocked productions are valid if title is nonempty and byline is valid */
		if (isLocked) return true;
		var title = cells.title.value.get();
		return (title !== null && title.match(/\S/) && cells.by.isValid());
	}

	self.existsOnServer = function() {
		return (placingId !== null);
	};

	/* get the index number of this placing within the list, counting only
		entries that exist on the server */
	function serverPosition() {
		var position = 1;
		for (var i = 0; i < table.placings.length; i++) {
			if (table.placings[i] == self) return position;
			if (table.placings[i].existsOnServer()) position++;
		}
	}

	function dataForServer() {
		var i;
		var savedata = {
			position: serverPosition(),
			ranking: cells.placing.value.get(),
			score: cells.score.value.get(),
			production: {
				id: productionId
			}
		};
		if (savedata.ranking === null) savedata.ranking = '';
		if (savedata.score === null) savedata.score = '';

		if (!isLocked) {
			var byline = cells.by.value.get();
			var authorSelections = [];
			for (i = 0; i < byline.author_matches.length; i++) {
				authorSelections.push(byline.author_matches[i].selection);
			}
			var affiliationSelections = [];
			for (i = 0; i < byline.affiliation_matches.length; i++) {
				affiliationSelections.push(byline.affiliation_matches[i].selection);
			}

			savedata.production.title = cells.title.value.get();
			savedata.production.byline = {
				'authors': authorSelections,
				'affiliations': affiliationSelections
			};
			savedata.production.platform_id = cells.platform.value.get();
			savedata.production.production_type_id = cells.type.value.get();
		}
		return savedata;
	}

	var uid = $.uid('competitionplacing');
	function saveIfValid() {
		if (isValid()) {
			var savedata = dataForServer(); /* capture saved state at this point - it may no longer be
				valid if we wait for ajaxQueue callback */
			$.ajaxQueue(uid, function(release) {
				self.row.setStatus('saving', 'Saving...');

				var submitUrl;
				if (placingId === null) {
					submitUrl = '/competition_api/add_placing/' + table.competition.id + '/';
				} else {
					submitUrl = '/competition_api/update_placing/' + placingId + '/';
				}

				$.ajax({
					type: 'POST',
					url: submitUrl,
					dataType: 'json',
					data: JSON.stringify(savedata),
					contentType: 'application/json',
					beforeSend: function(xhr) {
						xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
					},
					error: function() {
						self.row.setStatus('error', 'Error saving row');
						release();
					},
					success: function(newData) {
						cells.placing.value.set(newData.ranking);
						if (newData.production.stable) {
							populateProductionAndLock(newData.production);
						} else {
							cells.title.value.set(newData.production.title);
							cells.by.value.set(newData.production.byline);
							cells.platform.value.set(newData.production.platform);
							cells.type.value.set(newData.production.production_type);
						}
						cells.score.value.set(newData.score);
						productionId = newData.production.id;
						placingId = newData.id;
						self.row.setStatus('normal');
						release();
					}
				});
			});

		} else {
			self.row.setStatus('unsaved', 'Unsaved changes');
		}
	}

	var i;
	var cellOrder = ['placing', 'title', 'by', 'platform', 'type', 'score'];
	var cells;
	if (data.production.stable) {
		cells = {
			'placing': TextGridCell({'class': 'placing_field', 'value': data.ranking}),
			'title': ProductionTitleGridCell({'class': 'title_field', 'value': null}),
			'by': BylineGridCell({'class': 'by_field', 'value': null}),
			'platform': SelectGridCell({'class': 'platform_field', 'options': opts.platforms, 'value': null}),
			'type': SelectGridCell({'class': 'type_field', 'options': opts.productionTypes, 'value': null}),
			'score': TextGridCell({'class': 'score_field', 'value': data.score})
		};
		for (i = 0; i < cellOrder.length; i++) {
			self.row.addCell(cells[cellOrder[i]]);
			cells[cellOrder[i]].onFinishEdit.bind(saveIfValid);
		}
		populateProductionAndLock(data.production);
	} else {
		cells = {
			'placing': TextGridCell({'class': 'placing_field', 'value': data.ranking}),
			'title': ProductionTitleGridCell({'class': 'title_field', 'value': data.production.title}),
			'by': BylineGridCell({'class': 'by_field', 'value': data.production.byline}),
			'platform': SelectGridCell({'class': 'platform_field', 'options': opts.platforms, 'value': data.production.platform}),
			'type': SelectGridCell({'class': 'type_field', 'options': opts.productionTypes, 'value': data.production.production_type}),
			'score': TextGridCell({'class': 'score_field', 'value': data.score})
		};
		for (i = 0; i < cellOrder.length; i++) {
			self.row.addCell(cells[cellOrder[i]]);
			cells[cellOrder[i]].onFinishEdit.bind(saveIfValid);
		}
	}

	if (data.id) {
		self.row.setStatus('normal');
	} else {
		self.row.setStatus('unsaved', 'Unsaved changes');
	}

	self.getPlacing = function() {
		var placing = cells.placing.value.get();
		return (placing === null ? '' : String(placing));
	};
	row.onReorder.bind(function(oldIndex, newIndex) {
		if (self.getPlacing().match(/^\s*$/)) {
			/* placing field not previously populated; auto-populate it now */
			cells.placing.value.set(table.placingForPosition(newIndex, true));
		}
		saveIfValid();
	});

	cells.title.autocomplete.bind(function(production) {
		populateProductionAndLock(production);
		table.grid.setCursor(5, self.row.index.get());
		return false; /* tell the autocomplete handler not to call finishEdit
			(which prematurely submits the entry without an ID) */
	});

	cells.title.requestUnlock.bind(function() {
		cells.title.unlock();
		cells.by.unlock();
		cells.platform.unlock();
		cells.type.unlock();
		isLocked = false;
		productionId = null;
		cells.title._startEdit('unlock');
	});
	cells.title.cancelUnlock.bind(function() {
		populateProductionAndLock(lastLockedData);
	});

	self.row.onDelete.bind(function() {
		$.ajaxQueue(uid, function(release) {
			if (placingId === null) {
				release();
			} else {
				$.ajax({
					type: 'POST',
					url: '/competition_api/delete_placing/' + placingId + '/',
					beforeSend: function(xhr) {
						xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
					},
					complete: function() {
						release();
					}
				});
			}
		});
	});

	return self;
}
