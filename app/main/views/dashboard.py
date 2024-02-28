from flask import Blueprint, render_template

from sqlalchemy.sql import func

from main.models import Segment, Video
from main.utils.db import Session as db_session
from main.utils.enums import TranscriptType
from main.utils.video import get_duration

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET'])
def dashboard():
    with db_session() as s:
        # extract all the videos with segments
        videos = s.query(Video).join(Video.segments).group_by(Video).having(func.count(Segment.id) > 0)

        # get counts and total duration
        manual_count, segment_count, usable_segment_count, total_duration = 0, 0, 0, 0
        for video in videos:
            segment_count += len(video.segments)
            if video.transcript_type == TranscriptType.MANUAL:
                manual_count += 1

            usable_segments = [segment for segment in video.segments if segment.local_identity is not None]
            usable_segment_count += len(usable_segments)

            total_duration += sum([segment.duration for segment in usable_segments])

        # get total dataset duration in hours
        total_duration /= 3600

    return render_template('dashboard.html', videos=videos, manual_count=manual_count, segment_count=segment_count,
                           usable_segment_count=usable_segment_count, total_duration=total_duration)
