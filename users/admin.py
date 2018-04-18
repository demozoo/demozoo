from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class UndeletableUserAdmin(UserAdmin):
	# Customise the admin for django.contrib.auth.user to never provide the delete button.
	# Instead of deleting, users should be disabled by setting the 'active' flag to false.
	def has_delete_permission(self, request, obj=None):
		return False


admin.site.unregister(User)
admin.site.register(User, UndeletableUserAdmin)
