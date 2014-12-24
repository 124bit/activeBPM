from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from activeBPM.activiti_api import ActivityREST
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from activeBPM.models import TaskFile
from django.template import TemplateDoesNotExist
from activeBPM import process_forms_default
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
import ntpath
import json
import time
template_folder = 'activeBPM'
proc_dashbord_template = os.path.join(template_folder, 'proc_dashbord.html')
all_proc_template = os.path.join(template_folder, 'all_proc.html')
proc_control_template = os.path.join(template_folder, 'proc_control.html')
proc_status_template = os.path.join(template_folder, 'proc_base.html')
task_template = os.path.join(template_folder, 'task.html')
proc_init_template = os.path.join(template_folder, 'proc_base.html')
category = 'molds_development'
from activeBPM import molds_documentation_forms as forms_module
folders_paths = {'molds_documentation': os.path.join(settings.MEDIA_ROOT, 'Dropbox/molds_documentation/')}


#TODO profile
#TODO add a web account existance check
#TODO add a user group check if will be other modules than molds
#TODO add right permissions to admin and other groups
#TODO add a process sort by last state change
#TODO localization
#from silk.profiling.profiler import silk_profile
#@silk_profile(name='View main process list')
@login_required()
def proc_dashboard_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    active_proc_table = rest_client.get_proc_instncs_info_by_category(category, def_state='active',
                                                                            instnc_state='active')

    #TODO fix: not latest two from every latest def, but simply latest two
    finished_proc_table = rest_client.get_proc_instncs_info_by_category(category,
                                                                                       def_state='active',
                                                                                       instnc_state='finished',
                                                                                       quantity_per_def=2,
                                                                                       latest_def=True)

    admin_userids = rest_client.get_group_userids_by_group_name('admin')
    if request.user.bpmsuser.login in admin_userids:
        assignee_task_table = rest_client.get_tasks_info()
    else:
        assignee_task_table = rest_client.get_tasks_info(assignee=request.user.bpmsuser.login) + \
            rest_client.get_tasks_info(candidate_user=request.user.bpmsuser.login)

    if request.user.bpmsuser.login in admin_userids:
        available_proc_table = rest_client.get_proc_defs_info_by_category(category=category, def_state='active',
                                                                     latest_def=True)
    else:
        available_proc_table = rest_client.get_proc_defs_info_by_category(category=category, def_state='active',
                                                                     latest_def=True,
                                                                     startable_by_user=request.user.bpmsuser.login)
    tmpl_dict = {'active_proc_table': active_proc_table,
                 'finished_proc_table': finished_proc_table,
                 'assignee_task_table': assignee_task_table,
                 'available_proc_table': available_proc_table}
    return render(request, proc_dashbord_template, tmpl_dict)


@login_required()
def all_proc_view(request):
    #from activeBPM.tasks import new_task_sms
    #new_task_sms()
    #return HttpResponse('ok')
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)

    active_proc_table = rest_client.get_proc_instncs_info_by_category(category, def_state='active',
                                                                            instnc_state='active')
    suspended_proc_table = rest_client.get_proc_instncs_info_by_category(category, def_state='active',
                                                                            instnc_state='suspended')
    finished_proc_table = rest_client.get_proc_instncs_info_by_category(category, def_state='active',
                                                                            instnc_state='finished')
    tmpl_dict = {
        'active_proc_table': active_proc_table,
        'finished_proc_table': finished_proc_table,
        'suspended_proc_table': suspended_proc_table
    }
    return render(request, all_proc_template, tmpl_dict)


@login_required()
def proc_status_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    proc_instnc_id = request.GET['instnc_id']
    proc = rest_client.get_proc_instnc_info(proc_instnc_id)
    tmpl_dict = {'proc': proc}
    return render(request, proc_status_template, tmpl_dict)


