import argparse

from flask import Flask
from flask_restx import Api

app = Flask('Data Harvesting - FaceNet')
api = Api(app=app,
          title='Data Harvesting - FaceNet',
          version='1.0',
          description='Face Recognition')


def main(args):
    from resources import compare_namespace, embeddings_namespace

    api.add_namespace(compare_namespace)
    api.add_namespace(embeddings_namespace)
    app.url_map.strict_slashes = False

    app.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8085)

    main(parser.parse_args())
