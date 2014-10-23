from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from moldslist.activiti_api import ActivityREST
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from moldslist import molds_process_forms
from moldslist.models import TaskFile
from dateutil.parser import parse as date_parse
from django.template import TemplateDoesNotExist
import json

def proc_vars_to_dict(proc_vars):
    return {var['name']: var['value'] for var in proc_vars}

def get_task_groups(rest_client, task_id):
    task_groups_ids = rest_client.get_task_groups_ids(task_id)
    task_groups = [rest_client.get_group(group_id)['name'] for group_id in task_groups_ids]
    return task_groups



#TODO change place with mold name and number
#TODO add proc has variable "mold" check
#TODO add rajise if another not from three stuses
def get_proc_table(rest_client, status='active'):
    if status == 'active':
        dashbord_proc_instances = rest_client.get_proc_instances(category='Molds', suspended_instnc=False)
    elif status == 'suspended':
        dashbord_proc_instances = rest_client.get_proc_instances(category='Molds', suspended_instnc=True)
    elif status == 'finished':
        dashbord_proc_instances = rest_client.get_historic_proc_instances(category='Molds')

    dashbord_table = []
    for proc in dashbord_proc_instances:
        name = rest_client.get_proc_definition(proc['processDefinitionId'])['name']
        try:
            mold_name = proc_vars_to_dict(proc['variables'])['mold_name']
            mold_number = proc_vars_to_dict(proc['variables'])['mold_number']
        except KeyError:
            mold_name = '-'
            mold_number = '-'
        active_tasks = rest_client.get_proc_tasks(proc['id'])
        #TODO rewrite


        active_tasks_repr = []
        for task in active_tasks:
            historic_task = rest_client.get_historic_task(task['id'])
            assignment_time = historic_task['claimTime']
            task_row = {
                'name': task['name'],
                'assignee': task['assignee'],
                'id': task['id'],
                'create_time': task['createTime'],
                'assignment_time': assignment_time,
                'groups': get_task_groups(rest_client, task['id'])
                         }
            active_tasks_repr.append(task_row)

        row_dict = {'name': name, 'mold_name': mold_name, 'mold_number': mold_number,
                            'tasks': active_tasks_repr, 'id': proc['id']}

        #TODO rewrite
        historic_proc = rest_client.get_historic_proc_instance(proc['id'])
        row_dict['start_time'] = date_parse(historic_proc['startTime'])
        if status == 'finished':
            row_dict['finish_time'] = date_parse(proc['endTime'])
            row_dict['time_spend'] = date_parse(proc['endTime']) - date_parse(proc['startTime'])
        dashbord_table.append(row_dict)
    return dashbord_table


def get_assignee_task_table(rest_client, candidate, active_molds_proc_table):
    candidate_tasks = rest_client.get_candidate_tasks(candidate)
    candidate_task_ids = [task['id'] for task in candidate_tasks]
    task_table = []

    for proc in active_molds_proc_table:
        for task in proc['tasks']:
            if task['id'] in candidate_task_ids or task['assignee'] == candidate:
                task_row = {'name': proc['name'], 'mold_name': proc['mold_name'], 'mold_number': proc['mold_number'], 'task': task, 'id': proc['id']}
                task_table.append(task_row)
    return task_table


#TODO add a web account existance check
#TODO add a user group check if will be other modules than molds
#TODO add right permissions to admin and other groups
#TODO add a process sort by last state change
#TODO localization
@login_required()
def dashboard(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)

    active_molds_proc_table = get_proc_table(rest_client)
    assignee_task_table = get_assignee_task_table(rest_client, request.user.bpmsuser.login, active_molds_proc_table)
    finished_molds_proc_table = reversed(get_proc_table(rest_client, status='finished'))

    available_proc_list = rest_client.get_proc_definitions(category="Molds", startableByUser=request.user.bpmsuser.login, latest=True)

    tmpl_dict = {'active_molds_proc_table': active_molds_proc_table,
                 'finished_molds_proc_table': finished_molds_proc_table,
                 'assignee_task_table': assignee_task_table,
                 'available_proc_list': available_proc_list}
    return render(request, 'moldslist/dashboard.html', tmpl_dict)

@login_required()
def allprocesses(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)

    active_molds_proc_table = get_proc_table(rest_client)
    suspended_molds_proc_table = reversed(get_proc_table(rest_client, status='suspended'))
    finished_molds_proc_table = reversed(get_proc_table(rest_client, status='finished'))

    tmpl_dict = {
        'active_molds_proc_table': active_molds_proc_table,
        'finished_molds_proc_table': finished_molds_proc_table,
        'suspended_molds_proc_table': suspended_molds_proc_table,
        }

    return render(request, 'moldslist/allprocesses.html', tmpl_dict)





