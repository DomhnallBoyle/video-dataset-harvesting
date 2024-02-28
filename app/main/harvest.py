import argparse
import os
import shutil
import tempfile
from http import HTTPStatus

from tqdm import tqdm

from main.containers import FaceDetection, FaceRecognition, ForcedAlignment, HeadPoseEstimation, SpeechRecognition, \
    SyncNet, VideoScraper
from main.models import Video, Word
from main.utils.audio import slice as slice_audio
from main.utils.db import construct_db, Session as db_session
from main.utils.enums import TranscriptType
from main.utils.file import File, initialise_dirs
from main.utils.time import time_to_millis, time_to_seconds
from main.utils.transcript import is_similar
from main.utils.video import combine_audio_and_video, convert, crop, extract_audio, get_centre_frame, get_num_frames, \
    precise_slice, slice as slice_video
from main.utils.vtt import extract_segments

MIN_MAX_SYNCNET_CONFIDENCE = 5
ASR_ENGLISH_CONFIDENCE = -10

# TODO:
#  SyncNet confidence too strict? Plot ROC curve to find optimal SyncNet confidence
#  Fix hope-net, should be looking for majority angles rather than median
#  Find out if words required? If not, just try finding videos where the start and end can have FA confidence < 0 and the rest > 0 (everything else thrown out)
#  Youtube-dl should look at info first before downloading video, would be quicker


def remove_video(s, _video):
    # remove video from disk but keep it in the database
    # remove all segment data
    shutil.rmtree(_video.data_path, ignore_errors=True)
    if _video.segments:
        for segment in _video.segments:
            s.delete(segment)
        s.commit()