#TODO check if task is a task of right user and process is active
#TODO simplify
@login_required()
def task_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    proc_instnc_id = request.GET['instnc_id']
    task_id = request.GET['task_id']
    proc = rest_client.get_proc_instnc_info(proc_instnc_id)
    task = rest_client.get_task_info(task_id)
    try:
        task_form_class = getattr(forms_module, '%s__%s' % (proc['def_key'], task['def_key']))
    except AttributeError:
        try:
            task_form_class = getattr(forms_module, 'TaskDefault')
        except AttributeError:
            task_form_class = getattr(process_forms_default, 'TaskDefault')
    if request.method == 'POST':
        admin_userids = rest_client.get_group_userids_by_group_name('admin')
        task_form = task_form_class(request.POST)
        if task_form.is_valid():
            data = task_form.cleaned_data
            rest_client.set_proc_vars(proc_instnc_id, data)
            rest_client.complete_task(task_id)
            task_form.after_complete()
            if request.user.bpmsuser.login in admin_userids:
                assignee_task_table = rest_client.get_tasks_info()
            else:
                assignee_task_table = rest_client.get_tasks_info(assignee=request.user.bpmsuser.login)

            next_tasks = [task for task in assignee_task_table if task['proc_instnc_id'] == proc_instnc_id]
            if len(next_tasks) == 1:
                next_task_id = next_tasks[0]['id']
                return HttpResponseRedirect(reverse("activeBPM:process-task")
                                     + '?instnc_id=%s&task_id=%s' % (proc_instnc_id, next_task_id))
            else:
                return HttpResponseRedirect(reverse("activeBPM:process-status") + '?instnc_id=%s' % proc_instnc_id)
        else:
            if request.user.bpmsuser.login in admin_userids:
                errors = task_form.errors
                return HttpResponse(str(errors))
            else:
                pass #error for users
    else:
        task_form = task_form_class()
    proc_template_folder = os.path.join(template_folder, 'proc_templates', proc['def_key'], '')
    proc_task_default_template = os.path.join(proc_template_folder, 'task_default.html')
    proc_task_main_default_template = 'activeBPM/proc_templates/default_process/task_default.html'
    task_tmpl = os.path.join(proc_template_folder, '%s__%s.html' % (proc['def_key'], task['def_key']))
    tmpl_dict = {'proc': proc, 'task': task, 'task_form': task_form}
    try:
        return render(request, task_tmpl, tmpl_dict)
    except TemplateDoesNotExist:
        try:
            return render(request, proc_task_default_template, tmpl_dict)
        except TemplateDoesNotExist:
            return render(request, proc_task_main_default_template, tmpl_dict)


#TODO init files loading works incorrect. Need right init behavior in process history and in file uploading
#TODO simplify
#upload with nowtime and then update key to process instance id - bed idea
@login_required()
def proc_init_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    proc_def_id = request.GET['def_id']
    proc = rest_client.get_proc_def_info(proc_def_id)
    init_task_id = 'init_%s_%s' % (request.user.bpmsuser.login, proc['def_key'])
    try:
        task_form_class = getattr(forms_module, '%s__%s' % (proc['def_key'], 'init'))
    except AttributeError:
        try:
            task_form_class = getattr(forms_module, 'ProcessInitDefault')
        except AttributeError:
            task_form_class = getattr(process_forms_default, 'ProcessInitDefault')
    if request.method == 'POST':
        task_form = task_form_class(request.POST)
        admin_userids = rest_client.get_group_userids_by_group_name('admin')
        if task_form.is_valid():
            data = task_form.cleaned_data
            #data['worker'] = '124bit'
            proc_instnc = rest_client.start_proc(proc_def_id, data)
            proc_instnc_id = proc_instnc['id']
            task_files = TaskFile.objects.filter(key='_' + init_task_id, purpose='comment')
            for task_file in task_files:
                task_file.key = proc_instnc_id + '_init'
                task_file.save()
            task_form.after_complete()
            if request.user.bpmsuser.login in admin_userids:
                assignee_task_table = rest_client.get_tasks_info()
            else:
                assignee_task_table = rest_client.get_tasks_info(assignee=request.user.bpmsuser.login)
            next_tasks = [task for task in assignee_task_table if task['proc_instnc_id'] == proc_instnc_id]
            if len(next_tasks) == 1:
                next_task_id = next_tasks[0]['id']
                return HttpResponseRedirect(reverse("activeBPM:process-task")
                                     + '?instnc_id=%s&task_id=%s' % (proc_instnc_id, next_task_id))
            else:
                return HttpResponseRedirect(reverse("activeBPM:process-status") + '?instnc_id=%s' % proc_instnc_id)
        else:
            if request.user.bpmsuser.login in admin_userids:
                errors = task_form.errors
                return HttpResponse(str(errors))
            else:
                pass #error for users
    else:
        task_form = task_form_class()
    proc_template_folder = os.path.join(template_folder, 'proc_templates', proc['def_key'], '')
    default_template = 'activeBPM/proc_templates/default_process/process_init_default.html'
    task_tmpl = os.path.join(proc_template_folder, '%s__%s.html' % (proc['def_key'], 'init'))
    tmpl_dict = {'proc': proc, 'init_task_id': init_task_id}
    tmpl_dict['task_form'] = task_form
    try:
        return render(request, task_tmpl, tmpl_dict)
    except TemplateDoesNotExist:
        return render(request, default_template, tmpl_dict)


