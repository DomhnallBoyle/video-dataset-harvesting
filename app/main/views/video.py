from http import HTTPStatus

from flask import abort, Blueprint, render_template

from main.models import Video
from main.utils.db import Session as db_session

video_bp = Blueprint('video', __name__)


@video_bp.route('/videos/<video_id>', methods=['GET'])
def get(video_id):
    with db_session() as s:
        # get specific video
        video = s.query(Video).filter((Video.id == video_id)).first()

    if not video:
        abort(HTTPStatus.NOT_FOUND)

    return render_template('video.html', video=video)
