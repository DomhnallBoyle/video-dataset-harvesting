import datetime
import os
import subprocess

import cv2
import ffmpeg
import numpy as np
from scipy import signal


def slice(video_path, start, end, output_path, quiet=True):
    if os.path.exists(output_path):
        return

    ffmpeg.input(video_path) \
        .trim(start=start, end=end) \
        .setpts('PTS-STARTPTS') \
        .output(output_path) \
        .run(quiet=quiet)


def path_check(path):
    return path.replace("'", "\\'")


def call(command):
    return subprocess.call(command, shell=True, stdout=None)


def precise_slice(video_path, start, end, output_path):
    start = str(datetime.timedelta(seconds=start))
    end = str(datetime.timedelta(seconds=end))

    command = f'ffmpeg -hide_banner -loglevel error -y ' \
              f'-i {path_check(video_path)} -ss {start} -to {end} {path_check(output_path)}'

    return call(command)


def get_duration(video_path):
    if not os.path.exists(video_path):
        return 0

    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", video_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    return float(result.stdout)


def get_num_frames(video_path):
    video_capture = cv2.VideoCapture(video_path)
    num_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    video_capture.release()

    return num_frames


def get_frames(video_path):
    video_capture = cv2.VideoCapture(video_path)
    frames = []
    while True:
        success, frame = video_capture.read()
        if not success:
            break
        frames.append(frame)
    video_capture.release()

    return frames


def get_centre_frame(video_path):
    frames = get_frames(video_path)
    num_frames = len(frames)

    return frames[(num_frames // 2) - 1]


def combine_audio_and_video(video_path, audio_path, combined_output_path):
    if os.path.exists(combined_output_path):
        return

    command = f'ffmpeg -hide_banner -loglevel error -y -i {video_path} -i {audio_path} -c:v copy -c:a aac {combined_output_path}'

    return call(command)


def extract_audio(video_path, output_audio_path, audio_codec='copy'):
    command = f'ffmpeg -hide_banner -loglevel error -y -i {video_path} -vn -acodec {audio_codec} {output_audio_path}'

    return call(command)


def crop(input_video_path, output_video_path, track, height, width, x_pad=0, y_pad=0, fps=25, crop_scale=0.4):
    video_reader = cv2.VideoCapture(input_video_path)
    video_writer = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (height, width))

    track = [[x1-x_pad, y1-y_pad, x2+x_pad, y2+y_pad] for x1, y1, x2, y2 in track]

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


def convert(input_video_path, output_video_path):
    # convert to a different video format - changing codecs and containers. Good article:
    # https://ottverse.com/ffmpeg-convert-avi-to-mp4-lossless/
    command = f'ffmpeg -hide_banner -loglevel error -y ' \
              f'-i {path_check(input_video_path)} {path_check(output_video_path)}'

    return call(command)


def show(video_path, f=None):
    video_capture = cv2.VideoCapture(video_path)
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    frame_delay = int((1 / int(fps)) * 1000)
    frame_counter = 0

    while True:
        success, frame = video_capture.read()

        if not success:
            break

        if f:
            frame = f(frame=frame, video_capture=video_capture,
                      frame_counter=frame_counter)

        # display the frame
        cv2.imshow('frame', frame)
        if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
            break

        frame_counter += 1

    # release the capture
    video_capture.release()
    cv2.destroyAllWindows()
