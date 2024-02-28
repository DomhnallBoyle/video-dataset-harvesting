import cv2
import numpy as np
from flask import request
from flask_restx import Namespace, reqparse, Resource
from werkzeug.datastructures import FileStorage

from main.utils.compare import compare

compare_namespace = Namespace('Compare Faces', path='/compare')


@compare_namespace.route('/')
class Compare(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('face_1', location='files', type=FileStorage, required=True)
    parser.add_argument('face_2', location='files', type=FileStorage, required=True)

    @compare_namespace.expect(parser)
    def post(self):
        face_1 = request.files['face_1']
        face_2 = request.files['face_2']

        face_1 = cv2.imdecode(np.asarray(bytearray(face_1.read()), dtype=np.uint8), cv2.IMREAD_COLOR)
        face_2 = cv2.imdecode(np.asarray(bytearray(face_2.read()), dtype=np.uint8), cv2.IMREAD_COLOR)

        distance = compare(face_1, face_2)

        return {
            'distance': distance
        }
