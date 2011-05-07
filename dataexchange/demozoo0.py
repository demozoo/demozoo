import pymysql

connection = pymysql.connect(user="root", db="demozoo_production", charset="latin1")

def run_productions_query(sql, params = (), columns = ('id', 'name', 'pouet_id', 'csdb_id')):
	cur = connection.cursor()
	cur.execute(sql, params)
	for row in cur:
		info = dict(zip(columns, row))
		info['name'] = info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		yield info

def all_productions():
	return run_productions_query('''
		SELECT
			productions.id, productions.name, productions.pouet_id, productions.csdb_id
		FROM
			productions
		ORDER BY productions.id
	''')

def productions_with_credits():
	return run_productions_query('''
		SELECT DISTINCT
			productions.id, productions.name, productions.pouet_id, productions.csdb_id
		FROM
			productions
			INNER JOIN credits ON (productions.id = credits.production_id)
		ORDER BY productions.id
	''')

def author_and_affiliation_names(production_id):
	cur = connection.cursor()
	cur.execute('''
		(
			SELECT nick_variants.name
			FROM authorships
			INNER JOIN nick_variants ON (authorships.nick_id = nick_variants.nick_id)
			WHERE authorships.production_id = %s
		) UNION (
			SELECT nick_variants.name
			FROM authorships
			INNER JOIN authorship_affiliations ON (authorships.id = authorship_affiliations.authorship_id)
			INNER JOIN nick_variants ON (authorship_affiliations.group_nick_id = nick_variants.nick_id)
			WHERE authorships.production_id = %s
		)
	''', (production_id,production_id) )
	for row in cur:
		yield row[0]
