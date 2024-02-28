import tempfile

import cv2
import numpy as np
from flask import request
from flask_restx import Namespace, reqparse, Resource
from werkzeug.datastructures import FileStorage

from main.utils.compare import get_embeddings

embeddings_namespace = Namespace('Embeddings', path='/embeddings')


@embeddings_namespace.route('/video')
class VideoEmbeddings(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('video', location='files', type=FileStorage, required=True)

    @embeddings_namespace.expect(parser)
    def post(self):
        video = request.files['video']

        with tempfile.NamedTemporaryFile('wb+') as f:
            f.write(video.read())
            f.seek(0)

            video_reader = cv2.VideoCapture(f.name)
            frames = []
            while True:
                success, frame = video_reader.read()
                if not success:
                    break
                frames.append(frame)
            video_reader.release()

            centre_frame = frames[(len(frames) // 2) - 1]
            try:
                embeddings = get_embeddings(centre_frame)
            except AttributeError:
                for frame in frames:
                    try:
                        embeddings = get_embeddings(frame)
                        break
                    except AttributeError:
                        continue

        return {'embeddings': embeddings.flatten().tolist()}


@embeddings_namespace.route('/image')
class ImageEmbeddings(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('face', location='files', type=FileStorage, required=True)

    @embeddings_namespace.expect(parser)
    def post(self):
        face = request.files['face']

        face = cv2.imdecode(np.asarray(bytearray(face.read()), dtype=np.uint8), cv2.IMREAD_COLOR)

        embeddings = get_embeddings(face)

        return {'embeddings': embeddings.flatten().tolist()}
