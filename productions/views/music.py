from productions.forms import CreateMusicForm, MusicIndexFilterForm
from productions.views.generic import CreateView, HistoryView, IndexView, ShowView


class MusicIndexView(IndexView):
    supertype = "music"
    template = "music/index.html"
    filter_form_class = MusicIndexFilterForm
    url_name = "musics"


class MusicShowView(ShowView):
    supertype = "music"

    def get_context_data(self):
        context = super().get_context_data()

        context["featured_in_productions"] = [
            appearance.production
            for appearance in self.production.appearances_as_soundtrack.prefetch_related(
                "production__author_nicks__releaser", "production__author_affiliation_nicks__releaser"
            ).order_by("production__release_date_date")
        ]
        context["packed_in_productions"] = [
            pack_member.pack
            for pack_member in self.production.packed_in.prefetch_related(
                "pack__author_nicks__releaser", "pack__author_affiliation_nicks__releaser"
            ).order_by("pack__release_date_date")
        ]

        return context


class MusicHistoryView(HistoryView):
    supertype = "music"


class CreateMusicView(CreateView):
    form_class = CreateMusicForm
    template = "music/create.html"
    title = "New music"
    action_url_name = "new_music"
    submit_button_label = "Add new music"
