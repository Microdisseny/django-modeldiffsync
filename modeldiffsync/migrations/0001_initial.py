# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ModeldiffSync',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'descriptive name', max_length=100)),
                ('active', models.BooleanField(default=False)),
                ('online_check_url', models.CharField(help_text=b'URL returning app activity status', max_length=255, blank=True)),
                ('source_url', models.CharField(help_text=b'REST endpoint providing the modeldiffs', max_length=255, blank=True)),
                ('source_username', models.CharField(max_length=50, null=True, blank=True)),
                ('source_password', models.CharField(max_length=50, null=True, blank=True)),
                ('target_url', models.CharField(help_text=b'REST endpoint to create the  modeldiffs in', max_length=255, blank=True)),
                ('target_username', models.CharField(max_length=50, null=True, blank=True)),
                ('target_password', models.CharField(max_length=50, null=True, blank=True)),
                ('update_callback_url', models.CharField(help_text=b'URL to start updating', max_length=255, blank=True)),
                ('target_update_url', models.CharField(help_text=b'URL to call if modeldiffs were added and an update must be run', max_length=255, null=True, blank=True)),
                ('username', models.CharField(help_text=b'Username to access the URLS', max_length=50, blank=True)),
                ('password', models.CharField(help_text=b'Password to access the URLS', max_length=50, blank=True)),
                ('last_id', models.IntegerField(default=0)),
                ('last_checked', models.DateTimeField(null=True, blank=True)),
                ('last_sync', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
