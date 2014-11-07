from celery.task import task
from celery.schedules import crontab
from activeBPM.activiti_api import ActivityREST
from activeBPM.help_functions import send_email, send_sms
from activeBPM.models import BPMSUser

@task()
def email_unfinished_task():
    rest_client = ActivityREST('124bit', '777777')
    for user in BPMSUser.objects.all():
 #       if user.login == '124bit': # delete after testing!
            user_active_tasks = rest_client.get_tasks_info(assignee=user.login) + \
                rest_client.get_tasks_info(candidate_user=user.login)
            if user_active_tasks:
                mail_text = "Вам поставлены такие задачи: \n"
                for task in user_active_tasks:
                    mail_text += "%s - %s \n" % (task['name'], task['state'])
                activiti_user = rest_client.get_user(user.login)
                user_email = activiti_user['email']
                send_email('Ваши задачи в UHP', mail_text, user_email)

#TODO rewrite
@task()
def new_task_sms():
    rest_client = ActivityREST('124bit', '777777')
    for user in BPMSUser.objects.all():
 #       if user.login == '124bit': # delete after testing!
            user_active_tasks = rest_client.get_tasks_info(assignee=user.login)
            for task in user_active_tasks:
                if ('assignee_notified' not in task['vars'] or not task['vars']['assignee_notified']) and not task['assign_time']:
                    parent_task_id = task['parent_task_id']
                    if parent_task_id:
                        parent_task = rest_client.get_task_info(task['parent_task_id'])
                    else:
                        parent_task = None

                    if (parent_task and parent_task['assignee'] != task['assignee']) or not parent_task:
                        if (parent_task and (('notify_next' in parent_task['vars'] and parent_task['vars']['notify_next']) or ('notify_next' not in parent_task['vars']))) or not parent_task:
                            text_message = 'Вам назначена задача "%s"' % task['name']
                            send_sms(user.phone, text_message)
                            rest_client.set_task_vars(task['id'], {'assignee_notified': True})