import argparse

from main import create_app


def main(args):
    app = create_app()
    app.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8082)

    main(parser.parse_args())
