from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User

from demoscene.shortcuts import get_page


def show(request, user_id):
	user = get_object_or_404(User, id=user_id)

	edits = user.edits.order_by('-timestamp').select_related('user', 'focus', 'focus2')
	if not request.user.is_staff:
		edits = edits.filter(admin_only=False)
	edits_page = get_page(
		edits,
		request.GET.get('page', '1'))

	return render(request, 'users/show.html', {
		'user': user,
		'edits_page': edits_page,
	})
