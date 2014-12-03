__author__ = 'torn'

import requests
import json
from dateutil.parser import parse as date_parse
from activeBPM.models import TaskFile
import ntpath

class ActivityREST():
    """functions with simular name as in Activity user guide can return different results"""

    @staticmethod
    def rest_vars_to_dict(proc_vars):
        return {var['name']: var['value'] for var in proc_vars}

    @staticmethod
    def date_adapt(UTC_date):
        if UTC_date:
            return date_parse(UTC_date)
        else:
            return None

    def __init__(self, login, password, server='http://localhost:8080'):
        self.rest_url = server + '/activiti-rest/service/'
        self.session = requests.Session()
        self.session.auth = (login, password)
        self.session.headers.update({'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.proc_defs_url = self.rest_url + 'repository/process-definitions'
        self.proc_instncs_url = self.rest_url + 'runtime/process-instances'
        self.historic_proc_instncs_url = self.rest_url + 'history/historic-process-instances'
        self.tasks_url = self.rest_url + 'runtime/tasks'
        self.historic_tasks_url = self.rest_url + 'history/historic-task-instances'
        self.groups_url = self.rest_url + 'identity/groups'
        self.users_url = self.rest_url + 'identity/users'

    def get_user(self, user_id):
        user_req = self.session.get(self.users_url +'/%s' % user_id)
        return user_req.json()

    def get_group(self, group_id):
        group_req = self.session.get(self.groups_url + '/%s' % group_id)
        groups = group_req.json()
        return groups

    def get_task_groups_ids_by_task_id(self, task_id):
        identity_links_req = self.session.get(self.historic_tasks_url + '/%s/identitylinks' % task_id)
        identity_links = identity_links_req.json()
        groups_ids = [link['groupId'] for link in identity_links if link['groupId']]
        return groups_ids

    def get_group_users_by_group_name(self, group_name):
        GET_params = {'memberOfGroup': group_name}
        members_req = self.session.get(self.users_url, params=GET_params)
        members = members_req.json()['data']
        return members

    def get_group_userids_by_group_name(self, group_name):
        users = self.get_group_users_by_group_name(group_name)
        userids = [user['id'] for user in users]
        return userids

    def get_group_info(self, group_id):
        props = {}
        props['id'] = group_id
        group = self.get_group(props['id'])
        props['name'] = group['name']
        props['descr'] = group['type']
        return props

    def get_groups_info_by_task_id(self, task_id):
        groups_ids = self.get_task_groups_ids_by_task_id(task_id)
        groups_info = [self.get_group_info(group_id) for group_id in groups_ids]
        return groups_info

    def get_task(self, task_id):
        task_req = self.session.get(self.tasks_url + '/' + task_id)
        task = task_req.json()
        return task

    def get_historic_task(self, task_id, include_task_variables=True, include_process_variables=True):
        GET_params = {'includeTaskLocalVariables': include_task_variables,
                      'includeProcessVariables': include_process_variables, 'taskId': task_id}
        task_req = self.session.get(self.historic_tasks_url, params=GET_params)
        task = task_req.json()['data'][0]
        return task

    @staticmethod
    def get_task_files_props(task_id, proc_id, purpose):
        task_comment_files = TaskFile.objects.filter(key=proc_id + '_' + task_id,
                                                     purpose=purpose).order_by('pk')
        task_comment_files_props = [{'name': ntpath.split(model.file.name)[1], 'file_pk': model.pk,
                                     'size': model.file.size, 'purpose': model.purpose}
                                    for model in task_comment_files]
        return task_comment_files_props


    #add user_info
    def get_task_info(self, task_id):
        props = {}
        props['id'] = task_id
        historic_task = self.get_historic_task(props['id'])
        props['def_key'] = historic_task['taskDefinitionKey']
        props['name'] = historic_task['name']
        props['descr'] = historic_task['description']
        props['groups'] = self.get_groups_info_by_task_id(props['id'])
        props['assignee'] = historic_task['assignee']
        props['assignee_profile'] = self.get_user(props['assignee'])
        props['parent_task_id'] = historic_task['parentTaskId']
        props['start_time'] = self.date_adapt(historic_task['startTime'])
        if historic_task['claimTime']:
            props['assign_time'] = self.date_adapt(historic_task['claimTime'])
        else:
            props['assign_time'] = props['start_time']
        props['end_time'] = self.date_adapt(historic_task['endTime'])
        if props['assignee']:
            props['wait_time'] = props['assign_time'] - props['start_time']
        else:
            props['wait_time'] = None
        if props['assignee'] and props['end_time']:
            props['work_time'] = props['end_time'] - props['assign_time']
        else:
            props['work_time'] = None
        if props['end_time']:
            props['full_time'] = props['end_time'] - props['start_time']
        else:
            props['full_time'] = None
        props['proc_instnc_id'] = historic_task['processInstanceId']
        props['proc_def_id'] = historic_task['processDefinitionId']
        if props['end_time']:
            props['state'] = 'finished'
        elif props['assignee']:
            props['state'] = 'assigned'
        else:
            props['state'] = 'started'

        if props['end_time']:
            props['suspended'] = False
        else:
            task = self.get_task(props['id'])
            props['suspended'] = task['suspended']
        props['vars'] = self.rest_vars_to_dict(historic_task['variables'])
        props['comment_files'] = self.get_task_files_props(props['id'], props['proc_instnc_id'], 'comment')
        #change if problem with performance
        proc_def = self.get_proc_def(props['proc_def_id'])
        props['proc_name'] = proc_def['name']
        return props

    def get_task_ids_by_proc_instnc_id(self, proc_instnc_id):
        GET_args = {'processInstanceId': proc_instnc_id}
        historic_tasks_req = self.session.get(self.historic_tasks_url, params=GET_args)
        historic_tasks = historic_tasks_req.json()['data']
        task_ids = [task['id'] for task in historic_tasks]
        return task_ids

    def get_tasks_info_by_proc_instnc_id(self, proc_instnc_id):
        task_ids = self.get_task_ids_by_proc_instnc_id(proc_instnc_id)
        tasks_info = [self.get_task_info(task_id) for task_id in task_ids]
        return tasks_info

    def get_tasks_ids(self, assignee=None, candidate_user=None, only_active=True):
        GET_args = {'active': only_active}
        if candidate_user:
            GET_args['candidateUser'] = candidate_user
        if assignee:
            GET_args['assignee'] = assignee
        tasks_req = self.session.get(self.tasks_url, params=GET_args)
        tasks = tasks_req.json()['data']
        tasks_ids = [task['id'] for task in tasks]
        return tasks_ids

    def get_tasks_info(self, assignee=None, candidate_user=None, only_active=True):
        tasks_ids = self.get_tasks_ids(assignee=assignee, candidate_user=candidate_user, only_active=only_active)
        tasks_info = [self.get_task_info(task_id) for task_id in tasks_ids]
        return tasks_info


    def complete_task(self, task_id):
        POST_args = json.dumps({'action': 'complete'})
        complete_task_req = self.session.post(self.tasks_url + '/%s' % task_id, data=POST_args)

    def claim_task(self, task_id, assignee):
        POST_args = json.dumps({'action': 'claim', "assignee": assignee})
        claim_task_req = self.session.post(self.tasks_url + '/%s' % task_id, data=POST_args)

    def resolve_task(self, task_id):
        POST_args = json.dumps({'action': 'resolve'})
        resolve_task_req = self.session.post(self.tasks_url + '/%s' % task_id, data=POST_args)

    def create_task_vars(self, task_id, local_vars):
        var_list = []
        for name, value in local_vars.items():
            var_list.append([{'name': name, 'value': str(value), 'scope': 'local', 'type': 'string'}])
        for var in var_list:
            json_var = json.dumps(var)
            set_var_req = self.session.post(self.tasks_url + '/%s/variables' % task_id, data=json_var)

    def update_task_vars(self, task_id, local_vars):
        var_list = []
        for name, value in local_vars.items():
            var_list.append({'name': name, 'value': str(value), 'scope': 'local', 'type': 'string'})
        for var in var_list:
            json_var = json.dumps(var)
            set_var_req = self.session.put(self.tasks_url + '/%s/variables/%s' % (task_id, var['name']), data=json_var)

    def set_task_vars(self, task_id, local_vars):
        self.create_task_vars(task_id, local_vars)
        self.update_task_vars(task_id, local_vars)

    def get_proc_def(self, proc_def_id):
        proc_def_req = self.session.get(self.proc_defs_url + '/' + proc_def_id)
        proc_def = proc_def_req.json()
        return proc_def

    def get_proc_def_info(self, proc_def_id):
        props = {}
        props['def_id'] = proc_def_id
        proc_def = self.get_proc_def(props['def_id'])
        props['def_key'] = proc_def['key']
        props['def_ver'] = proc_def['version']
        props['category'] = proc_def['category']
        props['name'] = proc_def['name']
        props['descr'] = proc_def['description']
        if proc_def['suspended']:
            props['def_state'] = 'suspended'
        else:
            props['def_state'] = 'active'
        return props

    def get_proc_defs_ids_by_category(self, category=None, def_state=None, latest_def=None, startable_by_user=None):
        proc_defs_query = {}
        if category:
            proc_defs_query['category'] = category
        if def_state == 'suspended':
            proc_defs_query['suspended'] = True
        elif def_state == 'active':
            proc_defs_query['suspended'] = False
        if startable_by_user:
            proc_defs_query['startableByUser'] = startable_by_user
        if latest_def:
            proc_defs_query['latest'] = latest_def

        proc_defs_req = self.session.get(self.proc_defs_url, params=proc_defs_query)
        proc_defs = proc_defs_req.json()['data']
        proc_defs_ids = [proc_def['id'] for proc_def in proc_defs]
        return proc_defs_ids

    def get_proc_defs_info_by_category(self, category=None, def_state=None, latest_def=None, startable_by_user=None):
        defs_ids = self.get_proc_defs_ids_by_category(category, def_state, latest_def, startable_by_user)
        defs_info = [self.get_proc_def_info(proc_def_id) for proc_def_id in defs_ids]
        return defs_info

    #no vars if need vars then do like get_proc_historic_instnc
    def get_proc_instnc(self, instnc_id):
        proc_instnc_req = self.session.get(self.proc_instncs_url + '/' + instnc_id)
        proc_instnc = proc_instnc_req.json()
        return proc_instnc

    def get_proc_historic_instnc(self, instnc_id, include_variables=True):
        GET_args = {'includeProcessVariables': include_variables, 'processInstanceId': instnc_id}
        proc_instnc_req = self.session.get(self.historic_proc_instncs_url, params=GET_args)
        historic_proc_instance = proc_instnc_req.json()['data'][0]
        return historic_proc_instance

    def get_proc_instnc_info(self, instnc_id):
        props = {}
        props['instnc_id'] = instnc_id
        historic_instnc = self.get_proc_historic_instnc(props['instnc_id'])
        props['initiator'] = historic_instnc['startUserId']
        props['initiator_profile'] = self.get_user(props['initiator'])
        props['def_id'] = historic_instnc['processDefinitionId']
        props['vars'] = self.rest_vars_to_dict(historic_instnc['variables'])
        props['start_time'] = self.date_adapt(historic_instnc['startTime'])
        props['end_time'] = self.date_adapt(historic_instnc['endTime'])
        if props['end_time']:
            props['full_time'] = props['end_time'] - props['start_time']
        else:
            props['full_time'] = None
        if historic_instnc['endTime']:
            props['state'] = 'finished'
        else:
            instnc = self.get_proc_instnc(props['instnc_id'])
            if instnc['suspended']:
                props['state'] = 'suspended'
            else:
                props['state'] = 'active'
        props.update(self.get_proc_def_info(props['def_id']))

        init_task = {'id': props['instnc_id'] + '_init',  #maybe put in get tasks
                     'name': 'Начало процесса',
                     'def_key': 'startevent',
                     'start_time': None,
                     'end_time': props['start_time'],
                     'assign_time': None,
                     'work_time': None,
                     'full_time': None,
                     'assignee': props['initiator'],
                     'assignee_profile': props['initiator_profile'],
                     'vars': {'task_comment': props['vars']['task_comment']},
                     'comment_files': self.get_task_files_props('init', props['instnc_id'], 'comment')}

        instnc_tasks = self.get_tasks_info_by_proc_instnc_id(props['instnc_id'])
        props['finished_tasks'] = [init_task] + [task for task in instnc_tasks if task['state'] == 'finished']
        props['active_tasks'] = [task for task in instnc_tasks if task['state'] != 'finished']
        return props

    def get_proc_instncs_ids_by_def_id(self, def_id, instnc_state=None, quantity_per_def=None):
        proc_instncs_query = {'processDefinitionId': def_id}
        if instnc_state == 'finished':
            proc_instncs_query['finished'] = True
            if quantity_per_def:
                proc_instncs_query.update({'size': quantity_per_def,  'order': 'desc', 'sort': 'endTime'})
            instncs_req = self.session.get(self.historic_proc_instncs_url, params=proc_instncs_query)
        else:
            if instnc_state == 'suspended':
                proc_instncs_query['suspended'] = True
            elif instnc_state == 'active':
                proc_instncs_query['suspended'] = False
            instncs_req = self.session.get(self.proc_instncs_url, params=proc_instncs_query)

        proc_instncs = instncs_req.json()['data']
        proc_instncs_ids = [proc_instnc['id'] for proc_instnc in proc_instncs]
        return proc_instncs_ids

    def get_proc_instncs_ids_by_category(self, category=None, def_state=None, latest_def=None,
                                         instnc_state=None,
                                         quantity_per_def=None):
        proc_defs_ids = self.get_proc_defs_ids_by_category(category, def_state, latest_def)
        proc_instncs_ids = []
        for def_id in proc_defs_ids:
            proc_instncs_ids += self.get_proc_instncs_ids_by_def_id(def_id, instnc_state, quantity_per_def)
        return proc_instncs_ids

    def get_proc_instncs_info_by_category(self, category=None, def_state=None, instnc_state=None,
                                          quantity_per_def=None,
                                          latest_def=None):
        proc_instncs_ids = self.get_proc_instncs_ids_by_category(category=category, def_state=def_state,
                                                                 instnc_state=instnc_state,
                                                                 quantity_per_def=quantity_per_def,
                                                                 latest_def=latest_def)
        proc_instncs_info = [self.get_proc_instnc_info(instnc_id) for instnc_id in proc_instncs_ids]
        return proc_instncs_info

    def get_proc_def_xml(self, proc_defenition_id):
        proc_def = self.get_proc_def(proc_defenition_id)
        proc_depl_resource = self.session.get(proc_def['resource']).json()
        proc_xml = self.session.get(proc_depl_resource['contentUrl']).text
        return proc_xml

    def start_proc(self, proc_defenition_id, proc_vars):
        var_list = []
        for name, value in proc_vars.items():
            var_list.append({'name': name, 'value': str(value), 'type': 'string'})
        POST_args = json.dumps({'processDefinitionId': proc_defenition_id, 'variables': var_list})
        proc_start_req = self.session.post(self.proc_instncs_url, data=POST_args)
        proc_instnc = proc_start_req.json()
        return proc_instnc

    def activate_proc(self, proc_instnc_id):
        PUT_args = json.dumps({'action': 'activate'})
        proc_activate_req = self.session.put(self.proc_instncs_url + '/' + proc_instnc_id, data=PUT_args)

    def suspend_proc(self, proc_instnc_id):
        PUT_args = json.dumps({'action': 'suspend'})
        proc_suspend_req = self.session.put(self.proc_instncs_url + '/' + proc_instnc_id, data=PUT_args)

    def delete_proc(self, proc_instnc_id):
        proc_delete_req = self.session.delete(self.proc_instncs_url + '/' + proc_instnc_id)

    def create_proc_vars(self, instnc_id, proc_vars):
        var_list = []
        for name, value in proc_vars.items():
            var_list.append([{'name': name, 'value': str(value), 'type': 'string'}])
        for var in var_list:
            json_var = json.dumps(var)
            create_var_req = self.session.post(self.proc_instncs_url + '/%s/variables' % instnc_id, data=json_var)

    def update_proc_vars(self, instnc_id, proc_vars):
        var_list = []
        for name, value in proc_vars.items():
            var_list.append([{'name': name, 'value': str(value), 'type': 'string'}])
        for var in var_list:
            json_var = json.dumps(var)
            set_var_req = self.session.put(self.proc_instncs_url + '/%s/variables' % instnc_id, data=json_var)

    def set_proc_vars(self, instnc_id, proc_vars):
        self.create_proc_vars(instnc_id, proc_vars)
        self.update_proc_vars(instnc_id, proc_vars)