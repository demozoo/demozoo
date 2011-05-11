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

def run_releasers_query(sql, params = (), columns = ('id', 'type', 'pouet_id', 'zxdemo_id', 'name', 'abbreviation', 'website', 'csdb_id', 'country_id', 'slengpung_id')):
	cur = connection.cursor()
	cur.execute(sql, params)
	for row in cur:
		info = dict(zip(columns, row))
		info['name'] = info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		yield info

def all_releasers():
	return run_releasers_query('''
		SELECT id, type, pouet_id, zxdemo_id, name, abbreviation, website, csdb_id, country_id, slengpung_id
		FROM releasers
	''')

def releasers_with_credits():
	return run_releasers_query('''
		SELECT DISTINCT
			releasers.id, releasers.type, releasers.pouet_id, releasers.zxdemo_id, releasers.name,
			releasers.abbreviation, releasers.website, releasers.csdb_id, releasers.country_id,
			releasers.slengpung_id
		FROM releasers
			INNER JOIN nicks ON (releasers.id = nicks.releaser_id)
			INNER JOIN credits ON (nicks.id = credits.nick_id)
	''')

def releasers_with_members():
	return run_releasers_query('''
		SELECT DISTINCT
			releasers.id, releasers.type, releasers.pouet_id, releasers.zxdemo_id, releasers.name,
			releasers.abbreviation, releasers.website, releasers.csdb_id, releasers.country_id,
			releasers.slengpung_id
		FROM releasers
			INNER JOIN memberships ON (releasers.id = memberships.group_id)
	''')

def releasers_with_groups():
	return run_releasers_query('''
		SELECT DISTINCT
			releasers.id, releasers.type, releasers.pouet_id, releasers.zxdemo_id, releasers.name,
			releasers.abbreviation, releasers.website, releasers.csdb_id, releasers.country_id,
			releasers.slengpung_id
		FROM releasers
			INNER JOIN memberships ON (releasers.id = memberships.member_id)
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

def names_for_releaser(releaser_id):
	cur = connection.cursor()
	cur.execute('''
		SELECT nick_variants.name FROM nicks
		INNER JOIN nick_variants ON (nicks.id = nick_variants.nick_id)
		WHERE nicks.releaser_id = %s
	''', (releaser_id,) )
	return [row[0] for row in cur]

def groups_for_releaser(releaser_id):
	return run_releasers_query('''
		SELECT DISTINCT
			releasers.id, releasers.type, releasers.pouet_id, releasers.zxdemo_id, releasers.name,
			releasers.abbreviation, releasers.website, releasers.csdb_id, releasers.country_id,
			releasers.slengpung_id
		FROM memberships
			INNER JOIN releasers ON (memberships.group_id = releasers.id)
		WHERE memberships.member_id = %s
	''', (releaser_id,))

def members_for_releaser(releaser_id):
	return run_releasers_query('''
		SELECT DISTINCT
			releasers.id, releasers.type, releasers.pouet_id, releasers.zxdemo_id, releasers.name,
			releasers.abbreviation, releasers.website, releasers.csdb_id, releasers.country_id,
			releasers.slengpung_id
		FROM memberships
			INNER JOIN releasers ON (memberships.member_id = releasers.id)
		WHERE memberships.group_id = %s
	''', (releaser_id,))
