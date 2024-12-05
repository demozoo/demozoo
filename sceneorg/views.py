from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from common.views import writeable_site_required
from demoscene.models import Edit
from parties.models import Competition, Party
from productions.models import Production, ProductionLink
from sceneorg.models import Directory, File


@login_required
def compofolders(request):
    parties = Party.objects.filter(external_links__link_class='SceneOrgFolder')

    # only include parties with at least one competition entered
    parties = parties.annotate(num_compos=Count('competitions')).filter(num_compos__gt=0)

    if request.GET.get('order') == 'series':
        parties = parties.select_related('party_series').order_by('party_series__name', 'start_date_date')
        return render(request, 'sceneorg/compofolders/parties_by_series.html', {
            'parties': parties,
        })
    else:
        parties = parties.extra(
            select={'date_year': "DATE_TRUNC('year', start_date_date)"},
            order_by=['date_year', 'name']
        )
        return render(request, 'sceneorg/compofolders/parties_by_year.html', {
            'parties': parties,
        })


@login_required
def compofolder_party(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    sceneorg_paths = [link.parameter for link in party.external_links.filter(link_class='SceneOrgFolder')]

    query = Q(path__startswith=sceneorg_paths[0])
    for path in sceneorg_paths[1:]:
        query = query | Q(path__startswith=path)

    dirs = Directory.objects.filter(query).filter(is_deleted=False).order_by('path').prefetch_related('competitions')
    unmatched_competitions = party.competitions.exclude(sceneorg_directories__in=dirs)
    unmatched_dirs = [d for d in dirs if d.competitions.count() == 0]
    matched_dirs = [d for d in dirs if d.competitions.count() > 0]

    return render(request, 'sceneorg/compofolders/party.html', {
        'party': party,
        'unmatched_directories': unmatched_dirs,
        'unmatched_competitions': unmatched_competitions,
        'matched_directories': matched_dirs,
    })


@writeable_site_required
@login_required
def compofolder_link(request):
    directory = get_object_or_404(Directory, id=request.POST.get('directory_id'))
    competition = get_object_or_404(Competition, id=request.POST.get('competition_id'))

    competition.sceneorg_directories.add(directory)

    return HttpResponse("OK", content_type="text/plain")


@writeable_site_required
@login_required
def compofolder_unlink(request):
    directory = get_object_or_404(Directory, id=request.POST.get('directory_id'))
    competition = get_object_or_404(Competition, id=request.POST.get('competition_id'))

    competition.sceneorg_directories.remove(directory)

    return HttpResponse("OK", content_type="text/plain")


@writeable_site_required
@login_required
def compofolders_done(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    if request.method == 'POST':
        party.sceneorg_compofolders_done = True
        party.save()
        messages.success(request, 'Compo folders for %s marked as done. Thanks!' % party.name)
    return redirect('sceneorg_compofolders')


@login_required
def compofolders_show_directory(request, directory_id):
    directory = get_object_or_404(Directory, id=directory_id)
    prefix_len = len(directory.path)

    subdirectories = [d.path[prefix_len:] for d in directory.subdirectories.order_by('path')]
    files = [f.path[prefix_len:] for f in directory.files.order_by('path')]

    return render(request, 'sceneorg/compofolders/show_directory.html', {
        'subdirectories': subdirectories,
        'files': files,
    })


@login_required
def compofolders_show_competition(request, competition_id):
    competition = get_object_or_404(Competition, id=competition_id)

    placings = competition.placings.prefetch_related(
        'production', 'production__author_nicks', 'production__author_affiliation_nicks'
    )

    return render(request, 'sceneorg/compofolders/show_competition.html', {
        'placings': placings,
    })


@login_required
def compofiles(request):
    # Retrieve a listing of scene.org directories which are associated with a party compo,
    # annotated with the number of files in the directory,
    # and the number of those files which are used as a download link for some production.
    # Where these numbers differ, there are files in the directory which are unaccounted for.
    directories = Directory.objects.raw('''
        SELECT
            sceneorg_directory.id, sceneorg_directory.path,
            COUNT(DISTINCT sceneorg_file.id) - COUNT(DISTINCT productions_productionlink.parameter) AS unmatched_count
        FROM
            sceneorg_directory_competitions
            INNER JOIN sceneorg_directory ON (
                sceneorg_directory_competitions.directory_id = sceneorg_directory.id)
            LEFT JOIN sceneorg_file ON (
                sceneorg_directory.id = sceneorg_file.directory_id
                AND sceneorg_file.is_deleted = 'f'
                AND sceneorg_file.path NOT LIKE '%%/descript.ion'
                AND sceneorg_file.path NOT LIKE '%%/index.htm'
                AND sceneorg_file.path NOT LIKE '%%/files.lst'
                AND sceneorg_file.path NOT LIKE '%%.diz'
            )
            LEFT JOIN productions_productionlink ON (
                sceneorg_file.path = productions_productionlink.parameter
                AND productions_productionlink.link_class = 'SceneOrgFile'
            )
        WHERE
            sceneorg_directory.is_deleted = 'f'
        GROUP BY
            sceneorg_directory.id, sceneorg_directory.path
        ORDER BY sceneorg_directory.path
    ''')

    top_users = User.objects.raw('''
        SELECT
            auth_user.id, auth_user.username,
            COUNT(demoscene_edit.id) AS edit_count
        FROM
            auth_user
            INNER JOIN demoscene_edit ON (
                auth_user.id = demoscene_edit.user_id
                AND action_type = 'add_download_link'
                AND timestamp >= '2013-01-10'
            )
        GROUP BY
            auth_user.id, auth_user.username
        HAVING
            COUNT(demoscene_edit.id) > 0
        ORDER BY
            COUNT(demoscene_edit.id) DESC
        LIMIT 20
    ''')

    return render(request, 'sceneorg/compofiles/index.html', {
        'directories': directories,
        'top_users': top_users,
    })


@login_required
def compofile_directory(request, directory_id):
    directory = get_object_or_404(Directory, id=directory_id)
    competitions = Competition.objects.filter(sceneorg_directories=directory).select_related('party')

    # productions which entered a competition linked to this scene.org directory
    compo_productions = Production.objects.filter(competition_placings__competition__in=competitions).order_by('title')

    # files within this folder, joined to the productions that have those files as download links
    files = File.objects.raw('''
        SELECT
            sceneorg_file.id, sceneorg_file.path,
            productions_productionlink.production_id
        FROM
            sceneorg_file
            LEFT JOIN productions_productionlink ON (
                sceneorg_file.path = productions_productionlink.parameter
                AND productions_productionlink.link_class = 'SceneOrgFile'
            )
        WHERE
            sceneorg_file.directory_id = %s
            AND sceneorg_file.is_deleted = 'f'
            AND sceneorg_file.path NOT LIKE '%%.diz'
        ORDER BY sceneorg_file.path
    ''', [directory.id])

    unmatched_files = [f for f in files if f.production_id is None]
    matches = [
        (f, Production.objects.get(id=f.production_id))
        for f in files
        if f.production_id is not None
    ]
    matched_production_ids = [f.production_id for f in files if f.production_id is not None]
    unmatched_productions = compo_productions.exclude(id__in=matched_production_ids)

    return render(request, 'sceneorg/compofiles/directory.html', {
        'directory': directory,
        'competitions': competitions,
        'unmatched_files': unmatched_files,
        'unmatched_productions': unmatched_productions,
        'matches': matches,
    })


@writeable_site_required
@login_required
def compofile_link(request):
    sceneorg_file = get_object_or_404(File, id=request.POST.get('file_id'))
    production = get_object_or_404(Production, id=request.POST.get('production_id'))

    (link, created) = ProductionLink.objects.get_or_create(
        link_class='SceneOrgFile',
        parameter=sceneorg_file.path,
        production_id=production.id,
        is_download_link=True,
        source='match',
    )
    if created:
        Edit.objects.create(
            action_type='add_download_link', focus=production,
            description=(u"Added download link %s" % link.url), user=request.user
        )

    return HttpResponse("OK", content_type="text/plain")


@writeable_site_required
@login_required
def compofile_unlink(request):
    sceneorg_file = get_object_or_404(File, id=request.POST.get('file_id'))
    production = get_object_or_404(Production, id=request.POST.get('production_id'))
    links = ProductionLink.objects.filter(
        link_class='SceneOrgFile',
        parameter=sceneorg_file.path,
        production_id=production.id)
    if links:
        Edit.objects.create(
            action_type='delete_download_link', focus=production,
            description=(u"Deleted download link %s" % links[0].url), user=request.user
        )
        links.delete()

    return HttpResponse("OK", content_type="text/plain")
