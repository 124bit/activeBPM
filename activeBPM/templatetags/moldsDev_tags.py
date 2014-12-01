__author__ = 'torn'
from django import template
from activeBPM.views import folders_paths
from activeBPM.activiti_api import ActivityREST
import os
register = template.Library()


@register.assignment_tag
def get_mold_folders(with_temp_docs=True):
    finished_doc_folder = folders_paths['molds_documentation']
    temp_doc_folder = os.path.join(finished_doc_folder, 'temp', '')
    doc_folders = []
    for doc_path in os.listdir(finished_doc_folder):
        if not os.path.isfile(doc_path):
            doc_path_folder = os.path.basename(os.path.normpath(doc_path))
            doc_folders.append(doc_path_folder)

    if with_temp_docs:
        for doc_path in os.listdir(temp_doc_folder):
            if not os.path.isfile(doc_path):
                doc_path_folder = os.path.basename(os.path.normpath(doc_path))
                doc_folders.append('temp/' + doc_path_folder)
    doc_folders.remove('temp')
    return doc_folders

@register.assignment_tag(takes_context=True)
def get_group_members(context, group_name):
    request = context['request']
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    members = rest_client.get_group_users_by_group_name(group_name)
    return members