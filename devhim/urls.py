from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth.decorators import login_required

handler404 = 'site_utils.handler404'
handler500 = 'site_utils.handler500'


@login_required
def protected_serve(request, path, document_root=None, show_indexes=False):
    return serve(request, path, document_root, show_indexes)

urlpatterns = patterns('', url(r'^admin/', include(admin.site.urls)))


if hasattr(settings, 'ENABLE_SILK') and settings.ENABLE_SILK:
    urlpatterns += patterns('', url(r'^silk/', include('silk.urls', namespace='silk')))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += patterns('',
        url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], protected_serve, {'document_root': settings.MEDIA_ROOT}),
    )

urlpatterns += patterns('', url(r'^', include('activeBPM.urls'), name='dev-home'))

