from .base import Base
from main.config import config
from main.utils.http import post
from main.utils.file import File


class SpeechRecognition(Base):

    def __init__(self):
        super().__init__(name=config.SPEECH_RECOGNITION_NAME, port=config.SPEECH_RECOGNITION_PORT)

    def transcribe(self, audio_path):
        response = post(
            endpoint=f'{self.api}/transcribe/',
            files={'audio': File(audio_path)},
        )

        return response
