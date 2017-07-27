from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class ActiveModelBackend(ModelBackend):
	"""
	Customisation of ModelBackend to reject users with is_active=False.
	Can be dropped on Django >=1.10, where ModelBackend checks is_active.
	"""
	def get_user(self, user_id):
		UserModel = get_user_model()
		try:
			return UserModel._default_manager.get(pk=user_id, is_active=True)
		except UserModel.DoesNotExist:
			return None


def is_ip_banned(request):
	return (request.META['REMOTE_ADDR'] in ['81.234.236.23', '81.230.148.230'])
