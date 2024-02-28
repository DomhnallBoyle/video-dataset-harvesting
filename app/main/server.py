from flask import Flask

from main.utils.db import construct_db
from main.views import blueprints

app = Flask('Video Harvesting', template_folder='app/main/templates', static_folder='app/static')


def main():
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    construct_db()

    app.run(host='0.0.0.0', port=8000)


if __name__ == '__main__':
    main()
