import re
import uuid

import webvtt
from main.models import Segment
from main.utils.time import string_to_time


def extract_segments(vtt_path, video=None):
    segments = []
    is_auto_generated = False

    for caption in webvtt.read(vtt_path):

        # check if transcript auto-generated
        if not is_auto_generated:
            for line in caption._lines:
                if '<c>' in line:  # this indicates auto-generated transcript
                    is_auto_generated = True
                    break

        start = string_to_time(s=caption.start)
        end = string_to_time(s=caption.end)
        text = caption.text.split('\n')

        # remove empty sentences
        for sentence in text:
            if not sentence.strip():
                text.remove(sentence)

        # remove duplicates
        if end.second - start.second >= 1:
            segments.append(Segment(start=start, end=end, text=text))

    # remove more duplicates
    for i, segment in enumerate(segments[:-1]):
        for sentence in segment.text:
            if sentence in segments[i + 1].text:
                segments[i + 1].text.remove(sentence)

    for segment in segments:
        text = ' '.join(segment.text)
        # text = text.translate(str.maketrans('', '', string.punctuation)).lower()  # lower case and remove punctuation
        text = re.sub(r'[^\w\d\'\s]+', '', text)  # remove punctuation
        segment.text = text

    # remove segments without text
    segments = [segment for segment in segments if segment.text.strip()]

    return segments, is_auto_generated
