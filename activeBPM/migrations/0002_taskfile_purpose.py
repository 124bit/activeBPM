# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activeBPM', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskfile',
            name='purpose',
            field=models.CharField(default='comment', max_length=200),
            preserve_default=False,
        ),
    ]
