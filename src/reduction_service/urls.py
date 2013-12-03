from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # url(r'^$', 'reduction_service.views.home', name='home'),
    url(r'^eqsans/', include('eqsans.urls')),
    url(r'^remote/', include('remote.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^database/doc/', include('django.contrib.admindocs.urls')),
    url(r'^database/', include(admin.site.urls)),
)
