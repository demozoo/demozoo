from datetime import datetime

from parties.models import Party
from tournaments.models import Tournament


def find_party_from_tournament_data(tournament_data):
    start_date = datetime.fromisoformat(tournament_data['started'])

    try:
        return Party.objects.get(
            party_series__name=tournament_data['title'],
            start_date_date=start_date
        )
    except Party.DoesNotExist:
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
        print("\tFound tournament: %s" % tournament)
        expected_party = find_party_from_tournament_data(tournament_data)
        if tournament.party != expected_party:
            print(
                "\tParty mismatch! Found %s, but data looks like %s" % (
                    tournament.party, expected_party
                )
            )
