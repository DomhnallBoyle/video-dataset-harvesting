import base64
import json
import os
import zipfile
from os.path import exists, join

import cv2
from sqlalchemy import event, Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base
from main import config
from main.mixins import VideoMixin
from main.utils.enums import TranscriptType
from main.utils.fields import IntEnum
from main.utils.file import JSONFile
from main.utils.video import show as show_video, get_centre_frame


class Video(Base, VideoMixin):

    __tablename__ = 'videos'

    # table attributes
    url = Column(String)
    transcript_type = Column(IntEnum(TranscriptType), default=TranscriptType.NO_TYPE)
    num_people = Column(Integer)

    segments = relationship('Segment', lazy='subquery')

    def __init__(self, url=None):
        super().__init__()
        self.url = url

    @property
    def data_path(self):
        return join(config.DATA_PATH, f'{self.id}')

    @property
    def segments_path(self):
        return join(self.data_path, 'segments')

    @property
    def video_path(self):
        return join(self.data_path, 'video.mp4')

    @property
    def audio_path(self):
        return join(self.data_path, 'audio.wav')

    @property
    def transcript_path(self):
        return join(self.data_path, 'transcript.en.vtt')

    @property
    def info_path(self):
        return join(self.data_path, 'data.info.json')

    @property
    def has_transcript(self):
        return exists(self.transcript_path)

    @property
    def has_info(self):
        return exists(self.info_path)

    @property
    def is_scraped(self):
        return exists(self.video_path) and exists(self.audio_path)

    @property
    def identity_list(self):
        identities = set()
        for segment in self.segments:
            identities.add(segment.local_identity)

        return list(identities)

    @property
    def duration(self):
        json = JSONFile(self.info_path).read()

        return json['duration']

    @property
    def view_count(self):
        json = JSONFile(self.info_path).read()

        return json['view_count']

    @property
    def thumbnail_base64(self):
        try:
            json = JSONFile(self.info_path).read()
            thumbnails = json.get('thumbnails')

            return thumbnails[-1]['url']
        except Exception:
            return super().thumbnail_base64

    def extract(self, zip_path):
        with zipfile.ZipFile(zip_path, 'r') as f:
            try:
                f.extract('video.mp4', self.data_path)
                f.extract('audio.wav', self.data_path)
                f.extract('transcript.en.vtt', self.data_path)
                f.extract('data.info.json', self.data_path)
            except KeyError:
                pass

        os.remove(zip_path)

    def show(self):
        if self.segments:
            for segment in self.segments:
                segment.show()

            return

        with open(self.detections_path, 'r') as f:
            video_detections = json.load(f)

        def f(**kwargs):
            video_capture = kwargs['video_capture']
            frame = kwargs['frame']
            frame_counter = kwargs['frame_counter']

            # get current frame seconds into video
            current_frame_secs = round(
                video_capture.get(cv2.CAP_PROP_POS_MSEC) / 1000, 3)

            cv2.putText(frame, f'{current_frame_secs} seconds', (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
                        cv2.LINE_AA)

            frame_detections = video_detections[frame_counter]
            for detection in frame_detections:
                x1, y1, x2, y2, score = detection
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)),
                              (0, 255, 0), 2)

            return frame

        return show_video(self.video_path, f=f)


@event.listens_for(Video, 'before_delete')
def receive_before_delete(mapper, connection, target):
    shutil.rmtree(target.data_path)
