from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db import connection
import itertools

# given a model class and a field name, determine whether the field is a regular field on the model,
# a relation with a single object on the other end, or a relation with multiple objects on the other end
def recognise_relation_type(model, field_name):
	# TODO: check one-to-one fields in both directions
	try:
		field = model._meta.get_field(field_name)
		if isinstance(field, ForeignKey):
			return ('single', field.rel.to)
		elif isinstance(field, ManyToManyField):
			return ('multiple', field.rel.to)
		else:
			return ('field', None)
	except FieldDoesNotExist:
		# check reverse relations
		for rel in model._meta.get_all_related_objects():
			if rel.get_accessor_name() == field_name:
				return ('multiple', rel.model)
		for rel in model._meta.get_all_related_many_to_many_objects():
			if rel.get_accessor_name() == field_name:
				return ('multiple', rel.model)
		raise FieldDoesNotExist('%s has no field named %r' % (model._meta.object_name, field_name))

def make_unpack_plan(model, columns, prefix = '', plan = []):
	field_map = {
		'model': model,
		'fields': {}
	}
	plan.append(field_map)
	
	seen_field_names = set()
	for (column_index, column) in enumerate(columns):
		if column.startswith(prefix):
			suffix = column[len(prefix):]
			field_name = suffix.split('__')[0]
			if field_name in seen_field_names:
				continue
			seen_field_names.add(field_name)
			rel_type, related_model = recognise_relation_type(model, field_name)
			if rel_type == 'field':
				field_map['fields'][field_name] = column_index
			elif rel_type == 'single':
				make_unpack_plan(related_model, columns, prefix = prefix + field_name + '__', plan = plan)
			else: # rel_type == 'multiple'
				plan.append(
					make_unpack_plan(related_model, columns, prefix = prefix + field_name + '__', plan = [])
				)
	return plan

def unjoinify(model, query, query_params, columns = None):
	cursor = connection.cursor()
	cursor.execute(query, query_params)
	if not columns:
		columns = [column_description[0] for column_description in cursor.description] # don't trust this - 64 char limit :-(
	plan = make_unpack_plan(model, columns)
	return unpack_with_plan(plan, ResultIter(cursor))

# Wrapper for cursor objects to make compatible with the iterator interface
def ResultIter(cursor, arraysize=1000):
	while True:
		results = cursor.fetchmany(arraysize)
		if not results:
			break
		for result in results:
			yield result

# replace all elements of arr whose indexes are not in mask with None
def mask_columns(arr, mask):
	return [(val if i in mask else None) for i,val in enumerate(arr)]

def unpack_with_plan(plan, results):
	columns_for_grouper = set()
	child_count = 0
	for obj in plan:
		if isinstance(obj, dict):
			for col in obj['fields'].values():
				columns_for_grouper.add(col)
		else:
			child_count += 1
	
	output = []
	seen_primary_ids = set()
	for grouper, rows in itertools.groupby(results, lambda row: mask_columns(row, columns_for_grouper)):
		# check primary key of the first model in the plan;
		# if it's null, skip this row (it's an outer join with no match)
		# Also skip if it's one we've seen before (it's a repeat caused by a cartesian join)
		pk_name = plan[0]['model']._meta.pk.name
		pk_index = plan[0]['fields'][pk_name]
		pk_value = grouper[pk_index]
		if pk_value == None or pk_value in seen_primary_ids:
			continue
		
		seen_primary_ids.add(pk_value)
		
		output_row = []
		if child_count > 1:
			# will need to iterate over grouped_results multiple times, so convert rows into a list
			rows = list(rows)
		
		for obj in plan:
			if isinstance(obj, dict):
				fields = {}
				for field_name, index in obj['fields'].iteritems():
					fields[field_name] = grouper[index]
				# if primary key in fields is none, don't instantiate model
				if fields[obj['model']._meta.pk.name] == None:
					output_row.append(None)
				else:
					model = obj['model'](**fields)
					output_row.append(model)
			else:
				output_row.append(unpack_with_plan(obj, rows))
		
		if any(output_row): # skip if all nulls
			if len(plan) == 1:
				output.append(output_row[0])
			else:
				output.append(tuple(output_row))
	
	return output
