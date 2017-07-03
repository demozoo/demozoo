from django.conf.urls import url

from maintenance import views

app_name = 'maintenance'

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^prods_without_screenshots$', views.prods_without_screenshots, name='prods_without_screenshots'),
	url(r'^prods_without_external_links$', views.prods_without_external_links, name='prods_without_external_links'),
	url(r'^prods_with_dead_amigascne_links$', views.prods_with_dead_amigascne_links, name='prods_with_dead_amigascne_links'),
	url(r'^prods_with_dead_amiga_nvg_org_links$', views.prods_with_dead_amiga_nvg_org_links, name='prods_with_dead_amiga_nvg_org_links'),
	url(r'^prods_without_platforms$', views.prods_without_platforms, name='prods_without_platforms'),
	url(r'^prods_without_platforms_excluding_lost$', views.prods_without_platforms_excluding_lost, name='prods_without_platforms_excluding_lost'),
	url(r'^prods_without_platforms_with_downloads$', views.prods_without_platforms_with_downloads, name='prods_without_platforms_with_downloads'),
	url(r'^prods_with_blurbs$', views.prods_with_blurbs, name='prods_with_blurbs'),
	url(r'^tiny_intros_without_download_links$', views.tiny_intros_without_download_links, name='tiny_intros_without_download_links'),
	url(r'^tiny_intros_without_screenshots$', views.tiny_intros_without_screenshots, name='tiny_intros_without_screenshots'),
	url(r'^prod_comments$', views.prod_comments, name='prod_comments'),

	# release dates
	url(r'^prod_soundtracks_without_release_date$', views.prod_soundtracks_without_release_date, name='prod_soundtracks_without_release_date'),
	url(r'^prods_without_release_date$', views.prods_without_release_date, name='prods_without_release_date'),
	url(r'^prods_without_release_date_with_placement$', views.prods_without_release_date_with_placement, name='prods_without_release_date_with_placement'),
	url(r'^prods_with_release_date_outside_party$', views.prods_with_release_date_outside_party, name='prods_with_release_date_outside_party'),
	url(r'^fix_release_dates$', views.fix_release_dates, name='fix_release_dates'),

	# cleanup
	url(r'^group_nicks_with_brackets$', views.group_nicks_with_brackets, name='group_nicks_with_brackets'),
	url(r'^ambiguous_groups_with_no_differentiators$', views.ambiguous_groups_with_no_differentiators, name='ambiguous_groups_with_no_differentiators'),
	url(r'^implied_memberships$', views.implied_memberships, name='implied_memberships'),
	url(r'^add_membership$', views.add_membership, name='add_membership'),
	url(r'^sceneorg_party_dirs_with_no_party$', views.sceneorg_party_dirs_with_no_party, name='sceneorg_party_dirs_with_no_party'),
	url(r'^add_sceneorg_link_to_party$', views.add_sceneorg_link_to_party, name='add_sceneorg_link_to_party'),
	url(r'^empty_releasers$', views.empty_releasers, name='empty_releasers'),
	url(r'^public_real_names$', views.public_real_names, name='public_real_names'),
	url(r'^credits_to_move_to_text$', views.credits_to_move_to_text, name='credits_to_move_to_text'),
	url(r'^sceneorg_download_links_with_unicode$', views.sceneorg_download_links_with_unicode, name='sceneorg_download_links_with_unicode'),

	# de-duping
	url(r'^prods_with_same_named_credits$', views.prods_with_same_named_credits, name='prods_with_same_named_credits'),
	url(r'^same_named_prods_by_same_releaser$', views.same_named_prods_by_same_releaser, name='same_named_prods_by_same_releaser'),
	url(r'^same_named_prods_without_special_chars$', views.same_named_prods_without_special_chars, name='same_named_prods_without_special_chars'),
	url(r'^duplicate_external_links$', views.duplicate_external_links, name='duplicate_external_links'),
	url(r'^matching_real_names$', views.matching_real_names, name='matching_real_names'),
	url(r'^matching_surnames$', views.matching_surnames, name='matching_surnames'),
	url(r'^groups_with_same_named_members$', views.groups_with_same_named_members, name='groups_with_same_named_members'),
	url(r'^releasers_with_same_named_groups$', views.releasers_with_same_named_groups, name='releasers_with_same_named_groups'),

	# parties
	url(r'^parties_with_incomplete_dates$', views.parties_with_incomplete_dates, name='parties_with_incomplete_dates'),
	url(r'^parties_with_no_location$', views.parties_with_no_location, name='parties_with_no_location'),
	url(r'^result_file_encoding$', views.results_with_no_encoding, name='results_with_no_encoding'),
	url(r'^result_file_encoding/(\d+)/$', views.fix_results_file_encoding, name='fix_results_file_encoding'),

	url(r'^exclude$', views.exclude, name='exclude'),

	url(r'^unresolved_screenshots$', views.unresolved_screenshots, name='unresolved_screenshots'),
	url(r'^archive_member/(\d+)/$', views.view_archive_member, name='view_archive_member'),
	url(r'^resolve_screenshot/(\d+)/(\d+)/$', views.resolve_screenshot, name='resolve_screenshot'),
]
