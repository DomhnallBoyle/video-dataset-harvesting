import os

from flask import Flask
from flask_restx import Api

DOWNLOADS_PATH = 'downloads'

app = Flask('Data Harvesting - Video Scraper')
api = Api(app=app,
          title='Data Harvesting - Video Scraper',
          version='1.0',
          description='Video Scraper via URLs')


def create_app():
    # load namespaces
    from main.resources import url_namespace, video_namespace

    # register namespaces
    api.add_namespace(url_namespace)
    api.add_namespace(video_namespace)

    app.url_map.strict_slashes = False

    # setup directories
    if not os.path.exists(DOWNLOADS_PATH):
        os.mkdir(DOWNLOADS_PATH)

    return app
