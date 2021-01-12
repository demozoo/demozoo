from form_with_location import ModelFormWithLocation

from bbs.models import BBS
from demoscene.models import Edit


class BBSForm(ModelFormWithLocation):
    def log_creation(self, user):
        Edit.objects.create(action_type='create_bbs', focus=self.instance,
            description=(u"Added BBS '%s'" % self.instance.name), user=user)

    class Meta:
        model = BBS
        fields = ('name', 'location')
