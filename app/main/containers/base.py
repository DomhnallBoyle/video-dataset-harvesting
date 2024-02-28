import http
import requests
import time
from docker import from_env
from docker.errors import APIError

from main import config

MAX_STATUS_CHECKS = 180


class Base:

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.api = f'http://{config.HOST}:{self.port}'
        try:
            self._ = from_env().containers.get(container_id=name)
        except APIError:
            print(f'Could not find container: {self.name}')
            exit()
        self.start_time = None

    def __enter__(self):
        self.start()
        self.start_time = time.time()

        return self

    def __exit__(self, *args):
        end_time = time.time()
        print(f'Took {int(end_time - self.start_time)} seconds')

        self.stop()

    def is_up(self):
        try:
            r = requests.get(self.api)

            return r.status_code == http.HTTPStatus.OK
        except requests.exceptions.ConnectionError:
            return False

    def is_running(self):
        return self._.status == 'running' and self.is_up()

    def reload(self):
        return self._.reload()

    def start(self):
        print(f'\nStarting container: {self.name}...', end='', flush=True)

        if not self.is_running():
            try:
                self._.start()
                status_check_retries = 0
                while not self.is_running():
                    self.reload()
                    time.sleep(1)
                    status_check_retries += 1
                    if status_check_retries == MAX_STATUS_CHECKS:
                        print(f'Not running after {MAX_STATUS_CHECKS} status '
                              f'checks')
                        exit()
                    print('.', end='', flush=True)
            except APIError:
                print(f'Could not start container: {self.name}')

        print('Done')

    def stop(self):
        print(f'Stopping container: {self.name}...', end='', flush=True)

        if self.is_running():
            try:
                self._.stop()
                self.reload()
            except APIError:
                print(f'Could not stop container: {self.name}')

        print('Done\n')

    # @classmethod
    # def process(cls, f):
    #     def wrapper(self, *args, **kwargs):
    #         self.start()
    #         x = f(self, *args, **kwargs)
    #         self.stop()
    #
    #         return x
    #
    #     return wrapper
