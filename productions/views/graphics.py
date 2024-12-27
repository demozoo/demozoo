from productions.forms import CreateGraphicsForm, GraphicsIndexFilterForm
from productions.views.generic import CreateView, HistoryView, IndexView, ShowView


class GraphicsIndexView(IndexView):
    supertype = "graphics"
    template = "graphics/index.html"
    filter_form_class = GraphicsIndexFilterForm
    url_name = "graphics"


class GraphicsShowView(ShowView):
    supertype = "graphics"

    def get_context_data(self):
        context = super().get_context_data()

        if self.production.can_have_pack_members():
            context["pack_members"] = [
                link.member
                for link in self.production.pack_members.select_related("member").prefetch_related(
                    "member__author_nicks__releaser", "member__author_affiliation_nicks__releaser"
                )
            ]
        else:
            context["pack_members"] = None

        context["packed_in_productions"] = [
            pack_member.pack
            for pack_member in self.production.packed_in.prefetch_related(
                "pack__author_nicks__releaser", "pack__author_affiliation_nicks__releaser"
            ).order_by("pack__release_date_date")
        ]

        return context


class GraphicsHistoryView(HistoryView):
    supertype = "graphics"


class CreateGraphicsView(CreateView):
    form_class = CreateGraphicsForm
    template = "graphics/create.html"
    title = "New graphics"
    action_url_name = "new_graphics"
    submit_button_label = "Add new graphics prod"
