__author__ = 'torn'

import requests
import json
from dateutil.parser import parse as date_parse

class ActivityREST():
    """functions with simular name as in Activity user guide can return different results"""
    def __init__(self, login, password, server='http://localhost:8080'):

        self.rest_url = server + '/activiti-rest/service/'
        self.session = requests.Session()
        self.session.auth = (login, password)
        self.session.headers.update({'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.proc_defenitions_url = self.rest_url + 'repository/process-definitions'
        self.proc_instances_url = self.rest_url + 'runtime/process-instances'
        self.historic_proc_instances_url = self.rest_url + 'history/historic-process-instances'
        self.tasks_url = self.rest_url + 'runtime/tasks'
        self.historic_tasks_url = self.rest_url + 'history/historic-task-instances'



    def get_proc_definition(self, proc_defenition_id):
        proc_def_req = self.session.get(self.proc_defenitions_url + '/' + proc_defenition_id)
        return proc_def_req.json()

    def get_proc_definitions(self, **kwargs):
        proc_defs_req = self.session.get(self.proc_defenitions_url, params=kwargs)
        return proc_defs_req.json()['data']

    def get_proc_xml(self, proc_defenition_id):
        proc_def = self.get_proc_definition(proc_defenition_id)
        proc_depl_resource = self.session.get(proc_def['resource']).json()
        proc_xml = self.session.get(proc_depl_resource['contentUrl']).text
        return proc_xml

    def get_proc_instance(self, instnc_id):
        proc_instnc_req = self.session.get(self.proc_instances_url + '/' + instnc_id)
        return proc_instnc_req.json()

    def get_proc_instances(self, category=None, suspended_instnc=None, suspended_def=None, include_proc_vars=True):
        proc_defs_query = {}
        if category:
            proc_defs_query['category'] = category
        if suspended_def == False or suspended_def == True:
            proc_defs_query['suspended'] = suspended_def


        proc_defs = self.get_proc_definitions(**proc_defs_query)
        proc_defs_ids = [proc['id'] for proc in proc_defs]

        proc_category_instncs = []
        for id in proc_defs_ids:
            proc_defs_instncs_query = {'processDefinitionId': id, 'includeProcessVariables': include_proc_vars}
            if suspended_instnc == False or suspended_instnc == True:
                proc_defs_instncs_query['suspended'] = suspended_instnc
            proc_defs_instncs_req = self.session.get(self.proc_instances_url, params=proc_defs_instncs_query)
            proc_def_instncs = proc_defs_instncs_req.json()['data']
            proc_category_instncs += proc_def_instncs
        return proc_category_instncs

    def get_proc_instnc_diagram(self, instnc_id):
        return self.proc_instances_url + '/%s/diagram' % instnc_id

    def start_proc(self, proc_defenition_id):
        POST_args = json.dumps({'processDefinitionId': proc_defenition_id})
        proc_start_req = self.session.post(self.proc_instances_url, data=POST_args)
        return proc_start_req.json()

    def activate_proc(self, proc_instnc_id):
        PUT_args = json.dumps({'action': 'activate'})
        proc_activate_req = self.session.put(self.proc_instances_url + '/' + proc_instnc_id, data=PUT_args)

    def suspend_proc(self, proc_instnc_id):
        PUT_args = json.dumps({'action': 'suspend'})
        proc_suspend_req = self.session.put(self.proc_instances_url + '/' + proc_instnc_id, data=PUT_args)
        return 1

    def delete_proc(self, proc_instnc_id):
        proc_delete_req = self.session.delete(self.proc_instances_url + '/' + proc_instnc_id)



    def create_proc_vars(self, instnc_id, proc_vars):
        var_list = []
        for name, value in proc_vars.items():
            var_list.append({'name': name, 'value': str(value), 'scope': 'local', 'type': 'string'})
        json_var_list = json.dumps(var_list)
        create_vars_req = self.session.post(self.proc_instances_url + '/%s/variables' % instnc_id, data=json_var_list)
        return create_vars_req.json()

    def get_historic_proc_instance(self, instnc_id):
        proc_instnc_req = self.session.get(self.historic_proc_instances_url + '/' + instnc_id)
        return proc_instnc_req.json()

    def get_historic_proc_instances(self, category=None, suspended_def=None, include_proc_vars=True, finished=True):
        proc_defs_query = {}
        if category:
            proc_defs_query['category'] = category
        if suspended_def == False or suspended_def == True:
            proc_defs_query['suspended'] = suspended_def

        proc_defs = self.get_proc_definitions(**proc_defs_query)
        proc_defs_ids = [proc['id'] for proc in proc_defs]

        historic_proc_category_instncs = []
        for id in proc_defs_ids:
            proc_defs_instncs_query = {'processDefinitionId': id, 'includeProcessVariables': include_proc_vars}
            if finished:
                proc_defs_instncs_query['finished'] = finished
            proc_defs_instncs_req = self.session.get(self.historic_proc_instances_url, params=proc_defs_instncs_query)
            proc_def_instncs = proc_defs_instncs_req.json()['data']
            historic_proc_category_instncs += proc_def_instncs
        return historic_proc_category_instncs

    def get_task(self, task_id):
        tasks_req = self.session.get(self.tasks_url + '/' + task_id)
        task = tasks_req.json()
        task['createTime'] = date_parse(task['createTime'])
        return task

    def get_proc_tasks(self, proc_instance_id):
        GET_args = {'processInstanceId': proc_instance_id}
        tasks_req = self.session.get(self.tasks_url, params=GET_args)
        tasks = tasks_req.json()['data']
        for task in tasks:
            task['createTime'] = date_parse(task['createTime'])
        return tasks

    def create_task_vars(self, task_id, local_vars):
        var_list = []
        for name, value in local_vars.items():
            var_list.append({'name': name, 'value': str(value), 'scope': 'local', 'type': 'string'})
        json_var_list = json.dumps(var_list)
        create_vars_req = self.session.post(self.tasks_url + '/%s/variables' % task_id, data=json_var_list)
        return create_vars_req.json()

    def complete_task(self, task_id):
        POST_args = json.dumps({'action': 'complete'})
        complete_task_req = self.session.post(self.tasks_url + '/%s' % task_id, data=POST_args)


    def get_proc_historic_tasks(self, proc_instance_id, finished=True):
        GET_args = {'processInstanceId': proc_instance_id}
        if finished:
            GET_args['finished'] = finished
        tasks_req = self.session.get(self.historic_tasks_url, params=GET_args)

        tasks = tasks_req.json()['data']
        for task in tasks:
            task['startTime'] = date_parse(task['startTime'])
            task['endTime'] = date_parse(task['endTime'])
        return tasks