@login_required()
def proc_control_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    if request.method == "POST":
        instnc_id = request.POST['instnc_id']
        if request.POST['action'] == 'resume':
            rest_client.activate_proc(instnc_id)
            return HttpResponseRedirect(reverse('activeBPM:process-control'))
        elif request.POST['action'] == 'suspend':
            rest_client.suspend_proc(instnc_id)
            return HttpResponseRedirect(reverse('activeBPM:process-control'))
        elif request.POST['action'] == 'delete':
            rest_client.delete_proc(instnc_id)
            return HttpResponseRedirect(reverse('activeBPM:process-control'))

    active_proc_table = rest_client.get_proc_instncs_info_by_category(category, def_state='active',
                                                                                instnc_state='active')
    suspended_proc_table = rest_client.get_proc_instncs_info_by_category(category, def_state='active',
                                                                                instnc_state='suspended')
    admin_userids = rest_client.get_group_userids_by_group_name('admin')
    if request.user.bpmsuser.login in admin_userids:
        controled_active_proc_table = active_proc_table
        controled_suspended_proc_table = suspended_proc_table
    else:
        controled_active_proc_table = [proc for proc in active_proc_table
                                       if proc['initiator'] == request.user.bpmsuser.login]
        controled_suspended_proc_table = [proc for proc in suspended_proc_table
                                          if proc['initiator'] == request.user.bpmsuser.login]

    tmpl_dict = {
        'active_proc_table': controled_active_proc_table,
        'suspended_proc_table': controled_suspended_proc_table
    }
    return render(request, proc_control_template, tmpl_dict)


