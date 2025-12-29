from rest_framework import serializers
from modeldiff.models import Geomodeldiff

class GeomodeldiffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geomodeldiff
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', None)
        super().__init__(*args, **kwargs)

        if exclude_fields:
            for field in exclude_fields:
                self.fields.pop(field, None)
