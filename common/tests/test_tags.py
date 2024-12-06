from django import forms, template
from django.test import TestCase

from common.templatetags.safe_markdown import safe_markdown


class TestSpawningFormsetTag(TestCase):
    def test_spawningformset_without_param(self):
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template('{% load spawning_formset %}{% spawningformset %}{% endspawningformset %}')

    def test_spawningformset_with_undefined_var(self):
        tpl = template.Template('{% load spawning_formset %}{% spawningformset foo %}{% endspawningformset %}')
        context = template.Context({})
        result = tpl.render(context)
        self.assertEqual(result, '')

    def test_spawningform_without_param(self):
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template(
                '{% load spawning_formset %}'
                '{% spawningformset foo %}{% spawningform %}{% endspawningform %}{% endspawningformset %}'
            )

    def test_spawningform_with_malformed_param(self):
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template(
                '{% load spawning_formset %}'
                '{% spawningformset foo %}{% spawningform bar %}{% endspawningform %}{% endspawningformset %}'
            )

    def test_spawningformset_without_delete(self):
        class NameForm(forms.Form):
            name = forms.CharField()

        NameFormSet = forms.formset_factory(NameForm)
        formset = NameFormSet(initial=[{'name': "Raymond Luxury-Yacht"}])

        tpl = template.Template(
            '{% load spawning_formset %}'
            '{% spawningformset formset %}'
            '{% spawningform as form %}{{ form.name }}{% endspawningform %}'
            '{% endspawningformset %}'
        )
        context = template.Context({'formset': formset})
        result = tpl.render(context)

        self.assertIn('<div class="formset_item">', result)
        self.assertNotIn('<span class="delete">', result)


class TestSafeMarkdown(TestCase):
    def test_allow_images(self):
        markdown = """Here is an image: <img src="http://example.com/">"""
        result = safe_markdown(markdown)
        self.assertEqual(result, """<p>Here is an image: <img src="http://example.com/"></p>""")

    def test_pre(self):
        markdown = """<pre>   if we   don't
           preserve whitespace
                    in pre tags
then it's
    all a bit pointless
        </pre>"""
        result = safe_markdown(markdown)
        self.assertEqual(result, markdown)

    def test_link_types(self):
        self.assertEqual(
            safe_markdown('Here is a <a href="ftp://ftp.scene.org">link</a>'),
            '<p>Here is a <a href="ftp://ftp.scene.org">link</a></p>'
        )
        self.assertEqual(
            safe_markdown('Here is a <a href="/local/">link</a>'),
            '<p>Here is a <a href="/local/">link</a></p>'
        )
        self.assertEqual(
            safe_markdown('Here is a <a href="#anchor">link</a>'),
            '<p>Here is a <a href="#anchor">link</a></p>'
        )
        self.assertEqual(
            safe_markdown('Here is a <a href="smb://example.com/warez">link</a>'),
            '<p>Here is a <a>link</a></p>'
        )

    def test_autolink(self):
        self.assertEqual(
            safe_markdown('Here is a link to http://example.com/'),
            '<p>Here is a link to <a href="http://example.com/">http://example.com/</a></p>'
        )
