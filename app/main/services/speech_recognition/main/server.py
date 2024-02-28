import argparse

from main import create_app


def main(args):
    app = create_app(args.external_scorer_path, args.scorer_alpha, args.scorer_beta)
    app.run(host='0.0.0.0', port=args.port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8081)
    parser.add_argument('--external_scorer_path')  # custom language model
    parser.add_argument('--scorer_alpha', type=float)  # language model weight
    parser.add_argument('--scorer_beta', type=float)  # word insertion weight

    main(parser.parse_args())
