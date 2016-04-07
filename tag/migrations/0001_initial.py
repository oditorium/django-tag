# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-04-07 10:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import tag.models.tag


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='_Dummy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, db_index=True, default='', max_length=32, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_tag', models.CharField(blank=True, db_index=True, default='', max_length=255, unique=True)),
                ('_parent_tag', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tag.Tag')),
            ],
            bases=(tag.models.tag.TagBase, models.Model),
        ),
        migrations.AddField(
            model_name='_dummy',
            name='_tag_references',
            field=models.ManyToManyField(to='tag.Tag'),
        ),
    ]
