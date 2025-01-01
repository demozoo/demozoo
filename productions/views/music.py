from productions.forms import CreateMusicForm, MusicIndexFilterForm
from productions.views.generic import CreateView, HistoryView, IndexView, ShowView


class MusicIndexView(IndexView):
    supertype = "music"
    template = "music/index.html"
    filter_form_class = MusicIndexFilterForm
    url_name = "musics"


class MusicShowView(ShowView):
    supertype = "music"


class MusicHistoryView(HistoryView):
    supertype = "music"


class CreateMusicView(CreateView):
    form_class = CreateMusicForm
    template = "music/create.html"
    title = "New music"
    action_url_name = "new_music"
    submit_button_label = "Add new music"
