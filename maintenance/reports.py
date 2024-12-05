import redis
from django.conf import settings
from django.db.models import Q

from maintenance.models import Exclusion
from pouet.matching import get_pouetable_prod_types
from productions.models import Production, ProductionLink
from common.utils import groklinks


def write_set(pipe, key, values):
    # Write a set to the given redis key, with expiry of 10 minutes
    pipe.delete(key)
    if values:
        pipe.sadd(key, *values)
        pipe.expire(key, 600)


class FilteredProdutionsReport(object):
    @classmethod
    def run(cls, limit=100, platform_ids=None, production_type_ids=None, release_year=None):
        # compile a list of all the redis keys we're going to use, so that we can
        # construct a transaction that watches them
        used_keys = [cls.master_list_key]

        # use master_list_key as a prefix for the final filtered list
        filtered_result_key = cls.master_list_key
        if platform_ids:
            id_list = ','.join([str(id) for id in platform_ids])
            platforms_filter_key = 'demozoo:productions:by_platforms:%s' % id_list
            used_keys.append(platforms_filter_key)
            filtered_result_key += ':by_platforms:%s' % id_list

        if production_type_ids:
            id_list = ','.join([str(id) for id in production_type_ids])
            prod_types_filter_key = 'demozoo:productions:by_types:%s' % id_list
            used_keys.append(prod_types_filter_key)
            filtered_result_key += ':by_types:%s' % id_list

        if release_year is not None:
            release_year_filter_key = 'demozoo:productions:by_release_year:%d' % release_year
            used_keys.append(release_year_filter_key)
            filtered_result_key += ':by_release_year:%d' % release_year

        if platform_ids or production_type_ids or (release_year is not None):
            used_keys.append(filtered_result_key)

        def _transaction(pipe):
            must_update_master_list = not pipe.exists(cls.master_list_key)
            must_update_platforms_filter = platform_ids and not pipe.exists(platforms_filter_key)
            must_update_prod_types_filter = production_type_ids and not pipe.exists(prod_types_filter_key)
            must_update_release_year_filter = release_year is not None and not pipe.exists(release_year_filter_key)

            filter_keys = []
            if platform_ids:
                filter_keys.append(platforms_filter_key)
            if production_type_ids:
                filter_keys.append(prod_types_filter_key)
            if release_year is not None:
                filter_keys.append(release_year_filter_key)

            pipe.multi()

            if must_update_master_list:
                write_set(pipe, cls.master_list_key, cls.get_master_list())

            if must_update_platforms_filter:
                production_ids = (
                    Production.objects
                    .filter(platforms__id__in=platform_ids)
                    .values_list('id', flat=True)
                )
                write_set(pipe, platforms_filter_key, production_ids)

            if must_update_prod_types_filter:
                production_ids = (
                    Production.objects
                    .filter(types__id__in=production_type_ids)
                    .values_list('id', flat=True)
                )
                write_set(pipe, prod_types_filter_key, production_ids)

            if must_update_release_year_filter:
                production_ids = (
                    Production.objects
                    .filter(release_date_date__year=release_year)
                    .values_list('id', flat=True)
                )
                write_set(pipe, release_year_filter_key, production_ids)

            if filter_keys:
                # create a resultset in filtered_result_key consisting of the intersection
                # of the master_list and the filters
                pipe.sinterstore(filtered_result_key, cls.master_list_key, *filter_keys)
                pipe.expire(filtered_result_key, 600)

                # get randomised list of production IDs
                pipe.srandmember(filtered_result_key, number=limit)
                # get total count of prods after filtering
                pipe.scard(filtered_result_key)

            else:
                # use master_list set directly

                # get randomised list of production IDs
                pipe.srandmember(cls.master_list_key, number=limit)
                # get total count of prods
                pipe.scard(cls.master_list_key)

        r = redis.StrictRedis.from_url(settings.REDIS_URL)
        production_ids, count = r.transaction(_transaction, *used_keys)[-2:]

        productions = (
            Production.objects.filter(id__in=production_ids)
            .prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')
            .defer('notes')
        )

        return (productions, count)


class ProductionsWithoutExternalLinks(FilteredProdutionsReport):
    master_list_key = 'demozoo:productions:without_external_links'

    @classmethod
    def get_master_list(cls):
        excluded_ids = Exclusion.objects.filter(report_name='prods_without_external_links').values_list('record_id', flat=True)

        return (
            Production.objects
            .exclude(links__link_class__in=groklinks.PRODUCTION_EXTERNAL_LINK_TYPES)
            .exclude(id__in=excluded_ids)
            .values_list('id', flat=True)
        )


