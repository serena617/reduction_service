from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^jobs/$', 'remote.views.query_remote_jobs'),
    url(r'^authenticate/$', 'remote.views.authenticate'),
)
