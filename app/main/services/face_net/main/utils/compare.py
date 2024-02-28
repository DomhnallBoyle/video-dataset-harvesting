import argparse

import cv2
import torch
from PIL import Image

from main.utils.inception_resnet_v1 import InceptionResnetV1
from main.utils.mtcnn import MTCNN

HEIGHT, WIDTH = 160, 160
MODEL_PATH = 'models/vggface2.pt'
DEVICE = 'cuda:0'

mtcnn = MTCNN(device=DEVICE)  # face detection
resnet = InceptionResnetV1(pretrained={'type': 'vggface2', 'model_path': MODEL_PATH}).eval().to(DEVICE)  # embeddings


def get_embeddings(face):
    face = mtcnn(face)
    face = face.to(DEVICE)

    # unsqueeze adds extra dimension
    embeddings = resnet(face.unsqueeze(0)).detach().cpu()

    return embeddings


def compare(face_1, face_2):
    # get embeddings for each face
    e1, e2 = get_embeddings(face_1), get_embeddings(face_2)
    dist = (e1 - e2).norm().item()  # euclidean distance

    return dist


def main(args):
    image_1 = cv2.imread(args.image_1_path)[..., ::-1]  # opencv loads to BGR, convert to RGB
    image_2 = cv2.imread(args.image_2_path)[..., ::-1]

    dist = compare(image_1, image_2)
    print('Distance:', dist)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('image_1_path')
    parser.add_argument('image_2_path')

    main(parser.parse_args())
