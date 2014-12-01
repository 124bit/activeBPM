__author__ = 'torn'
from activeBPM.process_forms_default import FormWithComment, ProcessInitDefault, TaskDefault
from django import forms


class molds_documentation__init(ProcessInitDefault):  # molds name and number problem
    task_comment = forms.CharField(label='Комментарий', widget=forms.Textarea, required=False)
    worker_select = forms.CharField(max_length=200)
    check_state = forms.CharField(max_length=200)
    checker_select = forms.CharField(max_length=200)

    def clean(self):
        cleaned_data = super(molds_documentation__init, self).clean()

        worker_select = cleaned_data['worker_select']
        check_state = cleaned_data['check_state']
        checker_select = cleaned_data['checker_select']

        new_cleaned_data = {}
        new_cleaned_data['task_comment'] = cleaned_data['task_comment']
        new_cleaned_data['proc_individ_descr'] = new_cleaned_data['task_comment']


        if worker_select == 'designers_group':
            pass
            #cant solve Activiti problem with assignee. None, '', undefined don't work
            #new_cleaned_data['worker'] = None
        else:
            new_cleaned_data['worker'] = worker_select

        if check_state == 'check_needed':
            new_cleaned_data['need_audit'] = True
            new_cleaned_data['auditor'] = checker_select
        else:
            new_cleaned_data['need_audit'] = False
        return new_cleaned_data


class molds_documentation__folder_choice(TaskDefault):
    folder_state = forms.CharField(max_length=200)
    folder_select = forms.CharField(max_length=200)
    check_copy = forms.CharField(max_length=200)
    copy_folder_select = forms.CharField(max_length=200)

    mold_number = forms.IntegerField(label='Номер формы', min_value=100, max_value=9999, required=False)
    mold_name = forms.CharField(label='Имя формы', max_length=200, required=False)
    task_comment = forms.CharField(label='Комментарий', widget=forms.Textarea, required=False)

    def clean(self):
        cleaned_data = super(molds_documentation__folder_choice, self).clean()

        mold_number = cleaned_data['mold_number']
        mold_name = cleaned_data['mold_name']
        folder_state = cleaned_data['folder_state']
        folder_select = cleaned_data['folder_select']
        check_copy = cleaned_data['check_copy']
        copy_folder_select = cleaned_data['copy_folder_select']

        new_cleaned_data = {}
        new_cleaned_data['task_comment'] = cleaned_data['task_comment']

        if folder_state == "new_folder":
            folder = '%s. %s' % (mold_number, mold_name)
            if check_copy == 'copy_exists':
                folder += ' (копия %s)' % copy_folder_select
        else:
            folder = folder_select
        new_cleaned_data['mold_folder'] = folder
        new_cleaned_data['proc_individ_descr'] = folder
        return new_cleaned_data

class molds_documentation__documentation_audit(TaskDefault):
    documentation_valid = forms.CharField(max_length=200)