def harvest_url(**kwargs):
    url, manual_transcripts_only, keep_non_speakers = kwargs['url'], kwargs['manual_transcripts_only'], \
                                                      kwargs['keep_non_speakers']
    print('\n*******************************************************************************')
    print('URL:', url)
    print('Manual Transcripts Only:', manual_transcripts_only)
    print('Keep Non Speakers:', keep_non_speakers)

    # check if video has been done already
    with db_session() as s:
        video = s.query(Video).filter((Video.url == url)).first()
        if video:  # not None if exists
            print(f'{url} already processed')
            return

    try:
        # download video
        with VideoScraper() as vs:
            zip_path = vs.download_video(url=url)
    except Exception as e:
        print(f'Failed to scrape video: {e}')
        return

    with db_session() as s:
        # extract video zip
        video = Video(url=url)
        video.extract(zip_path=zip_path)
        s.add(video)
        s.commit()

        if video.has_info:
            # check for view count
            min_view_count = kwargs.get('min_num_views')
            if min_view_count and video.view_count < min_view_count:
                print(f'Not enough views: {video.view_count} < {min_view_count}')
                remove_video(s, video)
                return

            # check for duration
            max_duration = kwargs.get('max_duration')
            if max_duration and video.duration > (max_duration * 60):  # convert mins to seconds
                print(f'Video too long: {video.duration / 60} mins > {max_duration} mins')
                remove_video(s, video)
                return

        if not video.has_transcript:
            print(f'Video does not have transcript')
            remove_video(s, video)
            return

        segments, is_transcript_auto_generated = extract_segments(vtt_path=video.transcript_path)

        video.segments = segments
        video.transcript_type = TranscriptType.AUTO if is_transcript_auto_generated else TranscriptType.MANUAL
        s.commit()

        print('Video transcript type:', video.transcript_type.name)
        if manual_transcripts_only and video.transcript_type == TranscriptType.AUTO:
            print('Manual transcripts only')
            remove_video(s, video)
            return

        # create directories on disk
        dirs = [video.data_path, video.segments_path,
                *[segment.data_path for segment in video.segments],
                *[segment.words_path for segment in video.segments]]
        initialise_dirs(dirs)

        # extract audio, video and transcript segments using timestamps
        print(f'\nExtracting {len(video.segments)} video, audio and transcript segments...')
        for segment in tqdm(video.segments):
            slice_audio(audio_path=video.audio_path,
                        start=time_to_millis(segment.start),
                        end=time_to_millis(segment.end),
                        output_path=segment.audio_path)
            slice_video(video_path=video.video_path,
                        start=time_to_seconds(segment.start),
                        end=time_to_seconds(segment.end),
                        output_path=segment.video_path)
            combine_audio_and_video(video_path=segment.video_path,
                                    audio_path=segment.audio_path,
                                    combined_output_path=segment.combined_video_audio_path)
            File(segment.transcript_path).write(segment.text)

        # check language spoken in segments - run through ASR
        # 1) check if there's an ASR transcript
        # 2) check if ASR confidence meets threshold
        # 3) check if manual and ASR transcript are somewhat similar
        with SpeechRecognition() as asr:
            for segment in tqdm(video.segments):
                response = asr.transcribe(segment.audio_path)
                response = response.json()
                if response['transcript'].strip() and \
                        response['confidence'] >= ASR_ENGLISH_CONFIDENCE and \
                        is_similar(segment.text, response['transcript']):
                    segment.asr_text = response['transcript']
                    segment.asr_confidence = response['confidence']
                else:
                    s.delete(segment)
                s.commit()
            print('Segments left:', len(video.segments))

        if not video.segments:
            remove_video(s, video)
            return

        # run face detection and tracking on the segment
        # remove segment if no people detected
        with FaceDetection() as fd:
            for segment in tqdm(video.segments):
                response = fd.detect(video_path=segment.combined_video_audio_path)
                segment.frame_detections = response.json()
                if segment.get_num_people() == 0:
                    s.delete(segment)
                s.commit()
            print('Segments left:', len(video.segments))

        if not video.segments:
            remove_video(s, video)
            return

        # find out who the speaker is in the segments
        with SyncNet() as sn:
            for segment in tqdm(video.segments):
                num_frames = get_num_frames(segment.combined_video_audio_path)
                frame_detections = segment.frame_detections
                assert num_frames == len(frame_detections)

                # create tracks from frame detections
                people_detections = {_id: [] for _id in range(segment.get_num_people())}
                for frame_id, detections in frame_detections.items():
                    for people_id, detection in detections.items():
                        people_detections[int(people_id)].append({
                            k: v for k, v in zip(['x1', 'y1', 'x2', 'y2'], detection)
                        })

                # get sync results from tracks of same length of video
                people_sync_results = {}
                for person_id, detections in people_detections.items():
                    detection_frames_ratio = len(detections) / num_frames
                    if detection_frames_ratio == 1:
                        sync_response = sn.find_synchronise(
                            video_path=segment.combined_video_audio_path,
                            track=detections
                        )
                        if sync_response.status_code == HTTPStatus.OK:
                            sync_results = sync_response.json()
                            people_sync_results[person_id] = sync_results

                            # download cropped video from sync-net API
                            cropped_video_path = os.path.join(segment.data_path,
                                                              f'cropped_person_{person_id}.avi')
                            sn.get_cropped_video(save_path=cropped_video_path)
                            people_sync_results[person_id]['cropped_video_path'] = cropped_video_path

                if len(people_sync_results) > 0:
                    # get person with max confidence - they are the speaker
                    speaker = None
                    max_confidence = 0
                    for person_id, sync_results in people_sync_results.items():
                        confidence = sync_results['confidence']
                        if confidence > max_confidence:
                            max_confidence = confidence
                            speaker = person_id

                    # check how high the max confidence is
                    # i.e. small max confidence indicates speaker not that person
                    if max_confidence >= MIN_MAX_SYNCNET_CONFIDENCE:
                        segment.sync_confidence = max_confidence
                        s.commit()

                        # now sync the video by the offset of the speaker
                        av_offset = people_sync_results[speaker]['offset']
                        sn.synchronise(
                            input_video_path=people_sync_results[speaker]['cropped_video_path'],
                            output_video_path=segment.speaker_video_path,
                            frame_offset=av_offset
                        )

                        # delete speaker cropped video
                        os.remove(people_sync_results[speaker]['cropped_video_path'])
                        del people_sync_results[speaker]

                        if keep_non_speakers:
                            for non_speaker_id, sync_results in people_sync_results.items():
                                # convert avi to mp4
                                convert(
                                    input_video_path=sync_results['cropped_video_path'],
                                    output_video_path=sync_results['cropped_video_path'].replace('.avi', '.mp4')
                                )

                        # delete other avi cropped videos that aren't the speaker cropped video
                        for non_speaker_id, sync_results in people_sync_results.items():
                            os.remove(sync_results['cropped_video_path'])

                        # crop speaker again but make the bounding box bigger
                        # this allows other services to make detections easier
                        crop(
                            input_video_path=segment.combined_video_audio_path,
                            output_video_path=segment.speaker_video_path_bigger,
                            track=[[d['x1'], d['y1'], d['x2'], d['y2']] for d in people_detections[speaker]],
                            height=250,
                            width=250,
                            x_pad=30,
                            y_pad=50
                        )

                        # convert cropped speaker avi to mp4 for browser viewing reasons
                        convert(
                            input_video_path=segment.speaker_video_path,
                            output_video_path=segment.speaker_video_path_mp4
                        )

                        # extract cropped speaker audio for forced alignment
                        extract_audio(
                            video_path=segment.speaker_video_path,
                            output_audio_path=segment.speaker_audio_path,
                            audio_codec='pcm_s16le'
                        )
                    else:
                        # delete segment - max syncnet confidence too small
                        s.delete(segment)
                        s.commit()
                else:
                    # delete segment - no sync results
                    s.delete(segment)
                    s.commit()

            print('Segments left:', len(video.segments))

        if not video.segments:
            remove_video(s, video)
            return

        # ------------------ POST-PROCESSING ------------------

        # run forced alignment between audio and transcript
        # subtitles may not be in sync with audio
        # only do this with automatic transcripts
        """
        Forced alignment only uses WAV:PCM format
        Need to convert using the command (check out sync-net preprocessing for a similar command):
        ffmpeg -y -i cropped_speaker.avi -vn -acodec pcm_s16le cropped_speaker.wav

        Interesting comment about millisecond slicing video and audio:
        https://superuser.com/questions/1257914/ffmpeg-cut-videos-with-millisecond-accuracy-without-audio#comment1849491_1257914
        """
        with ForcedAlignment() as fa:
            for segment in tqdm(video.segments):
                response = fa.align(
                    audio_path=segment.speaker_audio_path,
                    transcript=segment.text
                )
                if response.status_code == HTTPStatus.OK:
                    response = response.json()
                    segment.update(
                        fa_log_likelihood=response['av_log_likelihood_per_frame'],
                        fa_alignment=response['alignment']
                    )
                else:
                    s.delete(segment)
                s.commit()

        # # check forced alignment word confidences
        # # i.e. if words in middle of transcript have confidence < -5, remove segment
        # # ok for words at start or end to < min confidence, just remove them
        # for segment in tqdm(video.segments):
        #     # find all words with bad scores
        #     removed_word_indices = []
        #     for i, alignment in enumerate(segment.fa_alignment):
        #         score = alignment[-1]
        #         if score < 0:
        #             removed_word_indices.append(i)
        #
        #     # check if all bad words are linked to start or end
        #     num_words = len(segment.fa_alignment)
        #     all_linked = True
        #     for index in removed_word_indices:
        #         if all([j in removed_word_indices for j in range(index+1)]) or \
        #             all([j in removed_word_indices for j in range(index, num_words)]):
        #             continue
        #         else:
        #             all_linked = False
        #             break
        #
        #     # remove segment if we have bad middle words, else trim text
        #     if all_linked:
        #         segment_words = segment.text.split(' ')
        #         segment_words = [word for i, word in enumerate(segment_words) if i not in removed_word_indices]
        #         segment.trimmed_text = ' '.join(segment_words)
        #     else:
        #         s.delete(segment)
        #     s.commit()

        #     # checks forced alignment word confidences
        #     # i.e. remove words with less confidence
        #     for segment in tqdm(video.segments):
        #         removed_words = []
        #         for i, alignment in enumerate(segment.fa_alignment):
        #             score = alignment[-1]
        #             if score < 0:
        #                 removed_words.append(i)
        #         segment_words = segment.text.split(' ')
        #         segment_words = [word for i, word in enumerate(segment_words) if i not in removed_words]
        #         segment.text = ' '.join(segment_words)
        #         s.commit()
        #
        #     # run forced alignment again
        #     for segment in tqdm(video.segments):
        #         response = fa.align(
        #             audio_path=segment.speaker_audio_path,
        #             transcript=segment.text
        #         )
        #         if response.status_code == HTTPStatus.OK:
        #             response = response.json()
        #             segment.update(
        #                 fa_log_likelihood=response['av_log_likelihood_per_frame'],
        #                 fa_alignment=response['alignment']
        #             )
        #         else:
        #             s.delete(segment)
        #         s.commit()

        # slice words and run through ASR to validate
        with SpeechRecognition() as asr:
            for segment in tqdm(video.segments):
                for i, (text, start_time, end_time, score) in enumerate(segment.fa_alignment):
                    word = Word(text=text, segment_id=segment.id)
                    s.add(word)
                    s.commit()

                    precise_slice(
                        video_path=segment.speaker_video_path,
                        start=start_time,
                        end=end_time,
                        output_path=word.video_path
                    )
                    return_code = convert(
                        input_video_path=word.video_path,
                        output_video_path=word.video_path_mp4
                    )
                    if return_code != 0 and os.path.exists(word.video_path_mp4):
                        s.delete(word)
                        s.commit()
                        continue

                    # extract audio and run ASR on word
                    extract_audio(
                        video_path=word.video_path,
                        output_audio_path=word.audio_path,
                        audio_codec='pcm_s16le'
                    )
                    asr_response = asr.transcribe(audio_path=word.audio_path)
                    if asr_response.status_code != HTTPStatus.OK:
                        s.delete(word)
                        s.commit()
                        continue

                    asr_response = asr_response.json()
                    word.asr_text = asr_response['transcript']
                    word.asr_confidence = asr_response['confidence']
                    s.commit()

                    os.remove(word.video_path)
                    os.remove(word.audio_path)

        # find head pose estimation
        with HeadPoseEstimation() as hpe:
            for segment in tqdm(video.segments):
                response = hpe.estimate(segment.speaker_video_path_bigger)
                if response.status_code == HTTPStatus.OK:
                    segment.update(**response.json())
                    s.commit()

        # run face recognition across segments for local identity matching
        segment_embeddings = {}
        with FaceRecognition() as fr:
            for segment in video.segments:
                response = fr.get_embeddings_by_video(segment.speaker_video_path_bigger)
                if response.status_code == HTTPStatus.OK:
                    embeddings = response.json()['embeddings']
                    segment_embeddings[segment.data_path] = embeddings

            segment_to_identities, num_people = fr.get_matching_identities(segment_embeddings)
            video.num_people = num_people
            for segment in video.segments:
                segment.local_identity = segment_to_identities.get(segment.data_path, -1)  # -1 = no identity
            s.commit()


