import json

from django.conf import settings
from django.core.mail import mail_admins

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from modeldiff.models import Geomodeldiff
from .serializers import GeomodeldiffSerializer


class GeomodeldiffList(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        try:
            last_id = int(request.GET.get('last_id', 0))
        except Exception:
            last_id = 0

        try:
            limit = int(request.GET.get('limit', 0))
        except Exception:
            limit = 0

        qs = (
            Geomodeldiff.objects
            .filter(key=settings.MODELDIFF_KEY)
            .filter(pk__gt=last_id)
            .order_by('id')
        )

        if limit > 0:
            qs = qs[:limit]

        serializer = GeomodeldiffSerializer(qs, exclude_fields=['applied'])

        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
        except Exception:
            return Response(
                'Invalid JSON',
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = Geomodeldiff.objects.filter(
            key=data.get('key'),
            key_id=data.get('key_id')
        )

        if not qs.exists():
            try:
                obj = Geomodeldiff(**data)
                obj.save()

                serializer = GeomodeldiffSerializer(obj, many=True, exclude_fields=['applied'])

                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            except Exception:
                return Response(
                    'Invalid Data',
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            print('Already exists!')
            print(f"key={data.get('key')}, key_id={data.get('key_id')}")

            return Response(
                'Already exists!',
                status=status.HTTP_200_OK
            )


class Update(APIView):
    def get(self, request, *args, **kwargs):
        from .update import apply_modeldiffs
        result = apply_modeldiffs()

        if len(result['rows_skipped']) > 0:
            mail_admins('Some modeldiffs failed to apply!', 'ERROR!')

        serializer = GeomodeldiffSerializer(result['qs'], many=True, exclude_fields=['the_geom'])

        return Response(serializer.data)
