from __future__ import absolute_import, unicode_literals

from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import math

from six.moves import urllib

from demoscene.models import Releaser, ReleaserExternalLink, Membership
from productions.models import Production, Screenshot, ProductionLink, Credit
from parties.models import Party, PartyExternalLink
from zxdemo.models import NewsItem, Article, spectrum_releasers, filter_releasers_queryset_to_spectrum

def home(request):
    ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
    cursor = connection.cursor()
    cursor.execute(
        """
            SELECT COUNT(DISTINCT demoscene_nick.releaser_id)
            FROM demoscene_nick
            WHERE demoscene_nick.id IN (
                SELECT DISTINCT productions_production_author_nicks.nick_id
                FROM productions_production_platforms
                INNER JOIN productions_production_author_nicks ON (productions_production_platforms.production_id = productions_production_author_nicks.production_id)
                WHERE productions_production_platforms.platform_id IN (%s)
            )
            OR demoscene_nick.id IN (
                SELECT DISTINCT productions_production_author_affiliation_nicks.nick_id
                FROM productions_production_platforms
                INNER JOIN productions_production_author_affiliation_nicks ON (productions_production_platforms.production_id = productions_production_author_affiliation_nicks.production_id)
                WHERE productions_production_platforms.platform_id IN (%s)
            )
            OR demoscene_nick.id IN (
                SELECT DISTINCT productions_credit.nick_id
                FROM productions_production_platforms
                INNER JOIN productions_credit ON (productions_production_platforms.production_id = productions_credit.production_id)
                WHERE productions_production_platforms.platform_id IN (%s)
            )
        """, [tuple(ZXDEMO_PLATFORM_IDS), tuple(ZXDEMO_PLATFORM_IDS), tuple(ZXDEMO_PLATFORM_IDS)]
    )
    releaser_count = cursor.fetchone()[0]

    random_screenshot = Screenshot.objects.filter(production__platforms__id__in=ZXDEMO_PLATFORM_IDS).order_by('?')[0]

    latest_releases = Production.objects.filter(platforms__id__in=ZXDEMO_PLATFORM_IDS, release_date_date__isnull=False).order_by('-release_date_date').prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser')[:10]
    latest_additions = Production.objects.filter(platforms__id__in=ZXDEMO_PLATFORM_IDS).order_by('-created_at').prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser')[:10]

    news_items = NewsItem.objects.order_by('-created_at').select_related('author')[:8]

    return render(request, 'zxdemo/home.html', {
        'stats': {
            'demo_count': Production.objects.filter(supertype='production', platforms__id__in=ZXDEMO_PLATFORM_IDS).count(),
            'music_count': Production.objects.filter(supertype='music', platforms__id__in=ZXDEMO_PLATFORM_IDS).count(),
            'graphics_count': Production.objects.filter(supertype='graphics', platforms__id__in=ZXDEMO_PLATFORM_IDS).count(),
            'releaser_count': releaser_count,
        },
        'random_screenshot': random_screenshot,
        'latest_releases': latest_releases,
        'latest_additions': latest_additions,
        'news_items': news_items,
    })


def show_screenshot(request, screenshot_id):
    screenshot = get_object_or_404(Screenshot, id=screenshot_id)
    return render(request, 'zxdemo/show_screenshot.html', {
        'screenshot': screenshot,
        'production': screenshot.production,
    })