class ProductionsWithoutReleaseDate(FilteredProdutionsReport):
    master_list_key = 'demozoo:productions:without_release_date'

    @classmethod
    def get_master_list(cls):
        excluded_ids = Exclusion.objects.filter(report_name='prods_without_release_date').values_list('record_id', flat=True)

        return (
            Production.objects
            .filter(release_date_date=None)
            .exclude(id__in=excluded_ids)
            .values_list('id', flat=True)
        )


class ProductionsWithoutScreenshotsReport(FilteredProdutionsReport):
    master_list_key = 'demozoo:productions:without_screenshots'

    @classmethod
    def get_master_list(cls):
        excluded_ids = (
            Exclusion.objects.filter(report_name='prods_without_screenshots').values_list('record_id', flat=True)
        )

        return (
            Production.objects
            .filter(has_screenshot=False)
            .filter(links__is_download_link=True)
            .exclude(supertype='music')
            .exclude(tags__name__in=['lost', 'corrupted-file'])
            .exclude(id__in=excluded_ids)
            .values_list('id', flat=True)
        )


class ProductionsWithoutVideosReport(FilteredProdutionsReport):
    master_list_key = 'demozoo:productions:without_videos'

    @classmethod
    def get_master_list(cls):
        excluded_ids = Exclusion.objects.filter(report_name='prods_without_videos').values_list('record_id', flat=True)

        return (
            Production.objects
            .exclude(links__link_class__in=['YoutubeVideo', 'VimeoVideo'])
            .filter(links__is_download_link=True)
            .exclude(supertype__in=['music', 'graphics'])
            .exclude(tags__name__in=['lost', 'corrupted-file'])
            .exclude(id__in=excluded_ids)
            .values_list('id', flat=True)
        )


class ProductionsWithoutPouetLinksReport(FilteredProdutionsReport):
    master_list_key = 'demozoo:productions:without_pouet_links'

    @classmethod
    def get_master_list(cls):
        excluded_ids = Exclusion.objects.filter(
            report_name='prods_without_pouet_links'
        ).values_list('record_id', flat=True)

        return (
            Production.objects
            .exclude(links__link_class='PouetProduction')
            .filter(types__in=get_pouetable_prod_types())
            .exclude(id__in=excluded_ids)
            .values_list('id', flat=True)
        )


class ProductionsWithoutCreditsReport(FilteredProdutionsReport):
    master_list_key = 'demozoo:productions:without_credits'

    @classmethod
    def get_master_list(cls):
        excluded_ids = Exclusion.objects.filter(report_name='prods_without_credits').values_list('record_id', flat=True)

        # productions which are authored (or co-authored) by a group, but have no individual credits

        return (
            Production.objects
            .filter(author_nicks__releaser__is_group=True)
            .filter(credits__isnull=True)
            .filter(links__is_download_link=True)
            .exclude(id__in=excluded_ids)
            .exclude(tags__name__in=['lost', 'corrupted-file'])
            .values_list('id', flat=True)
        )


class RandomisedProductionsReport(object):
    @classmethod
    def run(cls, limit=100):

        def _transaction(pipe):
            must_update_master_list = not pipe.exists(cls.master_list_key)

            pipe.multi()

            if must_update_master_list:
                write_set(pipe, cls.master_list_key, cls.get_master_list())

            # get randomised list of production IDs
            pipe.srandmember(cls.master_list_key, number=limit)
            # get total count of prods
            pipe.scard(cls.master_list_key)

        r = redis.StrictRedis.from_url(settings.REDIS_URL)
        production_ids, count = r.transaction(_transaction, cls.master_list_key)[-2:]

        productions = (
            Production.objects.filter(id__in=production_ids)
            .prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')
            .defer('notes')
        )

        return (productions, count)


class TrackedMusicWithoutPlayableLinksReport(RandomisedProductionsReport):
    master_list_key = 'demozoo:productions:tracked_music_without_playable_links'

    @classmethod
    def get_master_list(cls):
        excluded_ids = (
            Exclusion.objects.filter(report_name='tracked_music_without_playable_links')
            .values_list('record_id', flat=True)
        )
        prod_ids_with_playable_links = ProductionLink.objects.filter(
            Q(link_class__in=['ModlandFile', 'ModarchiveModule']) |
            Q(link_class='BaseUrl', parameter__startswith='https://media.demozoo.org/')
        ).values_list('production_id', flat=True)

        return (
            Production.objects.filter(supertype='music', types__internal_name='tracked-music')
            .filter(platforms__isnull=True)
            .filter(links__is_download_link=True)
            .exclude(id__in=prod_ids_with_playable_links)
            .exclude(id__in=excluded_ids)
            .exclude(tags__name__in=['lost', 'corrupted-file'])
            .values_list('id', flat=True)
        )
