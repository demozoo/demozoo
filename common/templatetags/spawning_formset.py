import re

from django import template
from django.utils.html import escape, format_html


# {% spawningformset [sortable] formset %}
# {% spawningform as form %}
# ...
# {% endspawningform %}
# {% endspawningformset %}

register = template.Library()


@register.tag
def spawningformset(parser, token):
    args = token.split_contents()
    tag_name = args.pop(0)
    if not args:
        raise template.TemplateSyntaxError("%r tag requires arguments" % tag_name)

    sortable = False
    add_button_text = None
    formset_name = None

    for arg in args:
        if arg == "sortable":
            sortable = True
        else:
            m = re.match(r'add_button_text="(.*)"', arg)
            if m:
                add_button_text = m.groups()[0]
            else:
                # treat this as the formset variable name
                formset_name = arg

    nodelist = parser.parse(("endspawningformset",))
    parser.delete_first_token()
    return SpawningFormsetNode(sortable, add_button_text, formset_name, nodelist)


class SpawningFormsetNode(template.Node):
    def __init__(self, sortable, add_button_text, formset_name, nodelist):
        self.sortable = sortable
        self.formset_var = template.Variable(formset_name)
        self.nodelist = nodelist
        self.add_button_text = add_button_text

    def render(self, context):
        try:
            formset = self.formset_var.resolve(context)
        except template.VariableDoesNotExist:
            return ""

        context["formset_context"] = {
            "formset": formset,
            "sortable": self.sortable,
        }

        if self.sortable:
            class_attr = ' class="sortable_formset"'
        else:
            class_attr = ""

        if self.add_button_text is not None:
            data_attr = (' data-add-button-text="%s"' % escape(self.add_button_text),)
        else:
            data_attr = ""

        output = [
            '<div class="spawning_formset"%s>' % data_attr,
            str(formset.management_form),
            "<ul%s>" % class_attr,
            self.nodelist.render(context),
            "</ul>",
            "</div>",
        ]

        return "".join(output)


@register.tag
def spawningform(parser, token):
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    m = re.search(r"as (\w+)", arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    (form_var_name,) = m.groups()

    nodelist = parser.parse(("endspawningform",))
    parser.delete_first_token()
    return SpawningFormNode(form_var_name, nodelist)


class SpawningFormNode(template.Node):
    def __init__(self, form_var_name, nodelist):
        self.form_var_name = form_var_name
        self.nodelist = nodelist

    def render(self, context):
        formset = context["formset_context"]["formset"]
        sortable = context["formset_context"]["sortable"]

        output = []
        for form in formset.forms:
            context[self.form_var_name] = form
            if form.is_bound:
                li_class = "spawned_form bound"
            else:
                li_class = "spawned_form unbound"
            if sortable:
                li_class += " sortable_item"

            if "DELETE" in form.fields:
                delete_field = format_html(
                    '<span class="delete">{0} <label for="{1}">{2}</label></span>',
                    str(form["DELETE"]),
                    form["DELETE"].id_for_label,
                    form["DELETE"].label,
                )
            else:
                delete_field = ""
            output += [
                '<li class="%s">' % li_class,
                '<div class="formset_item">',
                self.nodelist.render(context),
                "</div>",
                delete_field,
                '<div style="clear: both;"></div>',
                "</li>",
            ]

        form = formset.empty_form
        context[self.form_var_name] = form
        if "DELETE" in form.fields:
            delete_field = format_html(
                '<span class="delete">{0} <label for="{1}">{2}</label></span>',
                str(form["DELETE"]),
                form["DELETE"].id_for_label,
                form["DELETE"].label,
            )
        else:
            delete_field = ""
        li_class = "spawned_form placeholder_form"
        if sortable:
            li_class += " sortable_item"
        output += [
            '<li class="%s">' % li_class,
            '<div class="formset_item">',
            self.nodelist.render(context),
            "</div>",
            delete_field,
            '<div style="clear: both;"></div>',
            "</li>",
        ]

        return "".join(output)