def productions(request):
    ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
    productions = Production.objects.filter(
        platforms__id__in=ZXDEMO_PLATFORM_IDS
    ).order_by('sortable_title').prefetch_related('links', 'screenshots', 'author_nicks', 'author_affiliation_nicks')

    supertypes = []
    if request.GET.get('demos', '1'):
        supertypes.append('production')
    if request.GET.get('music', '1'):
        supertypes.append('music')
    if request.GET.get('graphics', '1'):
        supertypes.append('graphics')

    productions = productions.filter(supertype__in=supertypes)
    if request.GET.get('noscreen'):
        productions=productions.filter(screenshots__id__isnull=True)

    count = request.GET.get('count', '50')
    letter = request.GET.get('letter', '')
    if len(letter) == 1 and letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        productions = productions.filter(title__istartswith=letter)

    try:
        int_count = int(count)
    except ValueError:
        int_count = 50

    paginator = Paginator(productions, int_count)
    page = request.GET.get('page')

    try:
        productions_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page of results.
        productions_page = paginator.page(1)
    except EmptyPage:
        # If page is not an integer, or out of range (e.g. 9999), deliver last page of results.
        productions_page = paginator.page(paginator.num_pages)

    return render(request, 'zxdemo/productions.html', {
        'productions': productions_page,
        'count': count,
        'letters': '#ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'count_options': ['10', '25', '50', '75', '100', '150', '200'],
        'filters': {
            'demos': 'production' in supertypes,
            'graphics': 'graphics' in supertypes,
            'music': 'music' in supertypes,
        },
    })

def releases_redirect(request):
    try:
        type_filter = int(request.GET.get('filter') or 7)
    except (ValueError, UnicodeEncodeError):
        type_filter = 7

    url_vars = []

    if not (type_filter & 1):
        url_vars.append('music=')

    if not (type_filter & 2):
        url_vars.append('demos=')

    if not (type_filter & 4):
        url_vars.append('graphics=')

    url = reverse('zxdemo_productions')
    if url_vars:
        url += '?' + '&'.join(url_vars)

    return redirect(url, permanent=True)

def production(request, production_id):
    ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
    production = get_object_or_404(Production, id=production_id, platforms__id__in=ZXDEMO_PLATFORM_IDS)

    try:
        random_screenshot = production.screenshots.order_by('?')[0]
    except IndexError:
        random_screenshot = None

    return render(request, 'zxdemo/production.html', {
        'production': production,
        'competition_placings': production.competition_placings.select_related('competition__party').order_by('competition__party__start_date_date'),
        'credits': production.credits_for_listing(),
        'screenshot': random_screenshot,
        'download_links': production.links.filter(is_download_link=True),
    })


def production_redirect(request):
    try:
        id = int(request.GET.get('id'))
    except (TypeError, ValueError, UnicodeEncodeError):
        raise Http404

    prod_link = get_object_or_404(ProductionLink, link_class='ZxdemoItem', parameter=id)
    return redirect('zxdemo_production', prod_link.production_id, permanent=True)


def authors(request):
    releasers = spectrum_releasers().extra(select={'lower_name': 'lower(demoscene_releaser.name)'}).order_by('lower_name')
    count = request.GET.get('count', '50')
    letter = request.GET.get('letter', '')
    if len(letter) == 1 and letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        releasers = releasers.filter(name__istartswith=letter)

    try:
        int_count = int(count)
    except ValueError:
        int_count = 50

    paginator = Paginator(releasers, int_count)
    page = request.GET.get('page')

    try:
        releasers_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page of results.
        releasers_page = paginator.page(1)
    except EmptyPage:
        # If page is not an integer, or out of range (e.g. 9999), deliver last page of results.
        releasers_page = paginator.page(paginator.num_pages)

    return render(request, 'zxdemo/authors.html', {
        'releasers': releasers_page,
        'count': count,
        'letters': '#ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'count_options': ['10', '25', '50', '75', '100', '150', '200'],
    })


