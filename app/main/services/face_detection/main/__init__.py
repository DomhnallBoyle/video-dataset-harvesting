import os

from flask import Flask
from flask_restx import Api

app = Flask('Data Harvesting - Face Detection')
api = Api(app=app,
          title='Data Harvesting - Face Detection',
          version='1.0',
          description='Run face detection on a video')


def create_app():
    # load namespaces
    from main.resources import face_detection_namespace

    # register namespaces
    api.add_namespace(face_detection_namespace)

    # setup config
    # app.config.from_object(configuration)

    app.url_map.strict_slashes = False

    # if not os.path.exists(configuration.UPLOADS_PATH):
    #     os.mkdir(configuration.UPLOADS_PATH)

    # logger = setup_logger(path='/shared/forced_alignment.log')
    # setup_request_logging(app=app, logger=logger)

    return app
