# Update Bitworld links to their new Kestra versions
from django.core.management.base import NoArgsCommand
from django.db.utils import IntegrityError
from productions.models import ProductionLink
from parties.models import PartyExternalLink
from django.db import transaction
import httplib
from time import sleep

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        for link in PartyExternalLink.objects.filter(link_class='BitworldParty'):
            conn = httplib.HTTPConnection("bitworld.bitfellas.org")
            conn.request("GET", "/party.php?id=%s" % link.parameter)
            response = conn.getresponse()
            if response.status == 301:
                new_link = PartyExternalLink(party_id=link.party_id)
                new_link.url = response.getheader('Location')
                try:
                    sid = transaction.savepoint()
                    new_link.save()
                    transaction.savepoint_commit(sid)
                    print "added url %s for party id %d" % (new_link.url, new_link.party_id)
                except IntegrityError:
                    # this link duplicates an existing one - we just didn't recognise it
                    # until now due to different link formats. Fair game to delete it
                    transaction.savepoint_rollback(sid)
                    print "%s already exists - skipping" % (new_link.url)

            else:
                print "Unexpected response status code %d - skipping" % response.status
            conn.close()
            sleep(1)

        for link in ProductionLink.objects.filter(link_class='BitworldDemo'):
            conn = httplib.HTTPConnection("bitworld.bitfellas.org")
            conn.request("GET", "/demo.php?id=%s" % link.parameter)
            response = conn.getresponse()
            if response.status == 301:
                new_link = ProductionLink(production_id=link.production_id)
                new_link.url = response.getheader('Location')
                try:
                    sid = transaction.savepoint()
                    new_link.save()
                    transaction.savepoint_commit(sid)
                    print "added url %s for prod id %d" % (new_link.url, new_link.production_id)
                except IntegrityError:
                    # this link duplicates an existing one - we just didn't recognise it
                    # until now due to different link formats. Fair game to delete it
                    transaction.savepoint_rollback(sid)
                    print "%s already exists - skipping" % (new_link.url)

            else:
                print "Unexpected response status code %d - skipping" % response.status
            conn.close()
            sleep(1)
