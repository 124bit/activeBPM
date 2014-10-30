from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
#    url(r'^silk/', include('silk.urls', namespace='silk')),
    url(r'^', include('activeBPM.urls'), name='dev-home'),
)
