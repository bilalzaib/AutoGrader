# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-23 11:26
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AutoGrade', '0012_remove_submission_percent'),
    ]

    operations = [
        migrations.CreateModel(
            name='Request_Extension',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('due_date', models.DateTimeField(default=datetime.datetime.now, verbose_name='due date')),
            ],
        ),
        migrations.AddField(
            model_name='assignment',
            name='allowed_late_days',
            field=models.IntegerField(default=3),
        ),
        migrations.AddField(
            model_name='submission',
            name='late_days',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='request_extension',
            name='assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='AutoGrade.Assignment'),
        ),
        migrations.AddField(
            model_name='request_extension',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='AutoGrade.Student'),
        ),
    ]
