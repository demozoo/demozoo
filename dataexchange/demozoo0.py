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

def productions_by_releaser(releaser_id):
	return run_productions_query('''
		SELECT DISTINCT
			productions.id, productions.name, productions.pouet_id, productions.csdb_id
		FROM
			productions
			LEFT JOIN authorships ON (productions.id = authorships.production_id)
			LEFT JOIN nicks ON (authorships.nick_id = nicks.id)
			LEFT JOIN authorship_affiliations ON (authorships.id = authorship_affiliations.authorship_id)
			LEFT JOIN nicks AS affil_nicks ON (authorship_affiliations.group_nick_id = affil_nicks.id)
		WHERE
			nicks.releaser_id = %s OR affil_nicks.releaser_id = %s
	''', (releaser_id, releaser_id))

def all_party_series():
	cur = connection.cursor()
	cur.execute("SELECT id, name, website, pouet_id FROM party_series WHERE name IS NOT NULL")
	columns = ['id','name','website','pouet_id']
	for row in cur:
		info = dict(zip(columns, row))
		yield info

def all_users():
	cur = connection.cursor()
	cur.execute("SELECT id, email, created_at, nick FROM users")
	columns = ['id','email','created_at','nick']
	for row in cur:
		info = dict(zip(columns, row))
		yield info

def all_releasers():
	cur = connection.cursor()
	cur.execute('''
		SELECT id, type, pouet_id, zxdemo_id, name, abbreviation, website, csdb_id, country_id, slengpung_id
		FROM releasers
	''')
	columns = ['id','type','pouet_id','zxdemo_id','name','abbreviation','website','csdb_id','country_id','slengpung_id']
	for row in cur:
		info = dict(zip(columns, row))
		info['name'] = info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		yield info

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

def production_type_ids_for_production(production_id):
	cur = connection.cursor()
	cur.execute('''
		SELECT production_type_id FROM production_types_productions
		WHERE production_id = %s
	''', (production_id,) )
	return [row[0] for row in cur]

def platform_ids_for_production(production_id):
	cur = connection.cursor()
	cur.execute('''
		SELECT platform_id FROM production_platforms
		WHERE production_id = %s AND platform_id != 74 -- platform_id 74 is 'null'
	''', (production_id,) )
	return [row[0] for row in cur]
