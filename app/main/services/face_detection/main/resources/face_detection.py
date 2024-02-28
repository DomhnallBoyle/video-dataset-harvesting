import tempfile

from flask import request
from flask_restx import Namespace, reqparse, Resource
from main.utils.detection import track
from werkzeug.datastructures import FileStorage

face_detection_namespace = Namespace('Face Detection', path='/detect')


@face_detection_namespace.route('/')
class FaceDetection(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('video', location='files', type=FileStorage,
                        required=True)

    @face_detection_namespace.expect(parser)
    def post(self):
        video_file = request.files['video']

        # create temporary file on disk - deleted automatically afterwards
        with tempfile.NamedTemporaryFile('wb+') as f:
            f.write(video_file.read())
            f.seek(0)
            frame_trackings = track(f.name)

        video_file.close()

        return frame_trackings
