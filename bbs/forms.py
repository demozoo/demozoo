from form_with_location import ModelFormWithLocation

from bbs.models import BBS
from demoscene.models import Edit


class BBSForm(ModelFormWithLocation):
    def log_creation(self, user):
        Edit.objects.create(action_type='create_bbs', focus=self.instance,
            description=(u"Added BBS '%s'" % self.instance.name), user=user)

    @property
    def changed_data_description(self):
        descriptions = []
        changed_fields = self.changed_data
        if 'name' in changed_fields:
            descriptions.append(u"name to '%s'" % self.cleaned_data['name'])
        if 'location' in changed_fields:
            descriptions.append(u"location to %s" % self.cleaned_data['location'])
        if descriptions:
            return u"Set %s" % (u", ".join(descriptions))

    def log_edit(self, user):
        description = self.changed_data_description
        if description:
            Edit.objects.create(action_type='edit_bbs', focus=self.instance,
                description=description, user=user)

    class Meta:
        model = BBS
        fields = ('name', 'location')
