from django.conf.urls import patterns, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'eqsans.views.reduction_home'),
    url(r'^reduction/$', 'eqsans.views.reduction_options', name='eqsans_new_reduction'),
    url(r'^reduction/(?P<reduction_id>\d+)/$', 'eqsans.views.reduction_options', name='eqsans_reduction'),
    url(r'^reduction/(?P<reduction_id>\d+)/script$', 'eqsans.views.reduction_script'),
    url(r'^reduction/(?P<reduction_id>\d+)/submit$', 'eqsans.views.submit_job'),
    url(r'^reduction/(?P<reduction_id>\d+)/download/py$', 'eqsans.views.py_reduction_script'),
    url(r'^reduction/(?P<reduction_id>\d+)/download/xml$', 'eqsans.views.xml_reduction_script'),
    url(r'^query/(?P<job_id>\d+)/$', 'eqsans.views.job_details'),
    url(r'^jobs/$', 'eqsans.views.reduction_jobs', name='eqsans_reduction_jobs'),

)
