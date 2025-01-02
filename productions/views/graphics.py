from productions.forms import CreateGraphicsForm, GraphicsIndexFilterForm
from productions.views.generic import CreateView, HistoryView, IndexView, ShowView


class GraphicsIndexView(IndexView):
    supertype = "graphics"
    template = "graphics/index.html"
    filter_form_class = GraphicsIndexFilterForm
    url_name = "graphics"


class GraphicsShowView(ShowView):
    supertype = "graphics"


class GraphicsHistoryView(HistoryView):
    supertype = "graphics"


class CreateGraphicsView(CreateView):
    form_class = CreateGraphicsForm
    template = "graphics/create.html"
    title = "New graphics"
    action_url_name = "new_graphics"
    submit_button_label = "Add new graphics prod"
