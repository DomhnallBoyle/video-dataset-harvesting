import argparse
import json
import random
import re
from http import HTTPStatus

import requests

from main.utils.db import construct_db
from harvest import harvest

GET_CATEGORY_RECORD_IDS = 'https://storage.googleapis.com/data.yt8m.org/2/j/v/{}.js'
GET_RECORD_YOUTUBE_ID = 'https://storage.googleapis.com/data.yt8m.org/2/j/i/{}/{}.js'
YOUTUBE_URL = 'http://youtube.com/watch?v={}'

RECORD_IDS_REGEX = r'p\("{}",(\[.+\])\);'
YOUTUBE_ID_REGEX = r'i\("{}","(.+)"\);'


def get_category_ids():
    pass


def harvest_by_category_id(category_id, num_to_harvest):
    response = requests.get(GET_CATEGORY_RECORD_IDS.format(category_id))
    response_str = response.content.decode('utf-8')

    # extract record ids from category
    record_ids = re.match(RECORD_IDS_REGEX.format(category_id), response_str).groups()[0]
    record_ids = json.loads(record_ids)

    random.shuffle(record_ids)
    if num_to_harvest:
        record_ids = record_ids[:num_to_harvest]

    # extract youtube ids from record
    for record_id in record_ids:
        response = requests.get(GET_RECORD_YOUTUBE_ID.format(record_id[:2], record_id))
        response_str = response.content.decode('utf-8')
        if response.status_code == HTTPStatus.OK:
            youtube_id = re.match(YOUTUBE_ID_REGEX.format(record_id), response_str).groups()[0]
            url = YOUTUBE_URL.format(youtube_id)

            harvest(url=url, manual_transcripts_only=True)


def main(args):
    # category_id = '01_8w2'  # CBS News (145 videos)
    category_id = '025m070'  # Newscaster (8377 videos)

    construct_db(recreate=args.recreate_db)

    harvest_by_category_id(category_id=category_id, num_to_harvest=args.n)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--recreate_db', action='store_true')
    parser.add_argument('--n', type=int)

    main(parser.parse_args())
