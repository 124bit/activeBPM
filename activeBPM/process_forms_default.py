__author__ = 'torn'

from django import forms


class FormWithComment(forms.Form):
    task_comment = forms.CharField(label='Комментарий', widget=forms.Textarea)


class TaskDefault(FormWithComment):
    pass


class ProcessInitDefault(FormWithComment):
    mold_number = forms.IntegerField(label='Номер формы', min_value=1000, max_value=9999)
    mold_name = forms.CharField(label='Имя формы', max_length=100)