def author(request, releaser_id):
    ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS

    try:
        releaser = spectrum_releasers().get(id=releaser_id)
    except Releaser.DoesNotExist:
        raise Http404

    if releaser.is_group:
        member_memberships = filter_releasers_queryset_to_spectrum(
            releaser.member_memberships.select_related('member'),
            releaser_table='T3'
        )
    else:
        member_memberships = Membership.objects.none()

    group_memberships = filter_releasers_queryset_to_spectrum(
        releaser.group_memberships.select_related('group'),
        releaser_table='T3'
    )

    release_author_filter = Q(author_nicks__releaser=releaser) | Q(author_affiliation_nicks__releaser=releaser)
    releases = Production.objects.filter(
        release_author_filter,
        platforms__id__in=ZXDEMO_PLATFORM_IDS
    ).order_by('release_date_date').distinct().prefetch_related('links', 'screenshots', 'author_nicks', 'author_affiliation_nicks')

    credits = Credit.objects.filter(
        nick__releaser=releaser,
        production__platforms__id__in=ZXDEMO_PLATFORM_IDS
    ).order_by('production__release_date_date', 'production__title', 'production__id').prefetch_related('production__links', 'production__screenshots', 'production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser')

    if request.GET.get('noscreen'):
        releases=releases.exclude(supertype='music').filter(screenshots__id__isnull=True)
        credits=credits.exclude(production__supertype='music').filter(production__screenshots__id__isnull=True)

    releases_by_id = {}
    releases_with_credits = []
    for prod in releases:
        release_record = {'production': prod, 'credits': []}
        releases_by_id[prod.id] = release_record
        releases_with_credits.append(release_record)

    non_releaser_credits = []
    for credit in credits:
        if credit.production_id in releases_by_id:
            releases_by_id[credit.production_id]['credits'].append(credit)
        else:
            non_releaser_credits.append(credit)

    return render(request, 'zxdemo/author.html', {
        'releaser': releaser,
        'member_memberships': member_memberships,
        'group_memberships': group_memberships,
        'releases_with_credits': releases_with_credits,
        'non_releaser_credits': non_releaser_credits,
    })

def author_redirect(request):
    try:
        id = int(request.GET.get('id'))
    except (TypeError, ValueError, UnicodeEncodeError):
        raise Http404

    releaser_link = get_object_or_404(ReleaserExternalLink, link_class='ZxdemoAuthor', parameter=id)
    return redirect('zxdemo_author', releaser_link.releaser_id, permanent=True)


def parties(request):
    ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS

    parties_with_spectrum_entries = list(Party.objects.filter(
        competitions__placings__production__platforms__id__in=ZXDEMO_PLATFORM_IDS
    ).distinct().values_list('id', flat=True))
    parties_with_spectrum_invitations = list(Party.objects.filter(
        invitations__platforms__id__in=ZXDEMO_PLATFORM_IDS
    ).distinct().values_list('id', flat=True))

    parties = Party.objects.filter(
        id__in=(parties_with_spectrum_entries + parties_with_spectrum_invitations)
    ).order_by('start_date_date')
    return render(request, 'zxdemo/parties.html', {
        'parties': parties,
    })


def parties_year(request, year):
    ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS

    parties_with_spectrum_entries = list(Party.objects.filter(
        competitions__placings__production__platforms__id__in=ZXDEMO_PLATFORM_IDS
    ).distinct().values_list('id', flat=True))
    parties_with_spectrum_invitations = list(Party.objects.filter(
        invitations__platforms__id__in=ZXDEMO_PLATFORM_IDS
    ).distinct().values_list('id', flat=True))

    parties = Party.objects.filter(
        id__in=(parties_with_spectrum_entries + parties_with_spectrum_invitations),
        start_date_date__year=year
    ).distinct().order_by('start_date_date')

    all_years = Party.objects.filter(
        id__in=(parties_with_spectrum_entries + parties_with_spectrum_invitations),
    ).dates('start_date_date', 'year')

    return render(request, 'zxdemo/parties_year.html', {
        'year': int(year),
        'all_years': all_years,
        'parties': parties,
    })


def partycalendar_redirect(request):
    try:
        year = int(request.GET.get('year'))
    except (ValueError, TypeError, UnicodeEncodeError):
        year = None

    if year:
        return redirect('zxdemo_parties_year', year, permanent=True)
    else:
        return redirect('zxdemo_parties', permanent=True)


