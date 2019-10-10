from itertools import groupby

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count

from taggit.models import Tag

from demoscene.models import Releaser, Nick, NickVariant
from parties.models import Competition, ResultsFile
from productions.models import PackMember, Production, ProductionType, SoundtrackLink
# from sceneorg.models import Directory


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print "Looking for releasers without their name as a Nick"

        releasers = Releaser.objects.raw('''
            SELECT demoscene_releaser.*
            FROM
                demoscene_releaser
                LEFT JOIN demoscene_nick ON (
                    demoscene_releaser.id = demoscene_nick.releaser_id
                    AND demoscene_releaser.name = demoscene_nick.name
                )
            WHERE
                demoscene_nick.id IS NULL
        ''')
        for releaser in releasers:
            print "creating nick for %s" % releaser
            nick = Nick(releaser=releaser, name=releaser.name)
            nick.save()

        print "Looking for Nicks without their name as a NickVariant"

        nicks = Nick.objects.raw('''
            SELECT demoscene_nick.*
            FROM
                demoscene_nick
                LEFT JOIN demoscene_nickvariant ON (
                    demoscene_nick.id = demoscene_nickvariant.nick_id
                    AND demoscene_nick.name = demoscene_nickvariant.name
                )
            WHERE
                demoscene_nickvariant.id IS NULL
        ''')
        for nick in nicks:
            print "creating nick_variant for %s" % nick
            nick_variant = NickVariant(nick=nick, name=nick.name)
            nick_variant.save()

        print "Removing releaser abbreviations that are the same as the actual name"
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE demoscene_nick
            SET abbreviation = ''
            WHERE LOWER(name) = LOWER(abbreviation)
        ''')

        print "Looking for Nicks without their abbreviation as a NickVariant"

        nicks = Nick.objects.raw('''
            SELECT demoscene_nick.*
            FROM
                demoscene_nick
                LEFT JOIN demoscene_nickvariant ON (
                    demoscene_nick.id = demoscene_nickvariant.nick_id
                    AND demoscene_nick.abbreviation = demoscene_nickvariant.name
                )
            WHERE
                demoscene_nick.abbreviation <> ''
                AND demoscene_nickvariant.id IS NULL
        ''')
        for nick in nicks:
            print "creating nick_variant for %s" % nick.abbreviation
            nick_variant = NickVariant(nick=nick, name=nick.abbreviation)
            nick_variant.save()

        print "Truncating fuzzy dates to first of the month / first of January"
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE productions_production
            SET release_date_date = date_trunc('month', release_date_date)
            WHERE release_date_precision = 'm'
        ''')
        cursor.execute('''
            UPDATE productions_production
            SET release_date_date = date_trunc('year', release_date_date)
            WHERE release_date_precision = 'y'
        ''')

        print "Removing abbreviations on scener nicks"
        nicks = Nick.objects.exclude(abbreviation='').filter(releaser__is_group=False)
        for nick in nicks:
            print "Removing abbreviation %s of %s" % (nick.abbreviation, nick.name)
            nick.abbreviation = ''
            nick.save()

        print "Stripping leading / trailing spaces from names and titles"
        cursor.execute('''
            UPDATE productions_production
            SET title = REGEXP_REPLACE(title, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
            WHERE title LIKE ' %%' OR title LIKE '%% '
        ''')
        cursor.execute('''
            UPDATE demoscene_releaser
            SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
            WHERE name LIKE ' %%' OR name LIKE '%% '
        ''')
        cursor.execute('''
            UPDATE demoscene_nick
            SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
            WHERE name LIKE ' %%' OR name LIKE '%% '
        ''')
        cursor.execute('''
            UPDATE demoscene_nickvariant
            SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
            WHERE name LIKE ' %%' OR name LIKE '%% '
        ''')
        cursor.execute('''
            UPDATE parties_party
            SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
            WHERE name LIKE ' %%' OR name LIKE '%% '
        ''')
        cursor.execute('''
            UPDATE parties_partyseries
            SET name = REGEXP_REPLACE(name, E'^\\\\s*(.*?)\\\\s*$', E'\\\\1', 'g')
            WHERE name LIKE ' %%' OR name LIKE '%% '
        ''')

        # skip this. it takes ages.
        # print "Recursively marking children of deleted scene.org dirs as deleted"
        # for dir in Directory.objects.filter(is_deleted=True):
        #    dir.mark_deleted()

        print "Converting invitation competitions to party invitation relations"
        invitation_compos = Competition.objects.filter(name__istartswith='invitation').select_related('party')
        for compo in invitation_compos:
            placings = compo.placings.select_related('production')

            is_real_compo = False
            for placing in placings:
                if placing.ranking != '' or placing.score != '':
                    is_real_compo = True
                compo.party.invitations.add(placing.production)

            if not is_real_compo:
                compo.delete()

        print "Checking encodings on results files"
        results_files = ResultsFile.objects.all()
        for results_file in results_files:
            try:
                results_file.text
            except UnicodeDecodeError:
                print "Error on /parties/%d/results_file/%d/ - cannot decode as %r" % (results_file.party_id, results_file.id, results_file.encoding)
            except IOError:
                pass  # ignore files that aren't on disk (which probably means this is a local dev instance with a live db)

        print "Deleting unused tags"
        Tag.objects.annotate(num_prods=Count('taggit_taggeditem_items')).filter(num_prods=0).delete()

        # print "Setting has_screenshots flag on productions"
        # cursor.execute('''
        #     UPDATE productions_production SET has_screenshot = (
        #         id IN (
        #             SELECT DISTINCT production_id
        #             FROM productions_screenshot
        #             WHERE thumbnail_url <> ''
        #         )
        #     )
        # ''')

        print "Closing gaps in pack member sequences"
        for k, pms in groupby(PackMember.objects.order_by('pack_id', 'position'), lambda pm: pm.pack_id):
            for i, pm in enumerate(pms):
                if i + 1 != pm.position:
                    pm.position = i + 1
                    pm.save()

        print "Closing gaps in soundtrack sequences"
        for k, stls in groupby(SoundtrackLink.objects.order_by('production_id', 'position'), lambda stl: stl.production_id):
            for i, stl in enumerate(stls):
                if i + 1 != stl.position:
                    stl.position = i + 1
                    stl.save()

        print "Marking diskmags with pack contents as packs"
        diskmag_id = ProductionType.objects.get(name='Diskmag').id
        artpack_id = ProductionType.objects.get(internal_name='artpack').id
        pack = ProductionType.objects.get(internal_name='pack')
        for prod in Production.objects.raw('''
            SELECT distinct pack_id AS id
            FROM productions_packmember
            INNER JOIN productions_production AS packmember ON (member_id = packmember.id)
            WHERE
            pack_id NOT IN (select production_id from productions_production_types where productiontype_id in (%(pack)s, %(artpack)s))
            AND pack_id IN (select production_id from productions_production_types where productiontype_id = %(diskmag)s)
            AND packmember.supertype <> 'music'
        ''', {'pack': pack.id, 'artpack': artpack_id, 'diskmag': diskmag_id}):
            prod.types.add(pack)

        print "Reassigning musicdisk contents from pack contents to soundtrack links"
        musicdisk_id = ProductionType.objects.get(name='Musicdisk').id
        pack_contents = PackMember.objects.filter(pack__types=musicdisk_id, member__supertype='music').order_by('pack_id', 'position')
        for pack_id, pack_members in groupby(pack_contents, lambda pm: pm.pack_id):
            soundtrack_ids = list(
                SoundtrackLink.objects.filter(production_id=pack_id).order_by('position').values_list('soundtrack_id', flat=True)
            )
            for pack_member in pack_members:
                if pack_member.member_id not in soundtrack_ids:
                    SoundtrackLink.objects.create(
                        production_id=pack_id, soundtrack_id=pack_member.member_id,
                        position=len(soundtrack_ids) + 1, data_source=pack_member.data_source
                    )
                    soundtrack_ids.append(pack_member.member_id)
                pack_member.delete()

        print "done."
