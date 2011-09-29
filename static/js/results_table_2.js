function EditableGrid(elem) {
	var self = {};
	
	elem = $(elem);
	elem.addClass('editable_grid');
	
	var headerRowUl = $('<ul class="fields"></ul>')
	var headerRow = $('<li class="header_row"></li>').append(headerRowUl, '<div style="clear: both;"></div>');
	elem.prepend(headerRow);
	
	var insertButton = $('<input type="button" class="add" value="Add row" />');
	var insertButtonDiv = $('<div class="editable_grid_insert"></div>');
	insertButtonDiv.append(insertButton);
	$(elem).after(insertButtonDiv);
	
	self.addHeader = function(title, className) {
		var li = $('<li></li>').attr('class', className).append(
			$('<div class="show"></div>').text(title)
		);
		headerRowUl.append(li);
	}
	
	self.addRow = function(row) {
		elem.append(row.elem);
	}
	
	return self;
}

function GridRow() {
	var self = {};
	
	self.elem = $('<li class="data_row"></li>');
	var fieldsUl = $('<ul class="fields"></ul>');
	self.elem.append(fieldsUl, '<div style="clear: both;"></div>');
	
	self.addCell = function(cell) {
		fieldsUl.append(cell.elem);
	}
	
	return self;
}

function GridCell(opts) {
	if (!opts) opts = {};
	var self = {};
	
	self.elem = $('<li></li>')
	if (opts['class']) self.elem.addClass(opts['class']);
	
	var showElem = $('<div class="show"></div>');
	self.elem.append(showElem);
	if (opts.value) showElem.text(opts.value);
	
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
	
	for (var i = 0; i < opts.competitionPlacings.length; i++) {
		var competitionPlacing = CompetitionPlacing(opts.competitionPlacings[i]);
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
