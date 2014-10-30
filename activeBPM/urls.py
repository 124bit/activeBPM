__author__ = 'torn'

from django.conf.urls import patterns, include, url
from activeBPM import views

#TODO 404 page
moldslist_patterns = patterns('',
    url(r'^process-status$', views.proc_status_view, name='process-status'),
    url(r'^process-init$', views.proc_init_view, name='process-init'),
    url(r'^process-task$', views.task_view, name='process-task'),
    url(r'^all-processes$', views.all_proc_view, name='all-processes'),
    url(r'^process-control$', views.proc_control_view, name='process-control'),
    url(r'^task-control$', views.task_control, name='task-control'),
    url(r'^file-control$', views.file_control, name='file-control'),
    url(r'^process-xml$', views.proc_xml, name='process-xml'),
    url(r'^$', views.proc_dashboard_view, name='process-dashboard'),
)

urlpatterns = patterns('',
    url(r'^', include(moldslist_patterns, namespace='activeBPM')),
)
