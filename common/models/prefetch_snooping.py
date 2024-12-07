class PrefetchSnoopingMixin:
    """
    Adds a has_prefetched method to a model, which indicates whether the specified
    relation has been prefetched with prefetch_related. This knowledge can be used
    to optimise methods that follow the relation: if it has been prefetched, then
    it's probably more efficient to refine the cached result in Python, rather than
    running a whole new SQL query.

    Borrowing the pizza example from https://docs.djangoproject.com/en/1.4/ref/models/querysets/#prefetch-related :

    class Pizza(models.Model):
        def spicy_toppings(self):
            return self.toppings.filter(spicy=True)

    would do an unnecessary query if the Pizza instance had been built from
    Pizza.objects.prefetch_related('toppings'). An improvement would be:

    class Pizza(PrefetchSnoopingMixin, models.Model):
        def spicy_toppings(self):
            if self.has_prefetched('toppings'):
                return [topping from topping in self.toppings.all() if topping.spicy == True]
            else:
                return self.toppings.filter(spicy=True)
    """

    def has_prefetched(self, relation_name):
        try:
            return relation_name in self._prefetched_objects_cache
        except AttributeError:
            return False
