import json
import os
import tempfile

from flask import request
from flask_restx import Namespace, reqparse, Resource
from main.utils.alignment import align
from werkzeug.datastructures import FileStorage

forced_alignment_namespace = Namespace('Forced Alignment',
                                       description='',
                                       path='/align')


@forced_alignment_namespace.route('/')
class ForcedAlignment(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('audio', location='files', type=FileStorage,
                        required=True)
    parser.add_argument('transcript', location='files', type=FileStorage,
                        required=True)

    @forced_alignment_namespace.expect(parser)
    def post(self):
        audio_file = request.files['audio']
        transcript_file = request.files['transcript']

        with tempfile.NamedTemporaryFile('wb+') as f1, tempfile.NamedTemporaryFile('wb+') as f2:
            f1.write(audio_file.read())
            f2.write(transcript_file.read())

            f1.seek(0)
            f2.seek(0)

            results = align(audio_path=f1.name, transcript_path=f2.name)

        for file in [audio_file, transcript_file]:
            file.close()

        return results
