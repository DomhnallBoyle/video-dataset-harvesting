import argparse
import os
from os.path import dirname as up

import cv2
import dlib
# from pyopenface.openface import detect_landmarks, FaceModel, FaceParams
# from pyopenface.models import install_models as install_openface_models

IOU_THRESHOLD = 0.2
DETECT_FACE_EVERY = 10
TRACKING_QUALITY = 7
MIN_FACE_DETECTION_CONFIDENCE_SCORE = 1
BB_ADD = 0

FILE_DIRECTORY = up(os.path.abspath(__file__))
MODELS_DIRECTORY = os.path.join(up(up(FILE_DIRECTORY)), 'models')
FACE_DETECTOR_MODEL_PATH = os.path.join(MODELS_DIRECTORY, 'mmod_human_face_detector.dat')

# install_openface_models()
# face_model = FaceModel()
# face_params = FaceParams()


def detect(video_path, debug=False):
    cnn_face_detector = dlib.cnn_face_detection_model_v1(FACE_DETECTOR_MODEL_PATH)

    # get video frames
    video_reader = cv2.VideoCapture(video_path)
    fps = int(video_reader.get(cv2.CAP_PROP_FPS))
    detections = []
    while True:
        success, frame = video_reader.read()
        if not success:
            break

        frame_detections = []
        faces = cnn_face_detector(frame, 1)
        for face in faces:
            x1, y1, x2, y2 = face.rect.left(), face.rect.top(), face.rect.right(), face.rect.bottom()
            frame_detections.append([x1, y1, x2, y2])
            if debug:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        detections.append(frame_detections)

        if debug:
            cv2.imshow(video_path, frame)
            cv2.waitKey(fps)

    video_reader.release()
    if debug:
        cv2.destroyAllWindows()

    return detections


def bb_intersection_over_union(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    iou = interArea / float(boxAArea + boxBArea - interArea)

    return iou


def rect_to_bb(r):
    return int(r.left()), int(r.top()), int(r.right()), int(r.bottom())


def landmarks_to_points(landmarks):
    return [[p.x, p.y] for p in landmarks.parts()]


def track(video_path, debug=False):
    # https://www.guidodiepen.nl/2017/02/tracking-multiple-faces/

    cnn_face_detector = dlib.cnn_face_detection_model_v1(FACE_DETECTOR_MODEL_PATH)

    video_reader = cv2.VideoCapture(video_path)
    fps = int(video_reader.get(cv2.CAP_PROP_FPS))

    frame_counter, current_face_id = 0, 0
    frame_tracks, face_trackers = {}, {}
    while True:
        success, frame = video_reader.read()
        if not success:
            break

        frame_tracks[frame_counter] = {}

        # updates trackers and removes bad quality trackers
        face_ids_to_delete = []
        for face_id, tracker in face_trackers.items():
            tracking_quality = tracker.update(frame)
            if tracking_quality < TRACKING_QUALITY:
                face_ids_to_delete.append(face_id)
        for face_id in face_ids_to_delete:
            del face_trackers[face_id]

        if frame_counter % DETECT_FACE_EVERY == 0:
            face_detections = cnn_face_detector(frame, 1)
            for face in face_detections:
                if face.confidence < MIN_FACE_DETECTION_CONFIDENCE_SCORE:
                    continue

                x1, y1, x2, y2 = rect_to_bb(face.rect)
                bb_center_x = (x1 + x2) / 2
                bb_center_y = (y1 + y2) / 2

                matched_id = None
                for face_id, tracker in face_trackers.items():
                    t_x1, t_y1, t_x2, t_y2 = rect_to_bb(tracker.get_position())
                    t_center_x = (t_x1 + t_x2) / 2
                    t_center_y = (t_y1 + t_y2) / 2

                    # # check face cp in tracker region
                    # # check tracker cp in face region
                    # if (t_x1 <= bb_center_x <= t_x2) and \
                    #         (t_y1 <= bb_center_y <= t_y2) and \
                    #         (x1 <= t_center_x <= x2) and \
                    #         (y1 <= t_center_y <= y2):
                    #     matched_id = face_id
                    #     break
                    iou = bb_intersection_over_union([x1, y1, x2, y2], [t_x1, t_y1, t_x2, t_y2])
                    if iou > IOU_THRESHOLD:
                        matched_id = face_id
                        break

                if matched_id is None:
                    tracker = dlib.correlation_tracker()
                    tracker.start_track(frame, dlib.rectangle(x1-BB_ADD, y1-BB_ADD, x2+BB_ADD, y2+BB_ADD))
                    face_trackers[current_face_id] = tracker
                    current_face_id += 1

        # perform NMS on trackers
        face_ids = list(face_trackers.keys())
        to_replace = []
        for i in range(len(face_ids)-1):
            for j in range(i+1, len(face_ids)):
                tracker_1 = face_trackers[face_ids[i]].get_position()
                tracker_2 = face_trackers[face_ids[j]].get_position()
                iou = bb_intersection_over_union(rect_to_bb(tracker_1), rect_to_bb(tracker_2))
                if iou > IOU_THRESHOLD:
                    to_replace.append([face_ids[i], face_ids[j]])
        for bad_face_id, good_face_id in to_replace:
            face_trackers[bad_face_id] = face_trackers[good_face_id]
            del face_trackers[good_face_id]

        # draw if applicable
        for face_id, tracker in face_trackers.items():
            t_x1, t_y1, t_x2, t_y2 = rect_to_bb(tracker.get_position())
            if debug:
                cv2.rectangle(frame, (t_x1, t_y1), (t_x2, t_y2), (255, 0, 0), 2)
                cv2.putText(frame, f'ID: {face_id}', (t_x1, t_y1-20), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)

            frame_tracks[frame_counter][face_id] = [t_x1, t_y1, t_x2, t_y2]

            # # perform facial landmark detection
            # landmarks = detect_landmarks(frame, face_model, face_params, [t_x1+BB_ADD,
            #                                                               t_y1+BB_ADD,
            #                                                               (t_x2-t_x1)-(2*BB_ADD),
            #                                                               (t_y2-t_y1)-(2*BB_ADD)])
            # num_landmarks = len(landmarks)
            # if debug and num_landmarks > 0:
            #     xs = landmarks[:num_landmarks//2]
            #     ys = landmarks[num_landmarks//2:]
            #     for x, y in zip(xs, ys):
            #         cv2.circle(frame, (int(x), int(y)), 1, (0, 0, 255), -1)

        if debug:
            cv2.imshow(video_path, frame)
            cv2.waitKey(fps)

        frame_counter += 1

    video_reader.release()
    if debug:
        cv2.destroyAllWindows()

    return frame_tracks


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('video_path')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    frame_tracks = track(args.video_path, args.debug)
    print(frame_tracks)

    # running X11 in docker container
    # docker run --net=host --env="DISPLAY" --volume="$HOME/.Xauthority:/root/.Xauthority:rw" --volume=$(pwd):/shared -it 62f433a197de
