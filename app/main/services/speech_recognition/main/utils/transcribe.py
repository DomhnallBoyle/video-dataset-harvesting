import wave
import shlex
import subprocess

import numpy as np

try:
    from shlex import quote
except ImportError:
    from pipes import quote


def convert_samplerate(audio_path, desired_sample_rate):
    sox_cmd = 'sox {} --type raw --bits 16 --channels 1 --rate {} ' \
              '--encoding signed-integer --endian little --compression 0.0 ' \
              '--no-dither - '.format(quote(audio_path), desired_sample_rate)
    try:
        output = subprocess.check_output(shlex.split(sox_cmd),
                                         stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
    except OSError as e:
        raise OSError(e.errno,
                      'SoX not found, use {}hz files or install it: {}'.format(
                          desired_sample_rate, e.strerror))

    return np.frombuffer(output, np.int16)


def words_from_candidate_transcript(metadata):
    word = ""
    word_list = []
    word_start_time = 0
    # Loop through each character
    for i, token in enumerate(metadata.tokens):
        # Append character to word if it's not a space
        if token.text != " ":
            if len(word) == 0:
                # Log the start time of the new word
                word_start_time = token.start_time

            word = word + token.text
        # Word boundary is either a space or the last character in the array
        if token.text == " " or i == len(metadata.tokens) - 1:
            word_duration = token.start_time - word_start_time

            if word_duration < 0:
                word_duration = 0

            each_word = dict()
            each_word["word"] = word
            each_word["start_time"] = round(word_start_time, 4)
            each_word["duration"] = round(word_duration, 4)

            word_list.append(each_word)
            # Reset
            word = ""
            word_start_time = 0

    return word_list


def run_recognition(audio_path, num_candidates=3):
    from main import model

    desired_sample_rate = model.sampleRate()

    with wave.open(audio_path, 'rb') as f:
        frame_rate = f.getframerate()
        if frame_rate != desired_sample_rate:
            audio = convert_samplerate(audio_path=audio_path,
                                       desired_sample_rate=desired_sample_rate)
        else:
            audio = np.frombuffer(f.readframes(f.getnframes()), np.int16)

    output = model.sttWithMetadata(audio, int(num_candidates))

    result = []
    for transcript in output.transcripts:
        result.append({
            'transcript': ''.join([token.text for token in transcript.tokens]).strip(),
            'confidence': transcript.confidence,
            'words': words_from_candidate_transcript(transcript)
        })

    return result
