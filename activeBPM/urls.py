__author__ = 'torn'

from django.conf.urls import patterns, include, url
from activeBPM import views
from django.views.generic.base import TemplateView

#TODO 404 page
moldslist_patterns = patterns('',
    url(r'^zip-folder$', views.zip_folder_task_file, name='zip-folder-task-file'),

    url(r'^process-status$', views.proc_status_view, name='process-status'),
    url(r'^process-init$', views.proc_init_view, name='process-init'),
    url(r'^process-task$', views.task_view, name='process-task'),
    url(r'^all-processes$', views.all_proc_view, name='all-processes'),
    url(r'^process-control$', views.proc_control_view, name='process-control'),
    url(r'^task-control$', views.task_control, name='task-control'),
    url(r'^file-control$', views.file_control, name='file-control'),
    url(r'^var-control$', views.var_control, name='variable-control'),
    url(r'^process-xml$', views.proc_xml, name='process-xml'),
    url(r'^doc-audit$', TemplateView.as_view(template_name='activeBPM/doc_audit.html'),
        name='documentation-audit'),
    url(r'^doc-view$', TemplateView.as_view(template_name='activeBPM/doc_view.html'),
        name='documentation-view'),
    url(r'^$', views.proc_dashboard_view, name='process-dashboard'),
)

urlpatterns = patterns('',
    url(r'^', include(moldslist_patterns, namespace='activeBPM')),
)
