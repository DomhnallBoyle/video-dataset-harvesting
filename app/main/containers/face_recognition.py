import os

import cv2
import numpy as np

from .base import Base
from main.config import config
from main.utils.file import File
from main.utils.http import post


class FaceRecognition(Base):

    def __init__(self):
        super().__init__(name=config.FACE_RECOGNITION_NAME, port=config.FACE_RECOGNITION_PORT)

    def compare(self, image_path_1, image_path_2):
        response = post(endpoint=f'{self.api}/compare/', files={'face_1': File(image_path_1),
                                                                'face_2': File(image_path_2)})

        return response

    def get_embeddings_by_image(self, image_path):
        response = post(endpoint=f'{self.api}/embeddings/image', files={'face': File(image_path)})

        return response

    def get_embeddings_by_video(self, video_path):
        response = post(endpoint=f'{self.api}/embeddings/video', files={'video': File(video_path)})

        return response

    def get_matching_identities(self, segment_embeddings, threshold=1):
        # return {segment.data_path: identity}
        matching_identities = {}
        counter = 0

        # find identities for each segment
        for segment_path, embedding in segment_embeddings.items():
            if len(matching_identities) == 0:
                matching_identities[counter] = [(segment_path, embedding)]
                counter += 1
            else:
                med_dists = []
                identity_ids = []
                for identity_id, data in matching_identities.items():
                    dists = [
                        np.linalg.norm(np.asarray(embedding) - np.asarray(e))
                        for p, e in data
                    ]
                    med_dists.append(np.median(dists))
                    identity_ids.append(identity_id)
                smallest_index = med_dists.index(min(med_dists))
                if med_dists[smallest_index] < threshold:
                    closest_identity_id = identity_ids[smallest_index]
                    matching_identities[closest_identity_id].append((segment_path, embedding))
                else:
                    matching_identities[counter] = [(segment_path, embedding)]
                    counter += 1

        num_people = len(matching_identities)
        segment_to_identity = {
            segment_path: identity_id
            for identity_id, data in matching_identities.items()
            for segment_path, embedding in data
        }

        return segment_to_identity, num_people
