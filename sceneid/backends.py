from demoscene.models import SceneID
from django.contrib.auth.models import User

class SceneIDBackend(object):
	# expect in a sceneID, either return a corresponding user or None
	def authenticate(self, sceneid=None):
		if (sceneid is None):
			return None
		try:
			row = SceneID.objects.extra(where=['sceneid = %s'],params=[sceneid])
			if (len(row) == 0):
				return None # nothing found, we couldn't authenticate
			user = User.objects.get(id=row[0].user.id)
		except User.DoesNotExist:
			raise Exception("Internal error, sceneid is linked but user doesn't exist?");
		return user

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None