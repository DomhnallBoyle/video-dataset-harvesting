import matplotlib.pyplot as plt
import numpy as np
import language_tool_python

from main.models import Segment
from main.utils.db import Session as db_session


def plot_hist(data, bin_width=1, x_label=None):
    plt.hist(data, bins=np.arange(min(data), max(data) + bin_width, bin_width))
    if x_label:
        plt.xlabel(x_label)
    plt.ylabel('Binned Count')
    plt.show()


def main():
    with db_session() as s:
        segments = s.query(Segment).all()

    # segments = [segment for segment in segments if segment.fa_log_likelihood and segment.fa_log_likelihood > 10]
    print('Num Segments:', len(segments))

    # # show binned histograms
    # fa_confidences = [segment.fa_log_likelihood for segment in segments if segment.fa_log_likelihood]
    # asr_confidences = [segment.asr_confidence for segment in segments if segment.asr_confidence]
    # sync_confidences = [segment.sync_confidence for segment in segments if segment.sync_confidence]
    # plot_hist(fa_confidences, x_label='FA Average Log Likelihood Per Frame')
    # plot_hist(asr_confidences, x_label='ASR Confidences')
    # plot_hist(sync_confidences, x_label='Sync Confidences')

    language_tool = language_tool_python.LanguageTool('en-US')
    is_good_rule = lambda rule: rule.message == 'Possible spelling mistake found.'

    for segment in segments:
        if segment.local_identity is None:
            continue

        # print('Segment before:')
        # print(f'Transcript: "{segment.text}"')
        # print(f'ASR: "{segment.asr_text}", {segment.asr_confidence}')
        # print(f'FA: {segment.fa_log_likelihood}, {[[a[0], a[-1]] for a in segment.fa_alignment]}')

        if segment.asr_confidence > -2:
            text_before = segment.asr_text
            for _ in range(3):
                grammar_matches = language_tool.check(text_before)
                correction = language_tool_python.utils.correct(text_before, grammar_matches)
                text_before = correction

            print(f'{segment.asr_text}, {correction}, {segment.asr_confidence}')


if __name__ == '__main__':
    main()
