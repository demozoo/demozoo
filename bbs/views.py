from django.db.models.functions import Lower
from django.shortcuts import render

from bbs.models import BBS
from demoscene.shortcuts import get_page


def index(request):
    page = get_page(
        BBS.objects.order_by(Lower('name')),
        request.GET.get('page', '1')
    )

    return render(request, 'bbs/index.html', {
        'page': page,
    })
