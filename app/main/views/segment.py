from http import HTTPStatus

from flask import abort, Blueprint, render_template

from main.models import Segment
from main.utils.db import Session as db_session

segment_bp = Blueprint('segment', __name__)


@segment_bp.route('/segments/<segment_id>', methods=['GET'])
def get(segment_id):
    with db_session() as s:
        segment = s.query(Segment).filter((Segment.id == segment_id)).first()

    if not segment:
        return abort(HTTPStatus.NOT_FOUND)

    return render_template('segment.html', segment=segment)
