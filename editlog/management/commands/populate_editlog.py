import re

from demoscene.models import Edit as OldEdit, Production, Releaser
from parties.models import Party
from editlog.models import Edit, EditedItem

from django.core.management.base import NoArgsCommand
from django.contrib.contenttypes.models import ContentType


def import_edit(old_edit, detail=''):
	return Edit.objects.create(
		action_type=old_edit.action_type,
		user_id=old_edit.user_id, timestamp=old_edit.timestamp, admin_only=False,
		detail=detail
	)


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		production_content_type_id = ContentType.objects.get_for_model(Production).id
		releaser_content_type_id = ContentType.objects.get_for_model(Releaser).id
		party_content_type_id = ContentType.objects.get_for_model(Party).id

		for old_edit in OldEdit.objects.all():
			if old_edit.action_type in ('production_edit_external_links', 'production_edit_download_links'):
				edit = import_edit(old_edit, old_edit.description)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'releaser_edit_external_links':
				edit = import_edit(old_edit, old_edit.description)

				item = old_edit.focus
				if item:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='group' if item.is_group else 'scener', name=item.name)
				else:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='releaser', name='(deleted)')

			elif old_edit.action_type == 'party_edit_external_links':
				edit = import_edit(old_edit, old_edit.description)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=party_content_type_id, role='party', name=item.name if item else '(deleted)')

			elif old_edit.action_type == 'edit_production_core_details':
				edit = import_edit(old_edit, old_edit.description)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'create_production':
				edit = import_edit(old_edit)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'edit_production_notes':
				edit = import_edit(old_edit)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=production_content_type_id, role='production', name=item.title if item else '(deleted)')

			elif old_edit.action_type == 'create_group':
				edit = import_edit(old_edit)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='group', name=item.name if item else '(deleted)')

			elif old_edit.action_type == 'create_scener':
				edit = import_edit(old_edit)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='scener', name=item.name if item else '(deleted)')

			elif old_edit.action_type == 'edit_scener_location':
				match = re.match(r'Set location to (.*)', old_edit.description)
				if match:
					location = match.group(1)
				else:
					location = ''

				edit = import_edit(old_edit, location)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='scener', name=item.name if item else '(deleted)')

			elif old_edit.action_type == 'edit_scener_real_name':
				edit = import_edit(old_edit,
					('set_real_name' if old_edit.description == "Set real name" else '')
				)
				item = old_edit.focus
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='scener', name=item.name if item else '(deleted)')

			elif old_edit.action_type == 'edit_releaser_notes':
				edit = import_edit(old_edit)

				item = old_edit.focus
				if item:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='group' if item.is_group else 'scener', name=item.name)
				else:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='releaser', name='(deleted)')

			elif old_edit.action_type == 'add_nick':
				match = re.match(r'Added nick \'(.*)\'$', old_edit.description)
				if match:
					nick = match.group(1)
				else:
					nick = ''

				edit = import_edit(old_edit, nick)
				item = old_edit.focus
				if item:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='group' if item.is_group else 'scener', name=item.name)
				else:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='releaser', name='(deleted)')

			elif old_edit.action_type == 'edit_nick':
				match = re.match(r'Edited nick (\'.*\': .*)$', old_edit.description)
				if match:
					detail = match.group(1)
				else:
					detail = ''

				edit = import_edit(old_edit, detail)
				item = old_edit.focus
				if item:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='group' if item.is_group else 'scener', name=item.name)
				else:
					EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
						item_content_type_id=releaser_content_type_id, role='releaser', name='(deleted)')

			elif old_edit.action_type == 'edit_membership':
				match = re.match(r'Updated (.*)\'s membership of (.*): (.*)$', old_edit.description)
				if match:
					member_name = match.group(1)
					group_name = match.group(2)
					detail = match.group(3)
				else:
					member = old_edit.focus
					group = old_edit.focus2
					member_name = member.name if member else '(deleted)'
					group_name = group.name if group else '(deleted)'
					detail = ''

				edit = import_edit(old_edit, detail)
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='member', name=member_name)
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='group', name=group_name)

			elif old_edit.action_type == 'edit_subgroup':
				match = re.match(r'Updated (.*)\'s status as a subgroup of (.*): (.*)$', old_edit.description)
				if match:
					subgroup_name = match.group(1)
					supergroup_name = match.group(2)
					detail = match.group(3)
				else:
					subgroup = old_edit.focus
					supergroup = old_edit.focus2
					subgroup_name = subgroup.name if subgroup else '(deleted)'
					supergroup_name = supergroup.name if supergroup else '(deleted)'
					detail = ''

				edit = import_edit(old_edit, detail)
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='subgroup', name=subgroup_name)
				EditedItem.objects.create(edit=edit, item_id=old_edit.focus_object_id,
					item_content_type_id=releaser_content_type_id, role='supergroup', name=supergroup_name)

