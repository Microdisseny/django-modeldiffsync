from django.urls import re_path

from modeldiffsync.api import GeomodeldiffList, Update


urlpatterns = [
    re_path(r'^geomodeldiff$', GeomodeldiffList.as_view()),
    re_path(r'^update', Update.as_view()),
]
