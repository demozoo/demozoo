function ResultsTable(elem, opts) {
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
	
	if (opts.competitionPlacings.length) {
		for (var i = 0; i < opts.competitionPlacings.length; i++) {
			var row = grid.addRow();
			var competitionPlacing = CompetitionPlacing(opts.competitionPlacings[i], row, rowOptions);
		}
	} else {
		/* add an initial empty row */
		var row = grid.addRow();
		var competitionPlacing = CompetitionPlacing(null, row, rowOptions);
	}
	
	grid.onAddRow.bind(function(row) {
		var competitionPlacing = CompetitionPlacing(null, row, rowOptions);
		grid.setCursor(1, row.index.get());
		grid.focus();
	})
}

function CompetitionPlacing(data, row, opts) {
	if (!data) data = {};
	if (!data.production) data.production = {};
	if (!data.production.byline) data.production.byline = {};
	
	var self = {};
	self.row = row;
	
	var cellOrder = ['placing', 'title', 'by', 'platform', 'type', 'score'];
	var cells = {
		'placing': TextGridCell({'class': 'placing_field', 'value': data.ranking}),
		'title': TextGridCell({'class': 'title_field', 'value': data.production.title}),
		'by': TextGridCell({'class': 'by_field', 'value': data.production.byline.search_term}),
		'platform': SelectGridCell({'class': 'platform_field', 'options': opts.platforms, 'value': data.production.platform}),
		'type': SelectGridCell({'class': 'type_field', 'options': opts.productionTypes, 'value': data.production.productionTypes}),
		'score': TextGridCell({'class': 'score_field', 'value': data.score})
	}
	for (var i = 0; i < cellOrder.length; i++) {
		self.row.addCell(cells[cellOrder[i]]);
	}
	
	return self;
}
