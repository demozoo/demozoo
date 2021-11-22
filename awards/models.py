# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from productions.models import Production, ProductionType


class Event(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, help_text="Used in URLs - /awards/[slug]/")
    intro = models.TextField(
        blank=True, help_text="Intro text to show on 'your recommendations' page - Markdown / HTML supported"
    )

    eligibility_start_date = models.DateField(
        help_text="Earliest release date a production can have to be considered for these awards"
    )
    eligibility_end_date = models.DateField(
        help_text="Latest release date a production can have to be considered for these awards"
    )

    production_types = models.ManyToManyField(
        ProductionType, blank=True,
        help_text="If set, these awards only accept recommendations for productions of these types"
    )

    recommendations_enabled = models.BooleanField(
        default=False, help_text="Whether these awards are currently accepting recommendations"
    )
    reporting_enabled = models.BooleanField(
        default=False, help_text="Whether jurors can currently view reports for these awards"
    )

    juror_feed_url = models.URLField(blank=True, max_length=255, help_text="URL to a list of juror SceneIDs")

    def __str__(self):
        return self.name

    @classmethod
    def accepting_recommendations_for(cls, production):
        """
        Return a queryset of award events that it is currently possible
        to recommend this prod for
        """
        if production.release_date_date is None:
            return cls.objects.none()

        # retrieve all production types that are ancestors (including self) of any production
        # type of this production
        prod_types_q = Q(pk__in=[])  # always false
        for prod_type in production.types.all():
            paths = [
                prod_type.path[0:pos]
                for pos in range(prod_type.steplen, len(prod_type.path) + 1, prod_type.steplen)
            ]
            prod_types_q |= Q(path__in=paths)
        prod_types = list(ProductionType.objects.filter(prod_types_q))

        return cls.objects.filter(
            recommendations_enabled=True,
            eligibility_start_date__lte=production.release_date_date,
            eligibility_end_date__gte=production.release_date_date,
        ).filter(
            Q(production_types__isnull=True) | Q(production_types__in=prod_types)
        )

    @classmethod
    def active_for_user(cls, user):
        """
        Return a queryset of award events that are either open for recommendations or have
        reports open for the given user
        """
        if not user.is_authenticated:
            return cls.objects.filter(recommendations_enabled=True)
        elif user.is_staff:
            return cls.objects.filter(
                models.Q(recommendations_enabled=True) | models.Q(reporting_enabled=True)
            )
        else:
            return Event.objects.filter(
                models.Q(recommendations_enabled=True) | models.Q(reporting_enabled=True, jurors__user=user)
            ).distinct()

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
        return (
            self.reporting_enabled
            and user.is_authenticated
            and (user.is_staff or self.jurors.filter(user=user).exists())
        )


class Category(models.Model):
    event = models.ForeignKey(Event, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.IntegerField(null=True, blank=True)

    def __str__(self):
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
    is_sticky = models.BooleanField(
        default=False, help_text=(
            "If set, this juror will not be removed in the event that they are absent from the feed of jury members"
        )
    )

    class Meta:
        unique_together = [
            ('user', 'event'),
        ]
