__author__ = 'torn'

from django.conf.urls import patterns, include, url
from moldslist import views

#TODO 404 page
moldslist_patterns = patterns('',
    url(r'^process$', views.proc_status_view, name='process-status'),
    url(r'^process-init$', views.proc_init_view, name='process-init'),
    url(r'^process-task$', views.proc_task_view, name='process-task'),
    url(r'^finished-processes$', views.proc_task_view, name='finished-processes'),

    url(r'^process-xml$', views.proc_xml, name='process-xml'),

    url(r'^$', views.dashboard, name='dashboard'),


)

urlpatterns = patterns('',
    url(r'^', include(moldslist_patterns, namespace='moldslist')),
)
