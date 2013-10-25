import gzip
import re

def parse_all_dirs(filename):
	f = gzip.open(filename, 'rb')

	while True:
		line = f.readline().decode('iso-8859-1')
		if not line:
			break

		m = re.match(r'pub(.*):$', line)
		if m:
			dir_name = m.group(1) + '/'
			# print "found dir: %s" % dir_name
		else:
			raise Exception("Expected dir name line, got %r" % line)

		line = f.readline()
		if not re.match(r'total \d+$', line):
			raise Exception("Expected 'total' line, got %r" % line)

		entries = get_dir_listing(f)
		if not dir_name.startswith('/incoming/'):
			yield (dir_name, entries)

	f.close()


def get_dir_listing(f):
	entries = []

	while True:
		line = f.readline().decode('iso-8859-1')
		if not line or line == "\n":
			break

		m = re.match(r'(.)[rwsx-]{9} +\d+ \w+ +\w+ +(\d+) \w{3} +\d+ +\d\d:?\d\d (.*)', line)
		if m:
			node_type, file_size, filename = m.groups(0)
			if node_type == '-':
				# entries.append(filename, False, file_size)
				entries.append((filename, False))
			elif node_type == 'd':
				entries.append((filename, True))
		else:
			raise Exception("Expected dir entry, got %r" % line)

	return entries
