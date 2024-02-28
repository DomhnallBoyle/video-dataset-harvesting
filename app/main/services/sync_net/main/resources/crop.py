import os
from http import HTTPStatus

from flask import abort, send_file
from flask_restx import Namespace, Resource

from main.resources.sync import opt

crop_namespace = Namespace('Crop', path='/crop')


@crop_namespace.route('/')
class Crop(Resource):

    def get(self):
        cropped_video_path = os.path.join(opt.ref_dir, 'video_combined.avi')
        if not os.path.exists(cropped_video_path):
            return abort(HTTPStatus.NOT_FOUND)

        return send_file(cropped_video_path, as_attachment=True)
