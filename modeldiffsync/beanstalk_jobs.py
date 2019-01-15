import os
import sys
import time
import io
from datetime import datetime

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

from django_beanstalkd_jobs import beanstalk_job

from modeldiffsync.models import ModeldiffSync

import requests
import json


@beanstalk_job
def run_sync(name):
    for sync in ModeldiffSync.objects.filter(name=name, active=True):
        run_single_sync(sync)

def run_single_sync(sync):
    from django_beanstalkd_jobs.utils import get_current_job
    jobrun = get_current_job()
    print(jobrun)
    print(jobrun.name)
    jobrun.meta['progress'] = '0'
    print('--- --- ---')
    print(sync.name)
    print(sync.source_url)
    print(sync.last_id)
    payload = {'last_id': sync.last_id, 'limit': '100'}
    r = requests.get(sync.source_url, params=payload, verify=False)
    print(r.status_code)
    print(r.text)
    if not r.status_code == 200:
        raise Exception(r.text)
    data = json.loads(r.text)
    # FIXME: ensure data is correct
    print()
    print(sync.target_url)
    headers = {'content-type': 'application/json'}
    r = requests.post(sync.target_url, data=json.dumps(data[0]),
                      headers=headers, verify=False)
    print(r.status_code)
    print(r.text)
    if not r.status_code == 201:
        raise Exception(r.text)

    jobrun.meta['progress'] = 100
