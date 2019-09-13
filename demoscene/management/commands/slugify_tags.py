from django.core.management.base import NoArgsCommand

from taggit.models import Tag, TaggedItem

from demoscene.utils.text import slugify_tag

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        for tag in Tag.objects.all():
            new_name = slugify_tag(tag.name)
            try:
                existing_tag = Tag.objects.exclude(id=tag.id).get(name=new_name)
                # if tag with that name already exists, move all tagged items to existing_tag
                # and delete this tag
                TaggedItem.objects.filter(tag=tag).update(tag=existing_tag)
                tag.delete()
            except Tag.DoesNotExist:
                # keep this tag, just rewrite the name
                tag.name = new_name
                tag.save()