#TODO check if there a GET paramters
#TODO add proc has variable "mold" check
def get_proc_status_dict(rest_client, proc_instnc_id):
    proc_historic_instnc = rest_client.get_historic_proc_instance(proc_instnc_id)
    if proc_historic_instnc['endTime']:
        proc_status = 'finished'
        proc_instnc = proc_historic_instnc
    else:
        proc_instnc = rest_client.get_proc_instance(proc_instnc_id)
        if proc_instnc['suspended']:
            proc_status = 'suspended'
        else:
            proc_status = 'active'



    proc_def_id = proc_instnc['processDefinitionId']
    proc_def = rest_client.get_proc_definition(proc_def_id)

    active_tasks = rest_client.get_proc_tasks(proc_instnc_id)
    for task in active_tasks:
        task['groups'] = get_task_groups(rest_client, task['id'])
        task['assignment_time'] = rest_client.get_historic_task(task['id'])['claimTime']


    finished_tasks = rest_client.get_proc_historic_tasks(proc_instnc_id)
    for task in finished_tasks:
        task['time_spend'] = task['startTime'] - task['endTime']
        task['task_comment'] = proc_vars_to_dict(task['variables'])['task_comment']

    try:
        mold_name = proc_vars_to_dict(proc_instnc['variables'])['mold_name']
        mold_number = proc_vars_to_dict(proc_instnc['variables'])['mold_number']
    except:
        mold_name = '-'
        mold_number = '-'

    tmpl_dict = {'proc_name': proc_def['name'], 'proc_def_id': proc_def_id,
                 'proc_status': proc_status,
                 'active_tasks': active_tasks, 'finished_tasks': finished_tasks,
                 'mold_name': mold_name, 'mold_number': mold_number,
                 'proc_help_text': str(proc_def['description'])
                 }
    return tmpl_dict


@login_required()
def proc_status_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    proc_instnc_id = request.GET['id']
    tmpl_dict = get_proc_status_dict(rest_client, proc_instnc_id)
    return render(request, 'moldslist/proc_base.html', tmpl_dict)


#TODO caeck if task is a task of right user and process is active
@login_required()
def proc_task_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)

    proc_instnc_id = request.REQUEST['proc']

    proc_historic_instnc = rest_client.get_historic_proc_instance(proc_instnc_id)
    if proc_historic_instnc['endTime']:
        proc_status = 'finished'
        proc_instnc = proc_historic_instnc
    else:
        proc_instnc = rest_client.get_proc_instance(proc_instnc_id)
        if proc_instnc['suspended']:
            proc_status = 'suspended'
        else:
            proc_status = 'active'


    task_id = request.REQUEST['task']
    task_historic_instnc = rest_client.get_historic_task(task_id)
    if task_historic_instnc['endTime']:
        task_status = 'finished'
        task = task_historic_instnc
    else:
        task = rest_client.get_task(task_id)
        if task['assignee']:
            task_status = 'assigned'
        else:
            task_status = 'unassigned'

    proc_def_id = proc_instnc['processDefinitionId']
    proc_def = rest_client.get_proc_definition(proc_def_id)
    try:
        task_form_class = getattr(molds_process_forms, '%s__%s' % (proc_def['key'], task['taskDefinitionKey']))
    except AttributeError:
         task_form_class = getattr(molds_process_forms, 'MoldProcessInitDefault')

    if request.method == 'POST':
        task_form = task_form_class(request.POST)
        if task_form.is_valid():
            data = task_form.cleaned_data
            rest_client.create_task_vars(task_id, data)
            rest_client.complete_task(task_id)
            return HttpResponseRedirect(reverse("moldslist:process-status") + '?id=%s' % proc_instnc_id)
    else:
        task_form = task_form_class()

    default_template = 'task_templates/mold_task_default.html'
    proc_template_folder = 'task_templates/%s/' % proc_def['key']
    task_tmpl = proc_template_folder + '%s__%s.html' % (proc_def['key'], task['taskDefinitionKey'])

    tmpl_dict = get_proc_status_dict(rest_client, proc_instnc_id)
    tmpl_dict['task_def_key'] = task['taskDefinitionKey']
    tmpl_dict['task_form'] = task_form
    tmpl_dict['task_help_text'] = task['description']
    tmpl_dict['task_name'] = task['name']
    tmpl_dict['task_assignee'] = task['assignee']
    tmpl_dict['task_groups'] = get_task_groups(rest_client, task_id)
    tmpl_dict['task_status'] = task_status

    try:
        return render(request, task_tmpl, tmpl_dict)
    except TemplateDoesNotExist:
        return render(request, default_template, tmpl_dict)



