import tempfile

from flask import request
from flask_restx import Namespace, reqparse, Resource
from werkzeug.datastructures import FileStorage

from main.utils.estimation import estimate

head_pose_estimation_namespace = Namespace('Head Pose Estimation', path='/estimate')


@head_pose_estimation_namespace.route('/')
class FaceDetection(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('video', location='files', type=FileStorage,
                        required=True)

    @head_pose_estimation_namespace.expect(parser)
    def post(self):
        video_file = request.files['video']

        # create temporary file on disk - deleted automatically afterwards
        with tempfile.NamedTemporaryFile('wb+') as f:
            f.write(video_file.read())
            f.seek(0)
            result = estimate(f.name)

        video_file.close()

        return result
