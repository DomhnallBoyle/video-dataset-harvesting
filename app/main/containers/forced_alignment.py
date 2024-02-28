import tempfile

from .base import Base
from main.config import config
from main.utils.http import post
from main.utils.file import File


class ForcedAlignment(Base):

    def __init__(self):
        super().__init__(name=config.FORCED_ALIGNMENT_NAME, port=config.FORCED_ALIGNMENT_PORT)

    def align(self, audio_path, transcript):
        with tempfile.NamedTemporaryFile('w+') as f:
            f.write(transcript)
            f.seek(0)
            response = post(endpoint=f'{self.api}/align/',
                            files={'audio': File(audio_path),
                                   'transcript': File(f.name)})

            return response
