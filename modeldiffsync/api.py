import json

from django.conf import settings

from restless.views import Endpoint
from restless.modelviews import ListEndpoint, DetailEndpoint
from restless.models import serialize
from restless.http import HttpError, Http200, Http201


from modeldiff.models import Geomodeldiff


class GeomodeldiffList(ListEndpoint):
    model = Geomodeldiff

    def get_query_set(self, request, *args, **kwargs):
        last_id = request.GET.get('last_id', 0)
        limit = request.GET.get('limit', 0)

        if self.model:
            queryset = (
                self.model.objects.all()
                .filter(key=settings.MODELDIFF_KEY)
                .filter(pk__gt=last_id)
                .order_by('id')
            )
            if limit > 0:
                queryset = queryset[:limit]
            return queryset
        else:
            raise HttpError(404, 'Resource Not Found')

    def serialize(self, objs):
        return serialize(objs, exclude=('applied',))

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        qs = Geomodeldiff.objects.filter(key=data['key'],
                                         key_id=data['key_id'])
        if qs.count() == 0:
            obj = Geomodeldiff(**data)
            try:
                obj.save()
                return Http201(self.serialize(obj))
            except:
                raise HttpError(400, 'Invalid Data')
        else:
            print 'Already exists!'
            print 'key=%s, key_id=%s' % (data['key'], data['key_id'])
            return Http200('Already exists!')


class Update(Endpoint):
    def get(self, request):
        from .update import apply_modeldiffs
        result = apply_modeldiffs()

        return serialize(result['qs'], exclude=('the_geom'))
