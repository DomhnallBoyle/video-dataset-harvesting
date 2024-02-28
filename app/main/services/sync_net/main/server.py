import argparse

from flask import Flask
from flask_restx import Api

app = Flask('Data Harvesting - AV Synchronisation')
api = Api(app=app,
          title='Data Harvesting - AV Synchronisation',
          version='1.0',
          description='Synchronise Audio and Video')


def main(args):
    from resources import crop_namespace, synchronisation_namespace

    api.add_namespace(crop_namespace)
    api.add_namespace(synchronisation_namespace)
    app.url_map.strict_slashes = False

    app.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8084)

    main(parser.parse_args())
