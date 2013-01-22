# Parsers for results text files in various formats.
# Each one returns a list of (ranking, title, author, score) tuples


# Tab-separated values
def tsv(results_text):
	rows = []
	result_lines = results_text.split('\n')
	for line in result_lines:
		fields = [field.strip() for field in line.split('\t')] + ['', '', '', '']
		placing, title, byline, score = fields[0:4]
		rows.append((placing, title, byline, score))
	return rows
