__author__ = 'torn'

from django import forms


class MoldTaskDefault(forms.Form):

    mold_number = forms.IntegerField(label='Номер формы', min_value=1000, max_value=9999)
    mold_name = forms.CharField(label='Имя формы', max_length=100)

class MoldProcessInitDefault(forms.Form):
    task_comment = forms.CharField(label='Комментарий', widget=forms.Textarea)