from django.db import models
from django.conf.urls import url
from django.contrib import admin
from django.forms import TextInput, Textarea
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.db.models import ForeignKey

import json

from diff_match_patch import diff_match_patch

from modeldiff.models import Geomodeldiff

from .models import ModeldiffSync
from .utils import run_sync
from .update import apply_modeldiffs, save_object

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


def decode_json(json_data):
    if json_data:
        data = json.loads(json_data)
    else:
        data = {}
    return data


def get_diff(original, modified, fields, skip_empty=False):
    data = []
    dmp = diff_match_patch()
    for field in fields:
        have_field = field in original and field in modified
        if skip_empty and not have_field:
            data.append('')
            continue
        v1 = original.get(field, '')
        v2 = modified.get(field, '')
        diff = dmp.diff_main(force_text(v1), force_text(v2))
        dmp.diff_cleanupSemantic(diff)
        html = dmp.diff_prettyHtml(diff)
        html = mark_safe(html)
        data.append(html)
    return data


class ModeldiffSyncAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'active', 'last_id', 'last_checked', 'last_sync')
    list_display_links = ('id', 'name',)

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'80'})},
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':40})},
    }

    actions = ['run_syncs', 'run_syncs_background']

    def run_syncs(self, request, queryset):
        for r in queryset:
            run_sync(r)
    run_syncs.short_description = "Run modelsyncs"

    def run_syncs_background(self, request, queryset):
        from django_beanstalkd_jobs import BeanstalkClient
        client = BeanstalkClient()
        client.call('modeldiffsync.run_sync', '')
    run_syncs_background.short_description = "Run modelsyncs in background"

    def get_urls(self):
        urls = super(ModeldiffSyncAdmin, self).get_urls()
        my_urls = [
            url(r'^apply_modeldiffs/$',
                self.admin_site.admin_view(self.apply_modeldiffs))
        ]
        return my_urls + urls

    def apply_modeldiffs(self, request):
        from .update import get_current_object_from_db, get_object_values
        from .update import get_fields

        if request.method == 'POST':
            print(request.POST)
            action = request.POST.get('action', None)
            id = request.POST.get('id', None)
            modeldiff = Geomodeldiff.objects.get(pk=id)
            obj, model = get_current_object_from_db(modeldiff)

            if modeldiff.action == 'delete':
                obj.delete()
                modeldiff.applied = True
                modeldiff.save()
                return HttpResponseRedirect('.')

            if action == 'all':
                # fix previous data first
                print("update ALL")
                old_data = decode_json(modeldiff.old_data)
                fields = get_fields(modeldiff) or list(old_data.keys())
                # for k in set(fields) & set(old_data.keys()):
                #     setattr(obj, k, old_data[k])
                for k in set(fields) & set(old_data.keys()):
                    field = model._meta.get_field(k)
                    if isinstance(field, ForeignKey):
                        if old_data[k]:
                            # TODO: support multiple to_fields
                            kwargs = {field.to_fields[0]: old_data[k]}
                            model_class = field.rel.model if hasattr(field, 'rel') else field.remote_field.model
                            value = model_class.objects.get(**kwargs)
                        else:
                            value = None
                    else:
                        value = old_data[k]
                    setattr(obj, k, value)

            new_data = decode_json(modeldiff.new_data)
            if action in ('all', 'new_only'):
                print("update NEW only")
                new_data = decode_json(modeldiff.new_data)
                fields = get_fields(modeldiff) or list(new_data.keys())
                # limit fields to those in new_data
                # for k in set(fields) & set(new_data.keys()):
                #     setattr(obj, k, new_data[k])
                for k in set(fields) & set(new_data.keys()):
                    field = model._meta.get_field(k)
                    if isinstance(field, ForeignKey):
                        if new_data[k]:
                            # TODO: support multiple to_fields
                            kwargs = { field.to_fields[0]: new_data[k] }
                            model_class = field.rel.model if hasattr(field, 'rel') else field.remote_field.model
                            value = model_class.objects.get(**kwargs)
                        else:
                            value = None
                    else:
                        value = new_data[k]
                    setattr(obj, k, value)
                save_object(obj)
                modeldiff.applied = True
                modeldiff.save()
            return HttpResponseRedirect('.')

        result = apply_modeldiffs(limit=1)
        skipped = []
        for r in result['rows_skipped']:
            obj, model = get_current_object_from_db(r)
            current = get_object_values(obj, model)

            fields = sorted(result['models_fields'][r.model_name])
            old_data = decode_json(r.old_data)
            new_data = decode_json(r.new_data)

            old_diff = get_diff(current, old_data, fields)
            new_diff = get_diff(current, new_data, fields, skip_empty=True)

            row = {
                'fields': fields,
                'old_diff': old_diff,
                'new_diff': new_diff,
                'modeldiff': r,
                'current': [current.get(x, '') for x in fields],
                'expected': [old_data.get(x, '') for x in fields],
                'new_data': [new_data.get(x, '') for x in fields],
            }
            skipped.append(row)
        result['rows_skipped'] = skipped
        return render(request, 'modeldiffsync/apply_modeldiffs.html', result)

admin.site.register(ModeldiffSync, ModeldiffSyncAdmin)
