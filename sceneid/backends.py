from demoscene.models import SceneID
from django.contrib.auth.models import User

class SceneIDBackend(object):
  # expect in a sceneID, either return a corresponding user or None
	def authenticate(self, sceneid=None):
		if (sceneid is None):
			return None
		try:
			row = SceneID.objects.extra(where=['sceneid = %s'],params=[sceneid])[0]
			if (row is None):
				return HttpResponse("user not found") # todo proper exception
			user = User.objects.get(id=row.user.id)
		except User.DoesNotExist:
			pass
		return user        

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None