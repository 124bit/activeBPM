__author__ = 'torn'

from django import forms


class FormWithComment(forms.Form):
    task_comment = forms.CharField(label='Комментарий', widget=forms.Textarea)

    def after_complete(self):
        pass


class TaskDefault(FormWithComment):
    pass


class ProcessInitDefault(FormWithComment):
    pass