from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^jobs/$', 'remote.views.query_remote_jobs'),
    url(r'^authenticate/$', 'remote.views.authenticate'),
    url(r'^query/(?P<job_id>\d+)/$', 'remote.views.job_details', name='remote_job_details'),
    url(r'^download/(?P<trans_id>\d+)/(?P<filename>[\w\.]+)$', 'remote.views.download_file'),
)
