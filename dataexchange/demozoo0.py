import pymysql

connection = pymysql.connect(user="root", db="demozoo_production", charset="latin1")

def run_productions_query(sql, params = (), columns = ('id', 'name', 'pouet_id', 'zxdemo_id', 'release_date_datestamp', 'release_date_precision', 'scene_org_id', 'csdb_id')):
	cur = connection.cursor()
	cur.execute(sql, params)
	for row in cur:
		info = dict(zip(columns, row))
		info['name'] = info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		yield info

def all_productions():
	return run_productions_query('''
		SELECT
			productions.id, productions.name, productions.pouet_id, productions.zxdemo_id,
			productions.release_date_datestamp, productions.release_date_precision,
			productions.scene_org_id, productions.csdb_id
		FROM
			productions
		ORDER BY productions.id
	''')

def productions_from_zxdemo():
	return run_productions_query('''
		SELECT
			productions.id, productions.name, productions.pouet_id, productions.zxdemo_id,
			productions.release_date_datestamp, productions.release_date_precision,
			productions.scene_org_id, productions.csdb_id
		FROM
			productions
		WHERE
			zxdemo_id IS NOT NULL
		ORDER BY productions.id
	''')

def productions_introduced_on_demozoo0():
	return run_productions_query('''
		SELECT
			productions.id, productions.name, productions.pouet_id, productions.zxdemo_id,
			productions.release_date_datestamp, productions.release_date_precision,
			productions.scene_org_id, productions.csdb_id
		FROM
			productions
		WHERE
			zxdemo_id IS NULL AND pouet_id IS NULL
		ORDER BY productions.id
	''')

def productions_with_credits():
	return run_productions_query('''
		SELECT DISTINCT
			productions.id, productions.name, productions.pouet_id, productions.zxdemo_id,
			productions.release_date_datestamp, productions.release_date_precision,
			productions.scene_org_id, productions.csdb_id
		FROM
			productions
			INNER JOIN credits ON (productions.id = credits.production_id)
		ORDER BY productions.id
	''')

def productions_by_releaser(releaser_id):
	return run_productions_query('''
		SELECT DISTINCT
			productions.id, productions.name, productions.pouet_id, productions.zxdemo_id,
			productions.release_date_datestamp, productions.release_date_precision,
			productions.scene_org_id, productions.csdb_id
		FROM
			productions
			LEFT JOIN authorships ON (productions.id = authorships.production_id)
			LEFT JOIN nicks ON (authorships.nick_id = nicks.id)
			LEFT JOIN authorship_affiliations ON (authorships.id = authorship_affiliations.authorship_id)
			LEFT JOIN nicks AS affil_nicks ON (authorship_affiliations.group_nick_id = affil_nicks.id)
		WHERE
			nicks.releaser_id = %s OR affil_nicks.releaser_id = %s
	''', (releaser_id, releaser_id))

def production_has_competition_placings(production_id):
	cur = connection.cursor()
	cur.execute("SELECT COUNT(*) FROM competition_placings WHERE production_id = %s", (production_id,))
	return cur.fetchone()[0]

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

def download_links_for_production(production_id):
	cur = connection.cursor()
	cur.execute('''
		SELECT id, url, description
		FROM downloads
		WHERE production_id = %s
	''', (production_id,) )
	columns = ['id','url','description']
	return [dict(zip(columns, row)) for row in cur]

def names_for_releaser(releaser_id):
	cur = connection.cursor()
	cur.execute('''
		SELECT nick_variants.name FROM nicks
		INNER JOIN nick_variants ON (nicks.id = nick_variants.nick_id)
		WHERE nicks.releaser_id = %s
	''', (releaser_id,) )
	return [row[0] for row in cur]

def nicks_for_releaser(releaser_id):
	cur = connection.cursor()
	cur.execute('''
		SELECT nicks.id, nicks.name, nicks.abbreviation FROM nicks
		WHERE releaser_id = %s
	''', (releaser_id,) )
	for row in cur:
		info = dict(zip(['id', 'name', 'abbreviation'], row))
		info['name'] = info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		if info['abbreviation']:
			info['abbreviation'] = info['abbreviation'].encode('latin-1').decode('utf-8') # hack to fix encoding
		yield info

def names_for_nick(nick_id):
	cur = connection.cursor()
	cur.execute('''
		SELECT name FROM nick_variants
		WHERE nick_id = %s
	''', (nick_id,) )
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

def authorships_for_production(production_id):
	cur = connection.cursor()
	cur.execute('''
		SELECT authorships.id,
		
		nicks.id, nicks.name, nicks.abbreviation,
		
		releasers.id, releasers.type, releasers.pouet_id, releasers.zxdemo_id, releasers.name,
		releasers.abbreviation, releasers.website, releasers.csdb_id, releasers.country_id,
		releasers.slengpung_id
		
		FROM authorships
		INNER JOIN nicks ON authorships.nick_id = nicks.id
		INNER JOIN releasers ON nicks.releaser_id = releasers.id
		WHERE authorships.production_id = %s
		ORDER BY position
	''', (production_id,) )
	releaser_columns = ('id', 'type', 'pouet_id', 'zxdemo_id', 'name', 'abbreviation', 'website', 'csdb_id', 'country_id', 'slengpung_id')
	nick_columns = ('id', 'name', 'abbreviation')
	
	for row in cur:
		nick_info  = dict(zip(nick_columns, row[1:4]))
		releaser_info = dict(zip(releaser_columns, row[4:14]))
		
		nick_info['name'] = nick_info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		releaser_info['name'] = releaser_info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		yield {
			'id': row[0],
			'nick': nick_info,
			'releaser': releaser_info,
		}

