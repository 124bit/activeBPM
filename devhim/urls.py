from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = patterns('', url(r'^admin/', include(admin.site.urls)))


if hasattr(settings, 'ENABLE_SILK') and settings.ENABLE_SILK:
    urlpatterns += patterns('', url(r'^silk/', include('silk.urls', namespace='silk')))

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += patterns('', url(r'^', include('activeBPM.urls'), name='dev-home'))

