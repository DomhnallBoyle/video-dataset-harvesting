from p2fa.align import align as _align


def align(audio_path, transcript_path):
    phoneme_alignments, word_alignments, av_log_likelihood_per_frame = \
        _align(wavfile=audio_path, trsfile=transcript_path)

    return {
        'av_log_likelihood_per_frame': av_log_likelihood_per_frame,  # this includes silences in the calculation
        'phoneme_alignments': phoneme_alignments,
        'word_alignments': word_alignments
    }
