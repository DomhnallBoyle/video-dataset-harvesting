import re
import os
import time
from http import HTTPStatus

import requests
from main import config

MAX_RETRIES = 5


def get(endpoint, json=None):
    try:
        response = requests.get(endpoint, json=json)

        return response
    except Exception as e:
        print(e)


def post(endpoint, data=None, json=None, files=None):
    try:
        response = requests.post(endpoint, data=data, json=json, files=files)

        return response
    except Exception as e:
        print(e)


def download_file(endpoint, request_type='post', save_path=None, data=None, json=None, files=None, debug=False):
    num_retries = MAX_RETRIES

    while True:
        if request_type == 'post':
            response = post(endpoint=endpoint, data=data, json=json, files=files)
        elif request_type == 'get':
            response = get(endpoint=endpoint, json=json)
        else:
            raise Exception('No such request type')

        if response.status_code == HTTPStatus.OK:
            break

        if debug:
            print(response.status_code, response.reason)

        num_retries -= 1
        if num_retries == 0:
            raise Exception(f'Failed to download file {MAX_RETRIES} times')

        time.sleep(1)

    if not save_path:
        # get the original filename from the download file
        d = response.headers['content-disposition']
        filename = re.findall('filename=(.+)', d)[0]
        save_path = os.path.join(config.DOWNLOADS_PATH, filename)

    # read in chunks for large files
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(4096):
            f.write(chunk)

    return save_path
