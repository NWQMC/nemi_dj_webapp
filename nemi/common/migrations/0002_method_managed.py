# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-09-26 11:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='method',
            options={'managed': True, 'verbose_name': '#3 published method'},
        ),
        migrations.AlterModelOptions(
            name='methodonline',
            options={'managed': True, 'verbose_name': '#1 pending method'},
        ),
        migrations.AlterModelOptions(
            name='methodstg',
            options={'managed': True, 'verbose_name': '#2 in-review method'},
        ),
    ]