def run_memberships_query(sql, params = ()):
	cur = connection.cursor()
	cur.execute(sql, params)
	releaser_columns = ('id', 'type', 'pouet_id', 'zxdemo_id', 'name', 'abbreviation', 'website', 'csdb_id', 'country_id', 'slengpung_id')
	for row in cur:
		member_info = dict(zip(releaser_columns, row[0:10]))
		member_info['name'] = member_info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		group_info = dict(zip(releaser_columns, row[10:20]))
		group_info['name'] = group_info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		yield {
			'member': member_info,
			'group': group_info,
			'is_current': row[20]
		}

def memberships_with_log_events():
	return run_memberships_query('''
		SELECT DISTINCT
			members.id, members.type, members.pouet_id, members.zxdemo_id, members.name,
			members.abbreviation, members.website, members.csdb_id, members.country_id,
			members.slengpung_id,
			
			groups.id, groups.type, groups.pouet_id, groups.zxdemo_id, groups.name,
			groups.abbreviation, groups.website, groups.csdb_id, groups.country_id,
			groups.slengpung_id,
			
			memberships.is_current
		FROM memberships
			INNER JOIN log_events ON (
				memberships.member_id = log_events.releaser_id
				AND memberships.group_id = log_events.group_id
				AND log_events.event_type IN ('add_member', 'remove_member', 'set_current_member', 'set_former_member')
			)
			INNER JOIN releasers AS members ON (memberships.member_id = members.id)
			INNER JOIN releasers AS groups ON (memberships.group_id = groups.id)
	''')

def memberships_from_zxdemo():
	return run_memberships_query('''
		SELECT DISTINCT
			members.id, members.type, members.pouet_id, members.zxdemo_id, members.name,
			members.abbreviation, members.website, members.csdb_id, members.country_id,
			members.slengpung_id,
			
			groups.id, groups.type, groups.pouet_id, groups.zxdemo_id, groups.name,
			groups.abbreviation, groups.website, groups.csdb_id, groups.country_id,
			groups.slengpung_id,
			
			memberships.is_current
		FROM memberships
			INNER JOIN releasers AS members ON (memberships.member_id = members.id AND members.zxdemo_id IS NOT NULL)
			INNER JOIN releasers AS groups ON (memberships.group_id = groups.id AND groups.zxdemo_id IS NOT NULL)
	''')

def subgroupages():
	return run_memberships_query('''
		SELECT DISTINCT
			members.id, members.type, members.pouet_id, members.zxdemo_id, members.name,
			members.abbreviation, members.website, members.csdb_id, members.country_id,
			members.slengpung_id,
			
			groups.id, groups.type, groups.pouet_id, groups.zxdemo_id, groups.name,
			groups.abbreviation, groups.website, groups.csdb_id, groups.country_id,
			groups.slengpung_id,
			
			subgroupages.is_current
		FROM subgroupages
			INNER JOIN releasers AS members ON (subgroupages.subgroup_id = members.id)
			INNER JOIN releasers AS groups ON (subgroupages.group_id = groups.id)
	''')

def credits():
	cur = connection.cursor()
	cur.execute('''
		SELECT
			credits.id, credits.role,
			
			productions.id, productions.name, productions.pouet_id, productions.zxdemo_id,
			productions.release_date_datestamp, productions.release_date_precision,
			productions.scene_org_id, productions.csdb_id,
			
			nicks.id, nicks.name, nicks.abbreviation,
			
			releasers.id, releasers.type, releasers.pouet_id, releasers.zxdemo_id, releasers.name,
			releasers.abbreviation, releasers.website, releasers.csdb_id, releasers.country_id,
			releasers.slengpung_id
		FROM credits
			INNER JOIN productions ON (credits.production_id = productions.id)
			INNER JOIN nicks ON (credits.nick_id = nicks.id)
			INNER JOIN releasers ON (nicks.releaser_id = releasers.id)
	''')
	production_columns = ('id', 'name', 'pouet_id', 'zxdemo_id', 'release_date_datestamp', 'release_date_precision', 'scene_org_id', 'csdb_id')
	releaser_columns = ('id', 'type', 'pouet_id', 'zxdemo_id', 'name', 'abbreviation', 'website', 'csdb_id', 'country_id', 'slengpung_id')
	nick_columns = ('id', 'name', 'abbreviation')
	
	for row in cur:
		prod_info = dict(zip(production_columns, row[2:10]))
		nick_info  = dict(zip(nick_columns, row[10:13]))
		releaser_info = dict(zip(releaser_columns, row[13:23]))
		
		prod_info['name'] = prod_info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		nick_info['name'] = nick_info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		releaser_info['name'] = releaser_info['name'].encode('latin-1').decode('utf-8') # hack to fix encoding
		yield {
			'id': row[0],
			'role': row[1],
			'production': prod_info,
			'nick': nick_info,
			'releaser': releaser_info,
		}
