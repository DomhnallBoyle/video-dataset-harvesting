import os

from deepspeech import Model
from flask import Flask
from flask_restx import Api

MODEL_PATH = 'models/deepspeech-0.9.3.pbmm'

app = Flask('Data Harvesting - Speech Recognition (Deep Speech)')
api = Api(app=app,
          title='Data Harvesting - Speech Recognition (Deep Speech)',
          version='1.0',
          description='Speech Recognition using Mozilla\'s Deep Speech')
model = None


def create_app(external_scorer_path=None, scorer_alpha=None, scorer_beta=None):
    # load namespaces
    from main.resources import speech_recognition_namespace

    # register namespaces
    api.add_namespace(speech_recognition_namespace)

    app.url_map.strict_slashes = False

    global model
    model = Model(MODEL_PATH)
    if external_scorer_path:
        model.enableExternalScorer(external_scorer_path)
    if scorer_alpha and scorer_beta:
        model.setScorerAlphaBeta(scorer_alpha, scorer_beta)

    return app
