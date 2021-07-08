from datetime import datetime
import re

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

    if created:
        print("\tCreated tournament: %s" % tournament)
    else:
        # print("\tFound tournament: %s" % tournament)
        expected_party = find_party_from_tournament_data(tournament_data)
        if tournament.party != expected_party:
            print(
                "\tParty mismatch! Found %s, but data looks like %s" % (
                    tournament.party, expected_party
                )
            )
