import os

from pydub import AudioSegment


def slice(audio_path, start, end, output_path):
    if os.path.exists(output_path):
        return

    audio = AudioSegment.from_wav(audio_path)
    segment = audio[start:end]
    segment.export(output_path, format='wav')
