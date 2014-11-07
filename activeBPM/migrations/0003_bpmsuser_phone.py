# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activeBPM', '0002_taskfile_purpose'),
    ]

    operations = [
        migrations.AddField(
            model_name='bpmsuser',
            name='phone',
            field=models.CharField(blank=True, null=True, verbose_name='BPMS user phone', max_length=50),
            preserve_default=True,
        ),
    ]
