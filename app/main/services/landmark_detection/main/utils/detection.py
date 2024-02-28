import argparse
import os
from os.path import dirname as up

import cv2
import dlib

FILE_DIRECTORY = up(os.path.abspath(__file__))
MODELS_DIRECTORY = os.path.join(up(up(FILE_DIRECTORY)), 'models')
LANDMARK_DETECTOR_MODEL_PATH = os.path.join(MODELS_DIRECTORY, 'shape_predictor_68_face_landmarks.dat')

predictor = dlib.shape_predictor(LANDMARK_DETECTOR_MODEL_PATH)


def shape_to_np(landmarks):
    return [[p.x, p.y] for p in landmarks.parts()]


def detect_landmarks(video_path, debug=False):
    video_reader = cv2.VideoCapture(video_path)
    fps = int(video_reader.get(cv2.CAP_PROP_FPS))
    width, height = int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH)), \
                    int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT))
    while True:
        success, frame = video_reader.read()
        if not success:
            break

        landmarks = predictor(frame, dlib.rectangle(0, 0, width, height))
        landmarks = shape_to_np(landmarks)

        if debug:
            for x, y in landmarks:
                cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)
            cv2.imshow(video_path, frame)
            cv2.waitKey(fps)

    video_reader.release()
    cv2.destroyAllWindows()

    return []


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('video_path')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    landmarks = detect_landmarks(args.video_path, args.debug)
    print(landmarks)
