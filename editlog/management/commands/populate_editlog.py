from demoscene.models import Edit as OldEdit, Production, Releaser
from parties.models import Party
from editlog.models import Edit, EditedItem

from django.core.management.base import NoArgsCommand
from django.contrib.contenttypes.models import ContentType


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		production_content_type_id = ContentType.objects.get_for_model(Production).id
		releaser_content_type_id = ContentType.objects.get_for_model(Releaser).id
		party_content_type_id = ContentType.objects.get_for_model(Party).id

		for old_edit in OldEdit.objects.all():
			if old_edit.action_type == 'production_edit_external_links':
				edit = Edit.objects.create(
					action_type='production_edit_external_links',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
					detail=old_edit.description
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'production_edit_download_links':
				edit = Edit.objects.create(
					action_type='production_edit_download_links',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
					detail=old_edit.description
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'releaser_edit_external_links':
				edit = Edit.objects.create(
					action_type='releaser_edit_external_links',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
					detail=old_edit.description
				)

				item = old_edit.focus
				if item:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='group' if item.is_group else 'scener', name=item.name)
				else:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='releaser', name='(deleted)')

			elif old_edit.action_type == 'party_edit_external_links':
				edit = Edit.objects.create(
					action_type='party_edit_external_links',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
					detail=old_edit.description
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=party_content_type_id, role='party', name=item.name if item else '(deleted)')

			elif old_edit.action_type == 'edit_production_core_details':
				edit = Edit.objects.create(
					action_type='edit_production_core_details',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
					detail=old_edit.description
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'create_production':
				edit = Edit.objects.create(
					action_type='create_production',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'edit_production_notes':
				edit = Edit.objects.create(
					action_type='edit_production_notes',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'create_group':
				edit = Edit.objects.create(
					action_type='create_group',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='group', name=item.name if item else '(deleted)')

			elif old_edit.action_type == 'create_scener':
				edit = Edit.objects.create(
					action_type='create_scener',
					user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='scener', name=item.name if item else '(deleted)')

