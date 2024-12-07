from unittest.mock import patch

from django.test import TestCase

from demoscene.models import Releaser
from janeway.tasks import automatch_all_authors, automatch_author, import_screenshot
from platforms.models import Platform
from productions.models import Production


class TestTasks(TestCase):
    fixtures = ["tests/janeway.json"]

    @patch("janeway.tasks.automatch_author")
    def test_automatch_all_authors(self, automatch_author):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        spb.external_links.create(link_class="KestraBitworldAuthor", parameter="123")

        automatch_all_authors()
        self.assertEqual(automatch_author.delay.call_count, 1)
        (releaser_id,) = automatch_author.delay.call_args.args
        self.assertEqual(releaser_id, spb.id)

    def test_automatch_author(self):
        spb = Releaser.objects.create(name="Spaceballs", is_group=True)
        spb.external_links.create(link_class="KestraBitworldAuthor", parameter="123")
        sota = Production.objects.create(title="State Of The Art", supertype="production")
        sota.platforms.add(Platform.objects.get(name="Amiga OCS/ECS"))
        sota.author_nicks.add(spb.primary_nick)

        automatch_author(spb.id)
        self.assertTrue(
            sota.links.filter(link_class="KestraBitworldRelease", parameter="345", source="janeway-automatch").exists()
        )

    @patch("screenshots.tasks.upload_to_s3")
    def test_import_screenshot(self, upload_to_s3):
        sota = Production.objects.create(title="State Of The Art", supertype="production")
        upload_to_s3.return_value = "http://media.demozoo.org/screens/sota.png"
        import_screenshot(sota.id, 111, "http://kestra.exotica.org.uk/files/screenies/28000/154a.png", "a")
        self.assertEqual(upload_to_s3.call_count, 3)
        self.assertEqual(sota.screenshots.count(), 1)
