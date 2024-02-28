import argparse

from flask import Flask
from flask_restx import Api

app = Flask('Data Harvesting - HopeNet')
api = Api(app=app,
          title='Data Harvesting - HopeNet',
          version='1.0',
          description='Head Pose Estimation')


def main(args):
    from resources import head_pose_estimation_namespace

    api.add_namespace(head_pose_estimation_namespace)
    app.url_map.strict_slashes = False

    app.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8085)

    main(parser.parse_args())
