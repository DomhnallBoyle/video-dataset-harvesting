import base64
import os

import cv2


class VideoMixin:

    @property
    def thumbnail_base64(self):
        video_reader = cv2.VideoCapture(self.video_path)
        success, frame = video_reader.read()
        video_reader.release()

        if not success:
            return None

        frame_buff = cv2.imencode('.jpg', frame)[1]

        return base64.b64encode(frame_buff).decode('utf-8')

    @property
    def data_path(self):
        raise NotImplementedError

    @property
    def video_path(self):
        raise NotImplementedError
