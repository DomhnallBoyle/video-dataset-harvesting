import datetime
import os
import shutil
from glob import glob
from os.path import exists, join

import cv2
from sqlalchemy import event, Float, Integer, Time, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from .base import Base
from main.mixins import VideoMixin
from main.utils.enums import Gender, HeadPoseDirection
from main.utils.fields import IntEnum
from main.utils.file import File, JSONFile
from main.utils.video import show as show_video


class Segment(Base, VideoMixin):

    __tablename__ = 'segments'

    # table attributes
    start = Column(Time)
    end = Column(Time)
    text = Column(String)
    frame_detections = Column(JSON)
    sync_confidence = Column(Float)
    pitch = Column(Float)
    roll = Column(Float)
    yaw = Column(Float)
    direction = Column(IntEnum(HeadPoseDirection), default=HeadPoseDirection.NO_TYPE)
    gender = Column(IntEnum(Gender), default=Gender.NO_TYPE)
    age = Column(Integer)
    local_identity = Column(Integer)
    asr_text = Column(String)
    asr_confidence = Column(Float)
    fa_log_likelihood = Column(Float)
    fa_alignment = Column(JSON)

    # foreign keys
    video_id = Column(UUID(as_uuid=True), ForeignKey('videos.id'))
    video = relationship('Video', back_populates='segments', lazy='joined')

    words = relationship('Word', lazy='subquery')

    def __init__(self, start, end, text=None):
        super().__init__()
        self.start = start
        self.end = end
        self.text = text

    @property
    def data_path(self):
        return join(self.video.segments_path, f'{self.id}')

    @property
    def words_path(self):
        return join(self.data_path, 'words')

    @property
    def video_path(self):
        return join(self.data_path, 'video.mp4')

    @property
    def audio_path(self):
        return join(self.data_path, 'audio.wav')

    @property
    def combined_video_audio_path(self):
        return join(self.data_path, 'combined.mp4')

    @property
    def speaker_video_path(self):
        return join(self.data_path, 'cropped_speaker.avi')

    @property
    def speaker_video_path_bigger(self):
        return join(self.data_path, 'cropped_speaker_bigger.avi')

    @property
    def speaker_video_path_mp4(self):
        return join(self.data_path, 'cropped_speaker.mp4')

    @property
    def speaker_audio_path(self):
        return join(self.data_path, 'cropped_speaker.wav')

    @property
    def transcript_path(self):
        return join(self.data_path, 'transcript.txt')

    @property
    def non_speaker_video_names(self):
        video_paths = glob(join(self.data_path, 'cropped_person_*.mp4'))

        print([os.path.basename(video_path) for video_path in video_paths])

        return [os.path.basename(video_path) for video_path in video_paths]

    @property
    def duration(self):
        date = datetime.date(1, 1, 1)
        start = datetime.datetime.combine(date, self.start)
        end = datetime.datetime.combine(date, self.end)

        return (end - start).total_seconds()

    def get_num_people(self):
        frame_detections = self.frame_detections
        people_ids = set()
        for frame_number, detections in frame_detections.items():
            people_ids = people_ids.union(set(list(detections.keys())))

        return len(people_ids)

    def show(self):
        def f(**kwargs):
            frame = kwargs['frame']
            cv2.putText(frame, self.text, (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
                        cv2.LINE_AA)

            return frame

        show_video(self.video_path, f=f)

    def update(self, **kwargs):
        direction = kwargs.pop('direction', None)
        super().update(**kwargs)
        if direction:
            self.direction = HeadPoseDirection.get(direction)


@event.listens_for(Segment, 'before_delete')
def receive_before_delete(mapper, connection, target):
    shutil.rmtree(target.data_path, ignore_errors=True)
