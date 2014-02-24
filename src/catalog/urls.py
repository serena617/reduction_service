from django.conf.urls import patterns, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'catalog.views.instrument_list', name='catalog'),
    url(r'^(?P<instrument>[\w]+)/$', 'catalog.views.experiment_list', name='catalog_experiments'),
    url(r'^(?P<instrument>[\w]+)/(?P<ipts>[\w\-\.]+)/$', 'catalog.views.experiment_run_list', name='catalog_runs'),
    url(r'^(?P<instrument>[\w]+)/run/(?P<run_number>\d+)/', 'catalog.views.run_info', name='catalog_run_info'),
)
