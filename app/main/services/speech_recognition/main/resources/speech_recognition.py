import tempfile

from main.utils.transcribe import run_recognition
from flask import request
from flask_restx import Namespace, reqparse, Resource
from werkzeug.datastructures import FileStorage

speech_recognition_namespace = Namespace('Speech Recognition',
                                         description='',
                                         path='/transcribe')


@speech_recognition_namespace.route('/')
class Transcribe(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('audio', location='files', type=FileStorage, required=True)
    parser.add_argument('num_candidates', location='form', type=int, default=3)

    @speech_recognition_namespace.expect(parser)
    def post(self):
        audio_file = request.files['audio']
        num_candidates = int(request.form['num_candidates'])

        with tempfile.NamedTemporaryFile('wb+') as f:
            f.write(audio_file.read())
            f.seek(0)
            result = run_recognition(audio_path=f.name, num_candidates=num_candidates)

        audio_file.close()

        return result
