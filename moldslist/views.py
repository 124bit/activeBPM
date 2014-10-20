from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from moldslist.activiti_api import ActivityREST
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from moldslist import proc_forms
from dateutil.parser import parse as date_parse
def proc_vars_to_dict(proc_vars):
    return {var['name']: var['value'] for var in proc_vars}

#TODO change place with mold name and number
#TODO add proc has variable "mold" check
def get_proc_table(rest_client, active=True):
    if active:
        dashbord_proc_instances = rest_client.get_proc_instances(category='Molds')
    else:
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
        #TODO rewSright
        active_tasks_repr = [{'name': task['name'], 'assignee': task['assignee'],
                              'id': task['id'],
                              'assigment_time': task['createTime']}
                             for task in active_tasks]

        row_dict = {'name': name, 'mold_name': mold_name, 'mold_number': mold_number,
                            'tasks': active_tasks_repr, 'id': proc['id']}
        if not active:
            row_dict['finish_time'] = date_parse(proc['endTime'])
            row_dict['time_spend'] = date_parse(proc['endTime']) - date_parse(proc['startTime'])
        dashbord_table.append(row_dict)
    return dashbord_table


def get_assignee_task_table(molds_proc_table, assignee):
    task_table = []
    for proc in molds_proc_table:
        for task in proc['tasks']:
            if task['assignee'] == assignee:
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
    assignee_task_table = get_assignee_task_table(active_molds_proc_table, request.user.bpmsuser.password)
    finished_molds_proc_table = reversed(get_proc_table(rest_client, active=False))

    available_proc_list = rest_client.get_proc_definitions(category="Molds", startableByUser=request.user.bpmsuser.login)

    tmpl_dict = {'active_molds_proc_table': active_molds_proc_table,
                 'finished_molds_proc_table': finished_molds_proc_table,
                 'assignee_task_table': assignee_task_table,
                 'available_proc_list': available_proc_list}
    return render(request, 'moldslist/dashboard.html', tmpl_dict)


#TODO check if there a GET paramters
#TODO add proc has variable "mold" check
def get_proc_status_dict(rest_client, proc_instnc_id):
    proc_historic_instnc = rest_client.get_historic_proc_instance(proc_instnc_id)
    if proc_historic_instnc['endTime']:
        proc_is_active = False
        proc_instnc = proc_historic_instnc
    else:
        proc_is_active = True
        proc_instnc = rest_client.get_proc_instance(proc_instnc_id)

    proc_def_id = proc_instnc['processDefinitionId']
    proc_def = rest_client.get_proc_definition(proc_def_id)

    active_tasks = rest_client.get_proc_tasks(proc_instnc_id)
    finished_tasks = rest_client.get_proc_historic_tasks(proc_instnc_id)
    for task in finished_tasks:
        task['time_spend'] = task['startTime'] - task['endTime']

    try:
        mold_name = proc_vars_to_dict(proc_instnc['variables'])['mold_name']
        mold_number = proc_vars_to_dict(proc_instnc['variables'])['mold_number']
    except:
        mold_name = '-'
        mold_number = '-'

    tmpl_dict = {'proc_name': proc_def['name'], 'proc_def_id': proc_def_id,
                 'proc_is_active': proc_is_active,
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
    proc_instnc = rest_client.get_proc_instance(proc_instnc_id)

    task_id = request.REQUEST['task']
    task = rest_client.get_task(task_id)

    proc_def_id = proc_instnc['processDefinitionId']
    proc_def = rest_client.get_proc_definition(proc_def_id)

    task_form_class = getattr(proc_forms, '%s__%s' % (proc_def['key'], task['taskDefinitionKey']))

    if request.method == 'POST':
        task_form = task_form_class(request.POST)
        if task_form.is_valid():
            data = task_form.cleaned_data
            rest_client.create_task_vars(task_id, data)
            rest_client.complete_task(task_id)
            return HttpResponseRedirect(reverse("moldslist:process-status") + '?id=%s' % proc_instnc_id)
    else:
        task_form = task_form_class()

    proc_template_folder = 'task_templates/%s/' % proc_def['key']
    task_tmpl = proc_template_folder + '%s__%s.html' % (proc_def['key'], task['taskDefinitionKey'])

    tmpl_dict = get_proc_status_dict(rest_client, proc_instnc_id)
    tmpl_dict['task_def_key'] = task['taskDefinitionKey']
    tmpl_dict['task_form'] = task_form
    tmpl_dict['task_template'] = task_tmpl
    tmpl_dict['task_help_text'] = task['description']
    tmpl_dict['task_name'] = task['name']

    return render(request, 'moldslist/proc_task.html', tmpl_dict)


def proc_init_view(request):
    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
    proc_def_id = request.REQUEST['id']
    proc_def = rest_client.get_proc_definition(proc_def_id)

    task_form_class = getattr(proc_forms, '%s__%s' % (proc_def['key'], 'init'))

    if request.method == 'POST':
        task_form = task_form_class(request.POST)
        if task_form.is_valid():
            data = task_form.cleaned_data
            proc_instnc_id = rest_client.start_proc(proc_def_id)['id']
            rest_client.create_proc_vars(proc_instnc_id, data)
            return HttpResponseRedirect(reverse("moldslist:process-status") + '?id=%s' % proc_instnc_id)
    else:
        task_form = task_form_class()

    proc_template_folder = 'task_templates/%s/' % proc_def['key']
    task_tmpl = proc_template_folder + '%s__%s.html' % (proc_def['key'], 'init')



    tmpl_dict = {'proc_name': proc_def['name'], 'proc_def_id': proc_def_id}
    tmpl_dict['task_form'] = task_form
    tmpl_dict['task_template'] = task_tmpl

    return render(request, 'moldslist/proc_init.html', tmpl_dict)

# @login_required()
# def proc_control(request):
#     rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)
#
#     proc_def_id = request.GET['id']
#     proc_def = rest_client.get_proc_definition(proc_def_id)
#
#     tmpl_dict = {'proc_name': proc_def['name']}
#
#     if request.GET['action'] == 'init':
#
#         tmpl_dict['form_template'] = proc_def['key'] + '.html'
#
#         return render(request, 'moldslist/proc_init.html', tmpl_dict)
#
#     if request.GET['action'] == 'start':
#         #start
#         return HttpResponseRedirect(reverse('moldslist:dashboard'))


#TODO maybe refactor the same parts, put in class, make all login, etc
@login_required()
def proc_xml(request):

    rest_client = ActivityREST(request.user.bpmsuser.login, request.user.bpmsuser.password)

    proc_def_id = request.GET['id']
    proc_xml = rest_client.get_proc_xml(proc_def_id)

    return HttpResponse(proc_xml, content_type="text/plain")


