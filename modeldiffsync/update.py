import json

from django.apps import apps
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, WKTWriter
from django.db.models import ForeignKey
from django.forms.models import model_to_dict
from modeldiff.models import Geomodeldiff


def get_current_object_from_db(modeldiff):
    model = apps.get_model(*modeldiff.model_name.rsplit('.', 1))
    unique_field = getattr(model.Modeldiff, 'unique_field', None)

    try:
        if unique_field:
            kwargs = {unique_field: modeldiff.unique_id}
            obj = model.objects.get(**kwargs)
        else:
            obj = model.objects.get(pk=modeldiff.model_id)
    except model.DoesNotExist:
        obj = model()

    return obj, model


def get_object_values(obj, model):
    geom_field = model.Modeldiff.geom_field
    geom_precision = model.Modeldiff.geom_precision

    values = model_to_dict(obj)
    geom = getattr(obj, geom_field)
    if geom:
        wkt_w = WKTWriter(precision=geom_precision)
        values[geom_field] = wkt_w.write(geom)
    return values


def get_fields(modeldiff):
    sync_conf = getattr(settings, 'MODELDIFFSYNC_CONF', {})

    conf = sync_conf.get(modeldiff.key, None)
    if conf:
        model = conf.get(modeldiff.model_name, None)
        if model:
            return model.get('fields', None)
    return None


def save_object(obj):
    obj.save(modeldiff_ignore=True)


def modeldiff_add(r):
    # TODO: check object does not exist
    obj, model = get_current_object_from_db(r)
    new_data = json.loads(r.new_data)
    for k in list(new_data.keys()):
        field = model._meta.get_field(k)
        if isinstance(field, ForeignKey):
            if new_data[k]:
                # TODO: support multiple to_fields
                kwargs = {field.to_fields[0]: new_data[k]}
                value = field.related_model.objects.get(**kwargs)
            else:
                value = None
        else:
            value = new_data[k]
        setattr(obj, k, value)
    save_object(obj)
    r.applied = True
    r.save()


def equals(obj1, obj2):
    if {'', None} == {obj1, obj2}:
        return True
    return str(obj1) == str(obj2)


def geom_equals(geom, wkt, geom_precision):
    if not geom or not wkt:
        return not geom and not wkt
    # compare coordinates with a tolerance instead of the rounded wkt strings,
    # values rounded on different servers can differ in the last decimal
    tolerance = 10 ** -geom_precision
    return geom.equals_exact(GEOSGeometry(wkt), tolerance)


def current_matches_old_data(obj, model, old_data):
    geom_field = model.Modeldiff.geom_field
    geom_precision = model.Modeldiff.geom_precision
    none_equals_empty = getattr(
        settings, 'MODELDIFF_NONE_EQUALS_EMPTY_STRING', False)

    current = get_object_values(obj, model)

    for k in old_data:
        if k == geom_field:
            same = geom_equals(
                getattr(obj, geom_field), old_data[k], geom_precision)
        elif none_equals_empty:
            same = equals(current.get(k), old_data[k])
        else:
            same = str(current.get(k)) == str(old_data[k])

        if not same:
            return False

    return True


def modeldiff_update(r):
    obj, model = get_current_object_from_db(r)

    old_data = json.loads(r.old_data)
    fields = list(old_data.keys())
    ok_to_apply = current_matches_old_data(obj, model, old_data)

    r.fields = fields

    if ok_to_apply:
        fields = get_fields(r) or list(old_data.keys())
        new_data = json.loads(r.new_data)
        for k in set(fields) & set(new_data.keys()):
            field = model._meta.get_field(k)
            if isinstance(field, ForeignKey):
                if new_data[k]:
                    # TODO: support multiple to_fields
                    kwargs = {field.to_fields[0]: new_data[k]}
                    value = field.related_model.objects.get(**kwargs)
                else:
                    value = None
            else:
                value = new_data[k]
            setattr(obj, k, value)
        save_object(obj)
        r.applied = True
        r.save()


def modeldiff_delete(r):
    obj, model = get_current_object_from_db(r)

    old_data = json.loads(r.old_data)
    fields = list(old_data.keys())
    ok_to_apply = current_matches_old_data(obj, model, old_data)

    r.fields = fields

    if ok_to_apply:
        obj._modeldiff_ignore = True
        obj.delete()
        r.applied = True
        r.save()


def apply_modeldiffs(limit=None):
    qs = Geomodeldiff.objects.filter(
        applied=False).order_by('date_created', 'pk')
    qs = qs.exclude(key=settings.MODELDIFF_KEY)

    if limit:
        qs = qs[:limit]

    stats = lambda: None
    stats.rows_processed = 0

    rows = lambda: None
    rows.applied = []
    rows.skipped = []
    models_fields = {}

    for r in qs:
        if r.action == 'add':
            modeldiff_add(r)

        elif r.action == 'delete':
            modeldiff_delete(r)
            models_fields[r.model_name] = r.fields

        elif r.action == 'update':
            modeldiff_update(r)
            models_fields[r.model_name] = r.fields

        stats.rows_processed += 1

        if r.applied:
            rows.applied.append(r)
        else:
            # no multitasking
            rows.skipped.append(r)
            break

    result = {
        'qs': qs,
        'models_fields': models_fields,
        'rows_applied': rows.applied,
        'rows_skipped': rows.skipped,
        'stats': stats.__dict__
    }

    return result
