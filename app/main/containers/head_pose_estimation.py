from .base import Base
from main.config import config
from main.utils.file import File
from main.utils.http import post


class HeadPoseEstimation(Base):

    def __init__(self):
        super().__init__(name=config.HEAD_POSE_ESTIMATION_NAME,
                         port=config.HEAD_POSE_ESTIMATION_PORT)

    def estimate(self, video_path):
        response = post(endpoint=f'{self.api}/estimate/', files={'video': File(video_path)})

        return response
