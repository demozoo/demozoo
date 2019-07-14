from celery.task import task

from demoscene.models import Releaser, ReleaserExternalLink
from janeway.matching import automatch_productions


@task(ignore_result=True)
def automatch_all_authors():
	for releaser_id in ReleaserExternalLink.objects.filter(link_class='KestraBitworldAuthor').distinct().values_list('releaser_id', flat=True):
		automatch_author.delay(releaser_id)


@task(ignore_result=True)
def automatch_author(releaser_id):
	automatch_productions(Releaser.objects.get(id=releaser_id))
