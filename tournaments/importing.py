from datetime import datetime
import re

from demoscene.models import Nick, Releaser
from parties.models import Party
from tournaments.models import Tournament


PARTY_SERIES_ALIASES = {
    'assembly summer': 'assembly',
    'assembly autumn': 'assembly',
    'tokyo demo fest': 'tokyodemofest',
    'chaos constructions winter': 'chaos constructions',
    'deadline': 'deadline (.de)',
    'omzg': 'molvania zscene gathering',
    'hogmanay party': 'hogmanay.party',
}


def find_party_from_tournament_data(tournament_data):
    start_date = datetime.fromisoformat(tournament_data['started'])

    # get a list of party series names to try (case-insensitively),
    # starting with the actual name given
    original_name = tournament_data['title'].lower()
    series_names = [original_name]

    # strip off typical 'noise' words, 'party' and 'online'
    if original_name.endswith(' party') or original_name.endswith(' online'):
        series_names.append(re.sub(r' (online|party)$', '', original_name))

    # look for aliases in PARTY_SERIES_ALIASES
    for name in series_names:
        try:
            series_names.append(PARTY_SERIES_ALIASES[name])
        except KeyError:
            pass

    for series_name in series_names:
        try:
            return Party.objects.get(
                party_series__name__iexact=series_name,
                start_date_date=start_date
            )
        except Party.DoesNotExist:
            pass

    return None


def find_nick_from_handle_data(handle_data):
    if handle_data['demozoo_id'] is None:
        return (None, handle_data['name'])

    try:
        nick = Nick.objects.get(
            releaser_id=handle_data['demozoo_id'],
            variants__name__iexact = handle_data['name']
        )
    except Nick.DoesNotExist:
        print(
            "\tCannot find nick '%s' for releaser %d (%s)" % (
                handle_data['name'], handle_data['demozoo_id'],
                Releaser.objects.get(id=handle_data['demozoo_id']).name
            )
        )
        return (None, handle_data['name'])

    return (nick.id, '')


def import_tournament(filename, tournament_data):
    try:
        tournament = Tournament.objects.get(source_file_name=filename)
        created = False
    except Tournament.DoesNotExist:
        party = find_party_from_tournament_data(tournament_data)
        if not party:
            print(
                "\tNo match for party: %s %s" % (
                    tournament_data['title'], tournament_data['started']
                )
            )
            return

        tournament, created = Tournament.objects.get_or_create(
            party=party, name=tournament_data['type'],
            defaults={'source_file_name': filename}
        )

        if not created:
            print(
                "\tMismatched source filename! Previously %s, now %s" % (
                    tournament.source_file_name, filename
                )
            )
            return

    phases_data = tournament_data['phases']

    if created:
        print("\tCreated tournament: %s" % tournament)
        create_phases = True
    else:
        # print("\tFound tournament: %s" % tournament)
        expected_party = find_party_from_tournament_data(tournament_data)
        if tournament.party != expected_party:
            print(
                "\tParty mismatch! Found %s, but data looks like %s" % (
                    tournament.party, expected_party
                )
            )

        if tournament.name != tournament_data['type']:
            print(
                "\tChanged name from %s to %s" % (
                    tournament.name, tournament_data['type']
                )
            )
            tournament.name = tournament_data['type']
            tournament.save()

        # if there are any discrepancies in phase counts or titles,
        # delete and reimport them
        phases = list(tournament.phases.all())
        if len(phases) != len(phases_data):
            create_phases = True
        elif any(
            phase.name != (phases_data[i]['title'] or '')
            or phase.position != i
            for i, phase in enumerate(phases)
        ):
            create_phases = True
        else:
            create_phases = False

        if create_phases:
            print("\tPhases don't match - recreating")
            tournament.phases.all().delete()

    if create_phases:
        for position, phase_data in enumerate(phases_data):
            phase = tournament.phases.create(
                name=phase_data['title'] or '', position=position
            )

            load_phase_data(phase, phase_data)

    else:
        # phases for this tournament are already defined and confirmed to match the
        # names in the file, and have consecutive 0-based positions
        for phase in phases:
            load_phase_data(phase, phases_data[phase.position])


def load_phase_data(phase, phase_data):
    entries = list(phase.entries.all())
    entries_data = phase_data['entries']

    # if length of entries list doesn't match, or positions are inconsistent,
    # recreate
    create_entries = (
        len(entries) != len(entries_data)
        or any(entry.position != i for i, entry in enumerate(entries))
    )

    if create_entries:
        phase.entries.all().delete()
        for position, entry_data in enumerate(entries_data):
            nick_id, name = find_nick_from_handle_data(entry_data['handle'])

            phase.entries.create(
                position=position,
                nick_id=nick_id,
                name=name,
                ranking=entry_data['rank'] or '',
                score=entry_data['points'] or '',
            )

    else:
        for i, entry_data in enumerate(entries_data):
            entry = entries[i]
            has_changed = False

            nick_id, name = find_nick_from_handle_data(entry_data['handle'])
            if nick_id != entry.nick_id or name != entry.name:
                entry.nick_id = nick_id
                entry.name = name
                has_changed = True

            rank = '' if entry_data['rank'] is None else str(entry_data['rank'])
            if rank != entry.ranking:
                entry.ranking = rank
                has_changed = True

            score = '' if entry_data['points'] is None else str(entry_data['points'])
            if score != entry.score:
                entry.score = score
                has_changed = True

            if has_changed:
                print("\tupdating entry %s" % entry)
                entry.save()
