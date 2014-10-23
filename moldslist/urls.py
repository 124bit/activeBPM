__author__ = 'torn'

from django.conf.urls import patterns, include, url
from moldslist import views

#TODO 404 page
moldslist_patterns = patterns('',
    url(r'^process$', views.proc_status_view, name='process-status'),
    url(r'^process-init$', views.proc_init_view, name='process-init'),
    url(r'^process-task$', views.proc_task_view, name='process-task'),
    url(r'^all-processes$', views.allprocesses, name='all-processes'),
    url(r'^process-control$', views.proc_control, name='process-control'),
    url(r'^task-control$', views.task_control, name='task-control'),
    url(r'^file-control$', views.file_control, name='file-control'),

    url(r'^process-xml$', views.proc_xml, name='process-xml'),

    url(r'^$', views.dashboard, name='dashboard'),


)

urlpatterns = patterns('',
    url(r'^', include(moldslist_patterns, namespace='moldslist')),
)
