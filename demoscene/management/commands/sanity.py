from __future__ import absolute_import, unicode_literals

from itertools import groupby

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from taggit.models import Tag

from demoscene.models import Nick, NickVariant, Releaser
from parties.models import Competition, ResultsFile
from productions.models import PackMember, Production, ProductionType, SoundtrackLink

# from sceneorg.models import Directory


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.verbosity = kwargs['verbosity']

        if self.verbosity >= 1:
            print("Looking for releasers without their name as a Nick")

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
            if self.verbosity >= 1:
                print("creating nick for %s" % releaser)
            nick = Nick(releaser=releaser, name=releaser.name)
            nick.save()

        if self.verbosity >= 1:
            print("Looking for Nicks without their name as a NickVariant")

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
            if self.verbosity >= 1:
                print("creating nick_variant for %s" % nick)
            nick_variant = NickVariant(nick=nick, name=nick.name)
            nick_variant.save()

        if self.verbosity >= 1:
            print("Removing releaser abbreviations that are the same as the actual name")
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE demoscene_nick
            SET abbreviation = ''
            WHERE LOWER(name) = LOWER(abbreviation)
        ''')

        if self.verbosity >= 1:
            print("Looking for Nicks without their abbreviation as a NickVariant")

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
            if self.verbosity >= 1:
                print("creating nick_variant for %s" % nick.abbreviation)
            nick_variant = NickVariant(nick=nick, name=nick.abbreviation)
            nick_variant.save()

        if self.verbosity >= 1:
            print("Truncating fuzzy dates to first of the month / first of January")
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE productions_production
            SET release_date_date = date_trunc('month', release_date_date)
            WHERE
                release_date_precision = 'm'
                AND date_part('day', release_date_date) <> 1
        ''')
        cursor.execute('''
            UPDATE productions_production
            SET release_date_date = date_trunc('year', release_date_date)
            WHERE
                release_date_precision = 'y'
                AND (date_part('day', release_date_date) <> 1 or date_part('month', release_date_date) <> 1)
        ''')

        if self.verbosity >= 1:
            print("Removing abbreviations on scener nicks")
        nicks = Nick.objects.exclude(abbreviation='').filter(releaser__is_group=False)
        for nick in nicks:
            if self.verbosity >= 1:
                print("Removing abbreviation %s of %s" % (nick.abbreviation, nick.name))
            nick.abbreviation = ''
            nick.save()

        if self.verbosity >= 1:
            print("Stripping leading / trailing spaces from names and titles")
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
        # print("Recursively marking children of deleted scene.org dirs as deleted")
        # for dir in Directory.objects.filter(is_deleted=True):
        #    dir.mark_deleted()

        if self.verbosity >= 1:
            print("Converting invitation competitions to party invitation relations")
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

        if self.verbosity >= 1:
            print("Checking encodings on results files")
        results_files = ResultsFile.objects.all()
        for results_file in results_files:
            try:
                results_file.text
            except UnicodeDecodeError:
                if self.verbosity >= 1:
                    print(
                        "Error on /parties/%d/results_file/%d/ - cannot decode as %r"
                        % (results_file.party_id, results_file.id, results_file.encoding)
                    )
            except IOError:
                # ignore files that aren't on disk (which probably means this is a local dev instance with a live db)
                pass

        if self.verbosity >= 1:
            print("Deleting unused tags")
        Tag.objects.annotate(num_prods=Count('taggit_taggeditem_items')).filter(num_prods=0).delete()

        print("Fixing has_screenshots flag on productions that claim not to have screenshots but do")
        cursor.execute('''
            UPDATE productions_production SET has_screenshot = 't'
            WHERE productions_production.id IN (
                SELECT productions_production.id
                FROM productions_production
                INNER JOIN productions_screenshot on (
                    productions_production.id = productions_screenshot.production_id
                    and thumbnail_url <> ''
                )
                WHERE has_screenshot = 'f'
            )
        ''')
        print("Fixing has_screenshots flag on productions that claim to have screenshots but don't")
        cursor.execute('''
            UPDATE productions_production SET has_screenshot = 'f'
            WHERE productions_production.id IN (
                SELECT productions_production.id
                FROM productions_production
                LEFT JOIN productions_screenshot on (
                    productions_production.id = productions_screenshot.production_id
                    and thumbnail_url <> ''
                )
                WHERE productions_screenshot.production_id is null and has_screenshot = 't'
            )
        ''')

        if self.verbosity >= 1:
            print("Deleting duplicate soundtrack links")
        cursor.execute('''
            select p1.production_id, p1.soundtrack_id, min(p1.position) AS position
            from productions_soundtracklink as p1
            inner join productions_soundtracklink as p2 on (
                p1.production_id = p2.production_id and p1.soundtrack_id = p2.soundtrack_id
                and p1.id <> p2.id
            )
            group by p1.production_id, p1.soundtrack_id
        ''')
        for (prod_id, soundtrack_id, position) in cursor.fetchall():
            SoundtrackLink.objects.filter(
                production_id=prod_id, soundtrack_id=soundtrack_id, position__gt=position
            ).delete()

        if self.verbosity >= 1:
            print("Deleting duplicate pack members")
        cursor.execute('''
            select p1.pack_id, p1.member_id, min(p1.position) AS position
            from productions_packmember as p1
            inner join productions_packmember as p2 on (
                p1.pack_id = p2.pack_id and p1.member_id = p2.member_id
                and p1.id <> p2.id
            )
            group by p1.pack_id, p1.member_id
        ''')
        for (pack_id, member_id, position) in cursor.fetchall():
            PackMember.objects.filter(pack_id=pack_id, member_id=member_id, position__gt=position).delete()

        if self.verbosity >= 1:
            print("Closing gaps in pack member sequences")
        for k, pms in groupby(PackMember.objects.order_by('pack_id', 'position'), lambda pm: pm.pack_id):
            for i, pm in enumerate(pms):
                if i + 1 != pm.position:
                    pm.position = i + 1
                    pm.save()

        if self.verbosity >= 1:
            print("Closing gaps in soundtrack sequences")
        for k, stls in groupby(
            SoundtrackLink.objects.order_by('production_id', 'position'),
            lambda stl: stl.production_id
        ):
            for i, stl in enumerate(stls):
                if i + 1 != stl.position:
                    stl.position = i + 1
                    stl.save()

        if self.verbosity >= 1:
            print("Marking diskmags with pack contents as packs")
        diskmag_id = ProductionType.objects.get(name='Diskmag').id
        artpack_id = ProductionType.objects.get(internal_name='artpack').id
        pack = ProductionType.objects.get(internal_name='pack')
        for prod in Production.objects.raw('''
            SELECT distinct pack_id AS id
            FROM productions_packmember
            INNER JOIN productions_production AS packmember ON (member_id = packmember.id)
            WHERE
            pack_id NOT IN (
                select production_id from productions_production_types
                where productiontype_id in (%(pack)s, %(artpack)s)
            )
            AND pack_id IN (
                select production_id from productions_production_types where productiontype_id = %(diskmag)s
            )
            AND packmember.supertype <> 'music'
        ''', {'pack': pack.id, 'artpack': artpack_id, 'diskmag': diskmag_id}):
            prod.types.add(pack)

        if self.verbosity >= 1:
            print("Reassigning music in pack contents that looks like it should be soundtrack links")
        # get the most common prodtypes that have soundtracks mis-categorised as pack contents
        non_pack_type_ids = ProductionType.objects.filter(
            name__in=['Musicdisk', 'Chip Music Pack', 'Demo', 'Diskmag']
        ).values_list('id', flat=True)
        pack_type_id = ProductionType.objects.get(name='Pack').id
        actual_pack_ids = Production.objects.filter(types__id=pack_type_id).values_list('id', flat=True)
        # get packmembers which are music, inside productions that are one of our target types, but not actual packs
        pack_contents = PackMember.objects.filter(
            pack__types__in=non_pack_type_ids, member__supertype='music'
        ).exclude(
            pack_id__in=actual_pack_ids
        ).order_by('pack_id', 'position')
        for pack_id, pack_members in groupby(pack_contents, lambda pm: pm.pack_id):
            soundtrack_ids = list(
                SoundtrackLink.objects.filter(production_id=pack_id).order_by('position')
                .values_list('soundtrack_id', flat=True)
            )
            for pack_member in pack_members:
                if pack_member.member_id not in soundtrack_ids:
                    SoundtrackLink.objects.create(
                        production_id=pack_id, soundtrack_id=pack_member.member_id,
                        position=len(soundtrack_ids) + 1, data_source=pack_member.data_source
                    )
                    soundtrack_ids.append(pack_member.member_id)
                pack_member.delete()

        if self.verbosity >= 1:
            print("done.")
