# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-23 17:40
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Scheme name')),
                ('email', models.EmailField(max_length=254)),
                ('fasta', models.FileField(upload_to='uploads/%Y/%m/%d/')),
                ('amplicon_length', models.PositiveSmallIntegerField(validators=[django.core.validators.MaxValueValidator(4000)])),
                ('overlap', models.PositiveSmallIntegerField(validators=[django.core.validators.MaxValueValidator(200)])),
                ('request_time', models.DateTimeField(auto_now_add=True)),
                ('run_start_time', models.DateTimeField(null=True)),
                ('run_finish_time', models.DateTimeField(null=True)),
                ('run_duration', models.DurationField(null=True)),
                ('results_path', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Primer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.CharField(max_length=5)),
                ('name', models.CharField(max_length=50)),
                ('start', models.IntegerField()),
                ('end', models.IntegerField()),
                ('length', models.SmallIntegerField()),
                ('sequence', models.CharField(max_length=50)),
                ('gc', models.FloatField()),
                ('tm', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='PrimerPair',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_score', models.FloatField()),
                ('primer_left', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primer_pair_from_l', to='home.Primer')),
                ('primer_right', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primer_pair_from_r', to='home.Primer')),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheme', models.SmallIntegerField()),
                ('region_number', models.SmallIntegerField()),
                ('pool', models.SmallIntegerField()),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.Job')),
                ('top_pair', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='home.PrimerPair')),
            ],
        ),
        migrations.AddField(
            model_name='primerpair',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.Region'),
        ),
    ]
