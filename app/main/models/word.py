import os
from os.path import exists, join

from .base import Base
from sqlalchemy import event, Column, Integer, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from main.mixins import VideoMixin


class Word(Base, VideoMixin):

    __tablename__ = 'words'

    text = Column(String)
    asr_text = Column(String)
    asr_confidence = Column(Float)

    segment_id = Column(UUID(as_uuid=True), ForeignKey('segments.id'))
    segment = relationship('Segment', back_populates='words', lazy='joined')

    def __init__(self, text, segment_id):
        super().__init__()
        self.text = text
        self.segment_id = segment_id

    @property
    def data_path(self):
        return self.segment.words_path

    @property
    def video_path(self):
        return join(self.data_path, f'{self.id}.avi')

    @property
    def video_path_mp4(self):
        return join(self.data_path, f'{self.id}.mp4')

    @property
    def audio_path(self):
        return join(self.data_path, f'{self.id}.wav')


@event.listens_for(Word, 'before_delete')
def receive_before_delete(mapper, connection, target):
    for path in [target.video_path, target.video_path_mp4, target.audio_path]:
        if exists(path):
            os.remove(path)
