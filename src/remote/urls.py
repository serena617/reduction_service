from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^jobs/$', 'remote.views.query_remote_jobs'),
    url(r'^authenticate/$', 'remote.views.authenticate', name='remote_authenticate'),
    url(r'^query/(?P<job_id>[\w\-\.]+)/$', 'remote.views.job_details', name='remote_job_details'),
    url(r'^download/(?P<trans_id>\d+)/(?P<filename>[\w\-\.]+)$', 'remote.views.download_file', name='remote_download'),
    url(r'^transaction/(?P<trans_id>\d+)/stop/$', 'remote.views.stop_transaction', name='remote_stop_transaction'),
)
