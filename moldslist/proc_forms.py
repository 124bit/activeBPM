__author__ = 'torn'

from django import forms


class myProcess__usertask1(forms.Form):

    mold_number = forms.IntegerField(label='Mold number', min_value=1000, max_value=9999)
    mold_name = forms.CharField(label='Mold name', max_length=100)

class myProcess__init(forms.Form):

    mold_number = forms.IntegerField(label='Mold number', min_value=1000, max_value=9999)
    mold_name = forms.CharField(label='Mold name', max_length=100)