def proc_init_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    proc_def_id = request.REQUEST['id']
    proc_def = rest_client.get_proc_definition(proc_def_id)

    try:
        task_form_class = getattr(molds_process_forms, '%s__%s' % (proc_def['key'], 'init'))
    except AttributeError:
        task_form_class = getattr(molds_process_forms, 'MoldTaskDefault')

    if request.method == 'POST':
        task_form = task_form_class(request.POST)
        if task_form.is_valid():
            data = task_form.cleaned_data
            proc_instnc_id = rest_client.start_proc(proc_def_id)['id']
            rest_client.create_proc_vars(proc_instnc_id, data)
            return HttpResponseRedirect(reverse("moldslist:process-status") + '?id=%s' % proc_instnc_id)
    else:
        task_form = task_form_class()

    default_template = 'task_templates/mold_process_init_default.html'
    proc_template_folder = 'task_templates/%s/' % proc_def['key']
    task_tmpl = proc_template_folder + '%s__%s.html' % (proc_def['key'], 'init')

    tmpl_dict = {'proc_name': proc_def['name'], 'proc_def_id': proc_def_id}
    tmpl_dict['task_form'] = task_form
    try:
        return render(request, task_tmpl, tmpl_dict)
    except TemplateDoesNotExist:
        return render(request, default_template, tmpl_dict)


@login_required()
def proc_control(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)


    #proc_instnc = rest_client.get_proc_instance(proc_instnc_id)

    if request.method == "POST":
        proc_instnc_id = request.POST['id']
        if request.POST['action'] == 'resume':
            rest_client.activate_proc(proc_instnc_id)
            return HttpResponseRedirect(reverse('moldslist:process-control'))
        elif request.POST['action'] == 'suspend':
            rest_client.suspend_proc(proc_instnc_id)
            return HttpResponseRedirect(reverse('moldslist:process-control'))
        elif request.POST['action'] == 'delete':
            rest_client.delete_proc(proc_instnc_id)
            return HttpResponseRedirect(reverse('moldslist:process-control'))


    #elif request.REQUEST['action'] == 'change_variables':
    #    pass

    active_molds_proc_table = get_proc_table(rest_client)
    suspended_molds_proc_table = reversed(get_proc_table(rest_client, status='suspended'))

    tmpl_dict = {
        'active_molds_proc_table': active_molds_proc_table,
        'suspended_molds_proc_table': suspended_molds_proc_table,
        }

    return render(request, 'moldslist/proc_control.html', tmpl_dict)


@login_required()
def task_control(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    task_id = request.POST['task_id']
    action = request.POST['action']
    if action == 'assign':
        proc_id = request.POST['proc_id']
        rest_client.claim_task(task_id, request.user.bpmsuser.login)
        return HttpResponseRedirect(reverse('moldslist:process-task')+'?proc=%s&task=%s' % (proc_id, task_id))
    elif action == 'unassign':
        rest_client.resolve_task(task_id)
        return HttpResponseRedirect(reverse('moldslist:dashboard'))


#TODO maybe refactor the same parts, put in class, make all login, etc
@login_required()
def proc_xml(request):

    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)

    proc_def_id = request.GET['id']
    proc_xml = rest_client.get_proc_xml(proc_def_id)

    return HttpResponse(proc_xml, content_type="text/plain; charset=utf-8")


def file_control(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)



    if request.method == 'POST':
        if 'task' in request.POST:
            task = request.POST['task']
        else:
            task = 'init'
        proc = request.POST['proc']

        if request.POST['action'] == 'upload_comment_file':
            for file in request.FILES.values():
                task_file = TaskFile(key=proc + '_' + task, file=file)
                task_file.save()
            return HttpResponse('ok')
        elif request.POST['action'] == 'get_task_comment_files_descr':
            task_files = TaskFile.objects.filter(key=proc + '_' + task).order_by('pk')
            task_files_descr = [(model.pk, model.file.name.split('/')[-1], model.file.size) for model in task_files]
            return HttpResponse(json.dumps(task_files_descr), content_type="application/json")
        elif request.POST['action'] == 'delete_task_file':
            pk = request.POST['pk']
            TaskFile.objects.get(pk=pk).delete()
            return HttpResponse('ok')


    elif request.method == 'GET':
        pk = request.GET['pk']
        task_file = TaskFile.objects.get(pk=pk)
        response = HttpResponse(task_file.file)
        response['Content-Disposition'] = 'attachment; filename=' + task_file.file.name
        return response
