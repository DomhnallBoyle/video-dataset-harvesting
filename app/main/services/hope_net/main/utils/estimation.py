import argparse
from math import cos, sin

import cv2
import numpy as np
import torch
import torchvision.models.resnet
import torch.nn.functional as F
from PIL import Image
from torch.autograd import Variable
from torchvision import transforms

from main.utils.model import Hopenet

MODEL_PATH = 'models/hopenet_robust_alpha1.pkl'

# setup model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = Hopenet(block=torchvision.models.resnet.Bottleneck, layers=[3, 4, 6, 3], num_bins=66).to(device)
saved_state_dict = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(saved_state_dict)
model.eval()

# setup transformations
transformations = transforms.Compose([
    # transforms.Resize(224),
    # transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def draw_axis(img, yaw, pitch, roll, tdx=None, tdy=None, size=100):
    pitch = pitch * np.pi / 180
    yaw = -(yaw * np.pi / 180)
    roll = roll * np.pi / 180

    if tdx != None and tdy != None:
        tdx = tdx
        tdy = tdy
    else:
        height, width = img.shape[:2]
        tdx = width / 2
        tdy = height / 2

    # X-Axis pointing to right. drawn in red
    x1 = size * (cos(yaw) * cos(roll)) + tdx
    y1 = size * (cos(pitch) * sin(roll) + cos(roll) * sin(pitch) * sin(yaw)) + tdy

    # Y-Axis | drawn in green
    #        v
    x2 = size * (-cos(yaw) * sin(roll)) + tdx
    y2 = size * (cos(pitch) * cos(roll) - sin(pitch) * sin(yaw) * sin(roll)) + tdy

    # Z-Axis (out of the screen) drawn in blue
    x3 = size * (sin(yaw)) + tdx
    y3 = size * (-cos(yaw) * sin(pitch)) + tdy

    cv2.line(img, (int(tdx), int(tdy)), (int(x1), int(y1)), (0, 0, 255), 3)
    cv2.line(img, (int(tdx), int(tdy)), (int(x2), int(y2)), (0, 255, 0), 3)
    cv2.line(img, (int(tdx), int(tdy)), (int(x3), int(y3)), (255, 0, 0), 2)

    return img


def get_direction(yaw, pitch):
    if -10 <= pitch <= 10:
        direction = 'centre'
    elif pitch > 10:
        direction = 'upper'
    else:
        direction = 'lower'

    if -10 <= yaw <= 10 and direction != 'centre':
        direction += ' centre'
    elif yaw > 10:
        direction += ' right'
    elif yaw < -10:
        direction += ' left'

    return direction


def estimate(video_path, debug=False):
    video_reader = cv2.VideoCapture(video_path)

    idx_tensor = torch.FloatTensor(list(range(66))).to(device)

    angles = []
    while True:
        success, frame = video_reader.read()
        if not success:
            break

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # img = Image.fromarray(img)
        img = cv2.resize(img, (224, 224))
        img = transformations(img)

        img_shape = img.size()
        img = img.view(1, img_shape[0], img_shape[1], img_shape[2])
        img = Variable(img).to(device)

        yaw, pitch, roll = model(img)

        yaw_predicted = F.softmax(yaw, dim=1)
        pitch_predicted = F.softmax(pitch, dim=1)
        roll_predicted = F.softmax(roll, dim=1)

        yaw_predicted = round((torch.sum(yaw_predicted.data[0] * idx_tensor) * 3 - 99).item(), 2)
        pitch_predicted = round((torch.sum(pitch_predicted.data[0] * idx_tensor) * 3 - 99).item(), 2)
        roll_predicted = round((torch.sum(roll_predicted.data[0] * idx_tensor) * 3 - 99).item(), 2)

        # store results
        angles.append([yaw_predicted, pitch_predicted, roll_predicted])

        if debug:
            # find direction
            direction = get_direction(yaw_predicted, pitch_predicted)

            frame = draw_axis(frame, yaw_predicted, pitch_predicted, roll_predicted)
            cv2.putText(frame, direction, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.imshow('Head Pose Estimation', frame)
            cv2.waitKey(25)

    video_reader.release()
    cv2.destroyAllWindows()

    # direction calculated by median of yaws and pitches
    yaws, pitches, _ = zip(*angles)
    direction = get_direction(np.median(yaws), np.median(pitches))

    return {
        'direction': direction,
        'angles': angles
    }


def main(args):
    results = estimate(args.video_path, args.debug)
    print(results['direction'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('video_path')
    parser.add_argument('--debug', action='store_true')

    main(parser.parse_args())
