from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'catalog.views.instrument_list', name='home'),
    url(r'^eqsans/', include('eqsans.urls')),
    url(r'^remote/', include('remote.urls')),
    url(r'^catalog/', include('catalog.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^database/doc/', include('django.contrib.admindocs.urls')),
    url(r'^database/', include(admin.site.urls)),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )