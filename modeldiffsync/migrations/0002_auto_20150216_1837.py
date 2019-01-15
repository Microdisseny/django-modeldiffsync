# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('modeldiffsync', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modeldiffsync',
            name='online_check_url',
        ),
        migrations.RemoveField(
            model_name='modeldiffsync',
            name='password',
        ),
        migrations.RemoveField(
            model_name='modeldiffsync',
            name='update_callback_url',
        ),
        migrations.RemoveField(
            model_name='modeldiffsync',
            name='username',
        ),
        migrations.AddField(
            model_name='modeldiffsync',
            name='title',
            field=models.CharField(default=b'', help_text=b'descriptive name', max_length=100, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modeldiffsync',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modeldiffsync',
            name='name',
            field=models.CharField(unique=True, max_length=100),
            preserve_default=True,
        ),
    ]
