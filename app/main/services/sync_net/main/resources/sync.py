import json
import os
import shutil

from flask import abort, request
from flask_restx import Namespace, reqparse, Resource
from werkzeug.datastructures import FileStorage

from main.utils.preprocessing import preprocess_video_and_audio, \
    extract_audio, reset_scale_and_frame_rate
from main.utils.SyncNetInstance import *

MODEL_PATH = 'models/syncnet_v2.model'

synchronisation_namespace = Namespace('Synchronisation', path='/synchronise')

# load sync_net model weights
s = SyncNetInstance()
s.loadParameters(MODEL_PATH)


class ArgNamespace:

    def __init__(self):
        self.batch_size = 20
        self.vshift = 15
        self.tmp_dir = '/var/www/data'
        self.reference = 'input'
        self.ref_dir = os.path.join(self.tmp_dir, self.reference)


opt = ArgNamespace()


@synchronisation_namespace.route('/')
class Synchronisation(Resource):

    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument('video', location='files', type=FileStorage, required=True)
    parser.add_argument('track', location='form', type=str, required=True)

    @synchronisation_namespace.expect(parser, validate=True)
    def post(self):
        try:
            track = json.loads(request.form['track'])  # [{}, {}, {}]
        except json.JSONDecodeError:
            abort(400)

        track = [[d['x1'], d['y1'], d['x2'], d['y2']] for d in track]

        video_file = request.files['video']
        video_save_path = os.path.join(opt.tmp_dir, 'video.mp4')
        video_file.save(video_save_path)

        # remove previous files
        if os.path.exists(opt.ref_dir):
            shutil.rmtree(opt.ref_dir)
        os.mkdir(opt.ref_dir)

        # scale video
        scaled_video_path = os.path.join(opt.ref_dir, 'video_scaled.avi')
        reset_scale_and_frame_rate(video_save_path, scaled_video_path)

        # extract audio from video
        audio_path = os.path.join(opt.ref_dir, 'extracted_audio.wav')
        extract_audio(scaled_video_path, audio_path)

        # preprocess video and audio
        preprocessed_video = os.path.join(opt.ref_dir, 'video_preprocessed.avi')
        preprocessed_audio = os.path.join(opt.ref_dir, 'audio_preprocessed.wav')
        combined_output_path = os.path.join(opt.ref_dir, 'video_combined.avi')
        preprocess_video_and_audio(
            video_input_path=scaled_video_path,
            video_output_path=preprocessed_video,
            track=track,
            audio_input_path=audio_path,
            audio_output_path=preprocessed_audio,
            combined_output_path=combined_output_path
        )

        offset, confidence, min_distance = s.evaluate(opt, videofile=combined_output_path)

        video_file.close()

        return {
            'offset': offset.item(),  # frame offset e.g -3 frames indicates 3/25 = 0.12 seconds offset
            'confidence': confidence.item(),
            'min_distance': min_distance.item()
        }
