import json
import os
import subprocess

from .base import Base
from main.config import config
from main.utils.file import File
from main.utils.http import post, download_file


class SyncNet(Base):

    def __init__(self):
        super().__init__(name=config.SYNC_NET_NAME, port=config.SYNC_NET_PORT)

    def find_synchronise(self, video_path, track):
        response = post(endpoint=f'{self.api}/synchronise/',
                        files={'video': File(video_path)},
                        data={'track': json.dumps(track)})

        return response

    def synchronise(self, input_video_path, output_video_path, frame_offset, fps=25):
        """https://github.com/joonson/syncnet_python/issues/2#issuecomment-833923703"""
        if os.path.exists(output_video_path):
            return

        time_offset = frame_offset / fps

        # delaying audio
        command = f'ffmpeg -hide_banner -loglevel error -y -i {input_video_path} -itsoffset {time_offset} -i {input_video_path} -map 0:v -map 1:a {output_video_path}'
        subprocess.call(command, shell=True, stdout=None)

    def get_cropped_video(self, save_path):
        download_file(endpoint=f'{self.api}/crop/',
                      request_type='get',
                      save_path=save_path)
