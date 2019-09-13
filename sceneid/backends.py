from django.contrib.auth.models import User


class SceneIDBackend(object):
    # expect in a sceneID, either return a corresponding user or None
    def authenticate(self, sceneid=None):
        if sceneid is None:
            return None

        try:
            return User.objects.get(sceneid__sceneid=sceneid, is_active=True)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None
