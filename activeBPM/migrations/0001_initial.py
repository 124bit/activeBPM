# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BPMSUser',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('login', models.CharField(verbose_name='BPMS user login', unique=True, max_length=50)),
                ('password', models.CharField(verbose_name='BPMS user password', max_length=50)),
                ('web_user', models.OneToOneField(blank=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Web user of BPMS account', null=True)),
            ],
            options={
                'verbose_name_plural': 'BPMS Users',
                'ordering': ['login'],
                'verbose_name': 'BPMS User',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskFile',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('file', models.FileField(upload_to='comments_files/%f%d%m%y/')),
                ('key', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
