import os

from flask import Flask
from flask_restx import Api

app = Flask('Data Harvesting - Penn Phonetics Lab Forced Alignment')
api = Api(app=app,
          title='Data Harvesting - Penn Phonetics Lab Forced Alignment',
          version='1.0',
          description='Run forced alignment using audio and transcription')


def create_app():
    # load namespaces
    from main.resources import forced_alignment_namespace

    # register namespaces
    api.add_namespace(forced_alignment_namespace)

    app.url_map.strict_slashes = False

    return app
