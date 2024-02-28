import argparse
import os
import shutil
from http import HTTPStatus

from tqdm import tqdm

from main.models import Segment, Video
from main.containers import FaceDetection, FaceRecognition, SyncNet
from main.utils.audio import slice as slice_audio
from main.utils.db import construct_db, Session as db_session
from main.utils.file import initialise_dirs
from main.utils.time import int_to_time, time_to_millis, time_to_seconds
from main.utils.video import combine_audio_and_video, convert, crop, extract_audio, get_duration, get_num_frames, \
    slice as slice_video

MIN_MAX_SYNCNET_CONFIDENCE = 5


def main(args):
    construct_db(recreate=args.recreate_db)

    video_path = '/home/domhnall/Repos/Lip2Wav/nyu/part_1_delayed.mov'

    # split into 3 second samples

    with db_session() as s:
        video = Video()
        s.add(video)
        s.commit()

        duration = int(get_duration(video_path=video_path))

        print('Grabbing segments...')
        segments = []
        for start_secs in tqdm(list(range(0, duration, args.segment_length))):
            start_time = int_to_time(i=start_secs)
            end_time = int_to_time(i=start_secs + args.segment_length)
            segments.append(Segment(start=start_time, end=end_time))
        video.segments = segments
        s.commit()

        dirs = [video.data_path, video.segments_path,
                *[segment.data_path for segment in video.segments]]
        initialise_dirs(dirs)

        shutil.copyfile(video_path, video.video_path)
        extract_audio(video_path=video.video_path, output_audio_path=video.audio_path, audio_codec='pcm_s16le')

        # TODO: tidy these up between files
        print('Slicing video...')
        import time
        for segment in tqdm(video.segments):

            # TODO: Slicing is so slow, make it faster
            start = time.time()
            slice_audio(audio_path=video.audio_path,
                        start=time_to_millis(segment.start),
                        end=time_to_millis(segment.end),
                        output_path=segment.audio_path)
            print('Slice audio', time.time() - start)
            start = time.time()
            slice_video(video_path=video.video_path,
                        start=time_to_seconds(segment.start),
                        end=time_to_seconds(segment.end),
                        output_path=segment.video_path)
            print('Slice video', time.time() - start)
            start = time.time()
            combine_audio_and_video(video_path=segment.video_path,
                                    audio_path=segment.audio_path,
                                    combined_output_path=segment.combined_video_audio_path)
            print('Combine', time.time() - start)

        # run face detection and tracking on segments
        # remove segment if no people detected
        with FaceDetection() as fd:
            for segment in tqdm(video.segments):
                response = fd.detect(video_path=segment.combined_video_audio_path)
                segment.frame_detections = response.json()
                if segment.get_num_people() == 0:
                    s.delete(segment)
                s.commit()
            print('Segments left:', len(video.segments))

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--segment_length', type=int, default=3)
    parser.add_argument('--recreate_db', action='store_true')

    main(parser.parse_args())