@login_required()
def task_control(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    task_id = request.POST['task_id']
    action = request.POST['action']
    if action == 'assign':
        proc_instnc_id = request.POST['instnc_id']
        rest_client.claim_task(task_id, request.user.bpmsuser.login)
        return HttpResponseRedirect(reverse('activeBPM:process-task')+'?instnc_id=%s&task_id=%s' % (proc_instnc_id,
                                                                                                    task_id))
    elif action == 'unassign':
        rest_client.resolve_task(task_id)
        return HttpResponseRedirect(reverse('activeBPM:process-dashboard'))


@csrf_exempt
@login_required()
def var_control(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    action = request.POST['action']
    if action == 'set_task_vars':
        task_id = request.POST['task_id']
        task_vars = {}
        for name, value in request.POST.items():
            if name.startswith('task_variables'):
                var_name = name[15:-1]
                task_vars[var_name] = value
        rest_client.set_task_vars(task_id, task_vars)
        return HttpResponse('ok')
    #elif action == 'get_task_vars':
    #    task_id = request.POST['task_id']
    #    task_var_names = request.POST['task_var_names']
    elif action == 'set_proc_vars':
        proc_id = request.POST['proc_id']
        proc_vars = {}
        for name, value in request.POST.items():
            if name.startswith('proc_variables'):
                var_name = name.lstrip('proc_variables[').rstrip(']')
                proc_vars[var_name] = value
        rest_client.set_task_vars(proc_id, proc_vars)
        return HttpResponse('ok')
    #elif action == 'get_proc_vars':
    #    pass


#TODO maybe refactor the same parts, put in class, make all login, etc
@login_required()
def proc_xml(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    proc_def_id = request.GET['def_id']
    proc_xml_content = rest_client.get_proc_def_xml(proc_def_id)
    return HttpResponse(proc_xml_content, content_type="text/plain; charset=utf-8")


def handle_uploaded_file(f, path, name):
    file_path = os.path.join(path, name)
    if not os.path.exists(path):
        os.makedirs(path)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


@login_required()
def file_control(request):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'upload_task_file':
            task = request.POST['task_id']
            proc = request.POST['instnc_id']  # empty if it is init task
            purpose = request.POST['purpose']
            for file in request.FILES.values():
                task_file = TaskFile(key=proc + '_' + task, file=file, purpose=purpose)
                task_file.save()
            return HttpResponse('ok')
        elif action == 'get_task_files_props':
            task = request.POST['task_id']
            proc = request.POST['instnc_id']
            purpose = request.POST['purpose']
            task_files = TaskFile.objects.filter(key=proc + '_' + task, purpose=purpose).order_by('pk')
            task_files_props = [{'name': ntpath.split(model.file.name)[1], 'file_pk': model.pk,
                                'size': model.file.size, 'purpose': model.purpose}
                                for model in task_files]
            return HttpResponse(json.dumps(task_files_props), content_type="application/json")
        elif action == 'delete_task_file':
            file_pk = request.POST['file_pk']
            TaskFile.objects.get(pk=file_pk).delete()
            return HttpResponse('ok')
        elif action == 'upload_file':
            folder_shortcut = request.POST['folder_shortcut']
            folder_path = os.path.join(folders_paths[folder_shortcut], request.POST['folder_path'], '')
            if 'filename' in request.POST:
                filename = request.POST['filename']
                chg_filename = None
            else:
                filename = None
                chg_filename = request.POST['chg_filename']
            for file in request.FILES.values():
                if filename:
                    handle_uploaded_file(file, folder_path, filename)
                else:
                    extension = os.path.splitext(file.name)[1]
                    chg_filename += extension
                    handle_uploaded_file(file, folder_path, chg_filename)
            return HttpResponse('ok')
        elif action == 'get_files_props':
            folder_shortcut = request.POST['folder_shortcut']
            folder_path = os.path.join(folders_paths[folder_shortcut], request.POST['folder_path'], '')
            tree = os.walk(folder_path)
            files_props = []
            for branch in tree:
                for filename in branch[2]:
                    file_path = os.path.join(branch[0], filename)
                    file_size = os.path.getsize(file_path)/1024
                    files_props.append({'name': filename, 'size': file_size,
                                        'folder_path': branch[0].replace(folder_path, '')})
            files_props.sort(key=lambda k: (k['folder_path'], k['name']))
            return HttpResponse(json.dumps(files_props), content_type="application/json")
        elif action == 'delete_file':
            folder_shortcut = request.POST['folder_shortcut']
            folder_path = os.path.join(folders_paths[folder_shortcut], request.POST['folder_path'], '')
            filename = request.POST['filename']
            file_path = os.path.join(folder_path,  filename)
            os.remove(file_path)
            if not os.listdir(folder_path):
                os.rmdir(folder_path)
            return HttpResponse('ok')

    elif request.method == 'GET':
        file_pk = request.GET['file_pk']
        task_file = TaskFile.objects.get(pk=file_pk).file
        #response = HttpResponse(task_file.file)
        #filename = ntpath.split(task_file.file.name)[1]
        #response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'%s' % filename
        return HttpResponseRedirect(settings.MEDIA_URL + task_file.name)


import zipfile
from django.core.files import File
import os
def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))


@login_required()
def zip_folder_task_file(request):
    task = request.POST['task_id']
    proc = request.POST['instnc_id']
    purpose = request.POST['purpose']
    folder_shortcut = request.POST['folder_shortcut']
    folder_path = os.path.join(folders_paths[folder_shortcut], request.POST['folder_path'], '')
    temp_folder = os.path.join(folders_paths[folder_shortcut], 'temp',  '')
    tempr_folder = os.path.join(temp_folder, proc + '_' + task, '')
    zip_file_path = os.path.join(tempr_folder, 'снимок_папки.zip')
    if not os.path.exists(tempr_folder):
        os.makedirs(tempr_folder)
    zipf = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    zipdir(folder_path, zipf)
    zipf.close()
    with open(zip_file_path, 'rb') as outfile:
        dj_file = File(outfile)
        task_file = TaskFile(key=proc + '_' + task, file=dj_file, purpose=purpose)
        task_file.save()
    os.remove(zip_file_path)
    os.rmdir(tempr_folder)
    #if not os.listdir(temp_folder):
    #    os.rmdir(temp_folder)
    return HttpResponse('ok')