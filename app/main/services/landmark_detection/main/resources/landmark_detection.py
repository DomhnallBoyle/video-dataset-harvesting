import tempfile

from flask import request
from flask_restx import Namespace, reqparse, Resource
from main.utils.detection import detect_landmarks
from werkzeug.datastructures import FileStorage

landmark_detection_namespace = Namespace('Landmark Detection', align='/detect_landmarks')


@landmark_detection_namespace.route('/')
class LandmarkDetection(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('video', location='files', type=FileStorage,
                        required=True)

    @landmark_detection_namespace.expect(parser)
    def post(self):
        video_file = request.files['video']

        # create temporary file on disk - deleted automatically afterwards
        with tempfile.NamedTemporaryFile('wb+') as f:
            f.write(video_file.read())
            landmarks = detect_landmarks(f.name)

        video_file.close()

        return landmarks