def party(request, party_id):
    ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS
    party = get_object_or_404(Party, id=party_id)

    # all competitions with at least one Spectrum entry
    competitions = party.competitions.filter(
        placings__production__platforms__id__in=ZXDEMO_PLATFORM_IDS
    ).distinct().order_by('name', 'id')
    competitions_with_placings = []

    for competition in competitions:
        placings = competition.placings.order_by('position', 'production__id').prefetch_related(
            'production__author_nicks__releaser', 'production__author_affiliation_nicks__releaser', 'production__platforms', 'production__types'
        ).defer('production__notes', 'production__author_nicks__releaser__notes', 'production__author_affiliation_nicks__releaser__notes')

        screenshots = Screenshot.objects.filter(
            production__competition_placings__competition=competition,
            production__platforms__id__in=ZXDEMO_PLATFORM_IDS).order_by('?')[:math.ceil(len(placings) / 6.0)]

        competitions_with_placings.append(
            (
                competition, placings, screenshots,
            )
        )

    # Do not show an invitations section in the special case that all invitations are
    # entries in a competition at this party (which probably means that it was an invitation compo)
    invitations = party.invitations.filter(platforms__id__in=ZXDEMO_PLATFORM_IDS).prefetch_related('author_nicks__releaser', 'author_affiliation_nicks__releaser', 'platforms', 'types')
    non_competing_invitations = invitations.exclude(competition_placings__competition__party=party)
    if not non_competing_invitations:
        invitations = Production.objects.none

    return render(request, 'zxdemo/party.html', {
        'party': party,
        'competitions_with_placings': competitions_with_placings,
        'invitations': invitations,
    })


def party_redirect(request):
    try:
        id = int(request.GET.get('id'))
    except (TypeError, ValueError, UnicodeEncodeError):
        raise Http404

    party_link = get_object_or_404(PartyExternalLink, link_class='ZxdemoParty', parameter=id)
    return redirect('zxdemo_party', party_link.party_id, permanent=True)


def rss(request):
    return render(request, 'zxdemo/rss.xml', {
        'news_items': NewsItem.objects.order_by('-created_at').select_related('author')[:8]
    }, content_type='text/xml')


