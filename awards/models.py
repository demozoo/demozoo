# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from productions.models import Production


class Event(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, help_text="Used in URLs - /awards/[slug]/")
    intro = models.TextField(blank=True, help_text="Intro text to show on 'your recommendations' page - Markdown / HTML supported")

    eligibility_start_date = models.DateField(help_text="Earliest release date a production can have to be considered for these awards")
    eligibility_end_date = models.DateField(help_text="Latest release date a production can have to be considered for these awards")

    recommendations_enabled = models.BooleanField(default=False, help_text="Whether these awards are currently accepting recommendations")
    reporting_enabled = models.BooleanField(default=False, help_text="Whether jurors can currently view reports for these awards")

    juror_feed_url = models.URLField(blank=True, max_length=255, help_text="URL to a list of juror SceneIDs")

    def __unicode__(self):
        return self.name

    @classmethod
    def accepting_recommendations_for(cls, production):
        """
        Return a queryset of award events that it is currently possible
        to recommend this prod for
        """
        if production.supertype != 'production' or production.release_date_date is None:
            return cls.objects.none()

        return cls.objects.filter(
            recommendations_enabled=True,
            eligibility_start_date__lte=production.release_date_date,
            eligibility_end_date__gte=production.release_date_date,
        )

    def get_recommendation_options(self, user, production):
        """
        Return list of (category_id, category_name, has_recommended) tuples for this
        event's awards, where has_recommended is a boolean indicating whether this
        user has already recommended this production for that category
        """
        categories = list(self.categories.all())
        recommendations = set(
            Recommendation.objects.filter(
                user=user, production=production,
                category__in=categories
            ).values_list('category_id', flat=True)
        )
        return [
            (category.id, category.name, category.id in recommendations)
            for category in categories
        ]

    def user_can_view_reports(self, user):
        return user.is_staff or self.jurors.filter(user=user).exists()


class Category(models.Model):
    event = models.ForeignKey(Event, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    def get_recommendation_report(self):
        return Production.objects.filter(award_recommendations__category=self).\
            annotate(recommendation_count=models.Count('award_recommendations')).\
            order_by('-recommendation_count', 'sortable_title')

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['position']


class Recommendation(models.Model):
    user = models.ForeignKey(User, related_name='award_recommendations', on_delete=models.CASCADE)
    production = models.ForeignKey(Production, related_name='award_recommendations', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='recommendations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ('user', 'production', 'category'),
        ]


class Juror(models.Model):
    user = models.ForeignKey(User, related_name='juror_appointments', on_delete=models.CASCADE)
    event = models.ForeignKey(Event, related_name='jurors', on_delete=models.CASCADE)
    is_sticky = models.BooleanField(default=False, help_text="If set, this juror will not be removed in the event that they are absent from the feed of jury members")

    class Meta:
        unique_together = [
            ('user', 'event'),
        ]
