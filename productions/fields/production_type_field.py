from django import forms


class ProductionTypeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s %s" % ("\u2192" * (obj.depth - 1), obj.name)


class ProductionTypeMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return "%s %s" % ("\u2192" * (obj.depth - 1), obj.name)