def search(request):
    ZXDEMO_PLATFORM_IDS = settings.ZXDEMO_PLATFORM_IDS

    search_term = request.GET.get('search', '')

    try:
        demoskip = int(request.GET.get('demoskip', 0))
    except ValueError:
        demoskip = 0

    try:
        musicskip = int(request.GET.get('musicskip', 0))
    except ValueError:
        musicskip = 0

    try:
        gfxskip = int(request.GET.get('gfxskip', 0))
    except ValueError:
        gfxskip = 0

    try:
        scenerskip = int(request.GET.get('scenerskip', 0))
    except ValueError:
        scenerskip = 0

    feature = request.GET.get('feature')

    base_url_params = {
        'search': search_term,
        'feature': feature,
        'musicskip': musicskip,
        'demoskip': demoskip,
        'gfxskip': gfxskip,
        'scenerskip': scenerskip,
    }

    demos = Production.objects.filter(
        platforms__id__in=ZXDEMO_PLATFORM_IDS, supertype='production',
        title__icontains=search_term
    ).order_by('sortable_title').prefetch_related('links', 'screenshots', 'author_nicks', 'author_affiliation_nicks')

    demos = list(demos[demoskip:demoskip+11])
    if len(demos) == 11:
        demos = demos[:10]
        url_params = base_url_params.copy()
        url_params.update({
            'feature': 'demos', 'demoskip': demoskip + 10
        })
        demos_next_link = reverse('zxdemo_search') + '?' + urllib.parse.urlencode(url_params)
    else:
        demos_next_link = None

    if demoskip > 0:
        url_params = base_url_params.copy()
        url_params.update({
            'feature': 'demos', 'demoskip': max(0, demoskip - 10)
        })
        demos_prev_link = reverse('zxdemo_search') + '?' + urllib.parse.urlencode(url_params)
    else:
        demos_prev_link = None


    musics = Production.objects.filter(
        platforms__id__in=ZXDEMO_PLATFORM_IDS, supertype='music',
        title__icontains=search_term
    ).order_by('sortable_title').prefetch_related('links', 'screenshots', 'author_nicks', 'author_affiliation_nicks')

    musics = list(musics[musicskip:musicskip+11])
    if len(musics) == 11:
        musics = musics[:10]
        url_params = base_url_params.copy()
        url_params.update({
            'feature': 'music', 'musicskip': musicskip + 10
        })
        musics_next_link = reverse('zxdemo_search') + '?' + urllib.parse.urlencode(url_params)
    else:
        musics_next_link = None

    if musicskip > 0:
        url_params = base_url_params.copy()
        url_params.update({
            'feature': 'music', 'musicskip': max(0, musicskip - 10)
        })
        musics_prev_link = reverse('zxdemo_search') + '?' + urllib.parse.urlencode(url_params)
    else:
        musics_prev_link = None


    graphics = Production.objects.filter(
        platforms__id__in=ZXDEMO_PLATFORM_IDS, supertype='graphics',
        title__icontains=search_term
    ).order_by('sortable_title').prefetch_related('links', 'screenshots', 'author_nicks', 'author_affiliation_nicks')

    graphics = list(graphics[gfxskip:gfxskip+11])
    if len(graphics) == 11:
        graphics = graphics[:10]
        url_params = base_url_params.copy()
        url_params.update({
            'feature': 'graphics', 'gfxskip': gfxskip + 10
        })
        graphics_next_link = reverse('zxdemo_search') + '?' + urllib.parse.urlencode(url_params)
    else:
        graphics_next_link = None

    if gfxskip > 0:
        url_params = base_url_params.copy()
        url_params.update({
            'feature': 'graphics', 'gfxskip': max(0, gfxskip - 10)
        })
        graphics_prev_link = reverse('zxdemo_search') + '?' + urllib.parse.urlencode(url_params)
    else:
        graphics_prev_link = None


    sceners = spectrum_releasers().filter(
        nicks__name__icontains=search_term
    ).distinct().extra(select={'lower_name': 'lower(demoscene_releaser.name)'}).order_by('lower_name')

    sceners = list(sceners[scenerskip:scenerskip+11])
    if len(sceners) == 11:
        sceners = sceners[:10]
        url_params = base_url_params.copy()
        url_params.update({
            'feature': 'sceners', 'scenerskip': scenerskip + 10
        })
        sceners_next_link = reverse('zxdemo_search') + '?' + urllib.parse.urlencode(url_params)
    else:
        sceners_next_link = None

    if scenerskip > 0:
        url_params = base_url_params.copy()
        url_params.update({
            'feature': 'sceners', 'scenerskip': max(0, scenerskip - 10)
        })
        sceners_prev_link = reverse('zxdemo_search') + '?' + urllib.parse.urlencode(url_params)
    else:
        sceners_prev_link = None


    return render(request, 'zxdemo/search.html', {
        'search_term': search_term,
        'feature': feature,

        'demos': demos,
        'demos_prev_link': demos_prev_link,
        'demos_next_link': demos_next_link,

        'musics': musics,
        'musics_prev_link': musics_prev_link,
        'musics_next_link': musics_next_link,

        'graphics': graphics,
        'graphics_prev_link': graphics_prev_link,
        'graphics_next_link': graphics_next_link,

        'sceners': sceners,
        'sceners_prev_link': sceners_prev_link,
        'sceners_next_link': sceners_next_link,
    })


def articles(request):
    articles = Article.objects.order_by('created_at')
    return render(request, 'zxdemo/articles.html', {
        'articles': articles,
    })


def article(request, zxdemo_id):
    article = get_object_or_404(Article, zxdemo_id = zxdemo_id)
    articles = Article.objects.order_by('created_at')
    return render(request, 'zxdemo/article.html', {
        'article': article,
        'articles': articles,
    })


def article_redirect(request):
    id = request.GET.get('id')
    if id is None:
        return redirect('zxdemo_articles')

    try:
        return redirect('zxdemo_article', int(id))
    except (ValueError, UnicodeEncodeError):
        raise Http404


def page_not_found(request):
    return render(request, 'zxdemo/404.html', status=404)
