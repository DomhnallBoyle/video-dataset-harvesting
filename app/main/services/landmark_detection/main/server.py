import argparse

from flask import Flask
from flask_restx import Api

app = Flask('Data Harvesting - Landmark Detection')
api = Api(app=app,
          title='Data Harvesting - Landmark Detection',
          version='1.0',
          description='Run landmark detection on a video ROI')


def main(args):
    # load namespaces
    from main.resources import landmark_detection_namespace

    # register namespaces
    api.add_namespace(landmark_detection_namespace)
    app.url_map.strict_slashes = False

    app.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8084)

    main(parser.parse_args())
