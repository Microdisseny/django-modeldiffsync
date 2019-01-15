import requests
import json


def create_remote_geomodeldiff(target_url, data):
    headers = {'content-type': 'application/json'}
    json_data = json.dumps(data)
    r = requests.post(target_url, data=json_data,
                      headers=headers, verify=False)
    return r


def run_sync(sync):
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

    if len(data) > 0:
        for gmd in data:
            gmd['key_id'] = gmd['id']
            del gmd['id']
            r = create_remote_geomodeldiff(sync.target_url, gmd)
            print(r.status_code)
            print(r.text)
            if r.status_code == 201:
                sync.last_id = gmd['key_id']
                sync.save()
            else:
                raise Exception(r.text)

        r = requests.get(sync.target_update_url)
        print(r.status_code)
        print(r.text)