def harvest_channel(**kwargs):
    channel_id = kwargs['channel_id']

    with VideoScraper() as vs:
        urls = vs.get_channel_urls(channel_id=channel_id)

    for url in urls:
        harvest_url(url=url, **kwargs)


def harvest_user(**kwargs):
    channel_user = kwargs['channel_user']

    with VideoScraper() as vs:
        urls = vs.get_user_urls(user_id=channel_user)

    for url in urls:
        harvest_url(url=url, **kwargs)


def harvest_playlist(**kwargs):
    playlist_id = kwargs['playlist_id']

    with VideoScraper() as vs:
        urls = vs.get_playlist_urls(playlist_id=playlist_id)

    for url in urls:
        harvest_url(url=url, **kwargs)


def main(args):
    f = {
        'url': harvest_url,
        'channel_id': harvest_channel,
        'channel_user': harvest_user,
        'playlist_id': harvest_playlist
    }
    run_type = args.run_type

    if run_type not in f:
        print(f'Choose from {list(f.keys())}')
        exit()

    f[run_type](**args.__dict__)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manual_transcripts_only', action='store_true')
    parser.add_argument('--min_num_views', type=int, default=None)
    parser.add_argument('--max_duration', type=int, default=None)
    parser.add_argument('--keep_non_speakers', action='store_true')

    sub_parsers = parser.add_subparsers(dest='run_type')

    parser_1 = sub_parsers.add_parser('url')
    parser_1.add_argument('url')

    parser_2 = sub_parsers.add_parser('channel_id')
    parser_2.add_argument('channel_id')

    parser_3 = sub_parsers.add_parser('channel_user')
    parser_3.add_argument('channel_user')

    parser_4 = sub_parsers.add_parser('playlist_id')
    parser_4.add_argument('playlist_id')

    main(parser.parse_args())
