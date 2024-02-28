import argparse
import json
import os
import shutil
import subprocess

import cv2
import numpy as np
from scipy import signal

WIDTH, HEIGHT, FPS = 224, 224, 25
CROP_SCALE = 0.4


def call(command):
    print(f'----- {command} -----')
    subprocess.call(command, shell=True, stdout=None)


def extract_audio(video_path, audio_output_path):
    command = f'ffmpeg -hide_banner -loglevel error -y -i {video_path} -ac 1 -vn -acodec pcm_s16le -ar 16000 {audio_output_path}'
    call(command)


def reset_scale_and_frame_rate(input_path, output_path):
    command = f'ffmpeg -hide_banner -loglevel error -y -i {input_path} -qscale:v 2 -async 1 -r {FPS} {output_path}'
    call(command)


def preprocess_video_and_audio(video_input_path, video_output_path, track, audio_input_path, audio_output_path,
                               combined_output_path, width=WIDTH, height=HEIGHT, crop_scale=CROP_SCALE):
    video_reader = cv2.VideoCapture(video_input_path)
    video_writer = cv2.VideoWriter(video_output_path, cv2.VideoWriter_fourcc(*'XVID'), FPS, (height, width))

    detections = {'x': [], 'y': [], 's': []}
    for x1, y1, x2, y2 in track:
        detections['s'].append(max((y2 - y1), (x2 - x1)) / 2)  # detection box size
        detections['x'].append((x1 + x2) / 2)  # center x
        detections['y'].append((y1 + y2) / 2)  # center y

    # smooth detections
    detections['s'] = signal.medfilt(detections['s'], kernel_size=13)
    detections['x'] = signal.medfilt(detections['x'], kernel_size=13)
    detections['y'] = signal.medfilt(detections['y'], kernel_size=13)

    frame_counter = 0
    while True:
        success, frame = video_reader.read()
        if not success:
            break

        bs = detections['s'][frame_counter]  # detection box size
        bsi = int(bs * (1 + 2 * crop_scale))  # pad videos by this amount

        frame = np.pad(frame, ((bsi, bsi), (bsi, bsi), (0, 0)), 'constant', constant_values=(110, 110))
        mx = detections['x'][frame_counter] + bsi  # bbox center X
        my = detections['y'][frame_counter] + bsi  # bbox center Y

        face = frame[int(my - bs):int(my + bs * (1 + 2 * crop_scale)),
                     int(mx - bs * (1 + crop_scale)):int(mx + bs * (1 + crop_scale))]

        video_writer.write(cv2.resize(face, (height, width)))

        frame_counter += 1

    video_writer.release()
    video_reader.release()

    audio_start = 0 / FPS
    audio_end = (frame_counter + 1) / FPS

    # crop audio file
    command = f'ffmpeg -hide_banner -loglevel error -y -i {audio_input_path} -ss {audio_start:.3f} -to {audio_end:.3f} {audio_output_path}'
    call(command)

    # combine audio and video files
    command = f'ffmpeg -hide_banner -loglevel error -y -i {video_output_path} -i {audio_output_path} -c:v copy -c:a copy {combined_output_path}'
    call(command)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('video_input_path')
    parser.add_argument('track_path')
    parser.add_argument('--width', type=int)
    parser.add_argument('--height', type=int)
    parser.add_argument('--crop_scale', type=float)

    args = parser.parse_args()

    tmp_dir = '/tmp'
    ref_dir = os.path.join(tmp_dir, 'preprocessed')
    if os.path.exists(ref_dir):
        shutil.rmtree(ref_dir)
    os.makedirs(ref_dir)

    with open(args.track_path, 'r') as f:
        frame_detections = json.load(f)
        track = []
        for frame_id, detections in frame_detections.items():
            for people_id, detection in detections.items():
                track.append({
                    k: v for k, v in zip(['x1', 'y1', 'x2', 'y2'], detection)
                })
        track = [[d['x1'], d['y1'], d['x2'], d['y2']] for d in track]

    # scale video
    scaled_video_path = os.path.join(ref_dir, 'video_scaled.avi')
    reset_scale_and_frame_rate(args.video_input_path, scaled_video_path)

    # extract audio from video
    audio_path = os.path.join(ref_dir, 'extracted_audio.wav')
    extract_audio(scaled_video_path, audio_path)

    # preprocess video and audio
    preprocessed_video = os.path.join(ref_dir, 'video_preprocessed.avi')
    preprocessed_audio = os.path.join(ref_dir, 'audio_preprocessed.wav')
    combined_output_path = os.path.join(ref_dir, 'video_combined.avi')
    preprocess_video_and_audio(
        video_input_path=scaled_video_path,
        video_output_path=preprocessed_video,
        track=track,
        audio_input_path=audio_path,
        audio_output_path=preprocessed_audio,
        combined_output_path=os.path.join(ref_dir, 'combined_output.avi'),
        width=args.width,
        height=args.height,
        crop_scale=args.crop_scale
    )
