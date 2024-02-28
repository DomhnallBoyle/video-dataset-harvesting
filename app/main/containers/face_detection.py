import os

from .base import Base
from main.config import config
from main.utils.file import File
from main.utils.http import post


class FaceDetection(Base):

    def __init__(self):
        super().__init__(name=config.FACE_DETECTION_NAME, port=config.FACE_DETECTION_PORT)

    def detect(self, video_path):
        response = post(endpoint=f'{self.api}/detect/',
                        files={'video': File(video_path)})

        return response
