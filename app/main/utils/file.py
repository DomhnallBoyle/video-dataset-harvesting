import json
import os


def initialise_dirs(dirs):
    for dir in dirs:
        if not os.path.exists(dir):
            os.mkdir(dir)


class File:

    def __init__(self, path):
        self.path = path

    def delete(self):
        os.remove(path=self.path)

    def read(self, mode='rb'):
        with open(self.path, mode) as f:
            return f.read()

    def write(self, text):
        with open(self.path, 'w') as f:
            f.write(text)


class JSONFile(File):

    def __init__(self, path):
        super().__init__(path=path)

    def read(self, mode='r'):
        with open(self.path, mode) as f:
            return json.load(f)

    def write(self, j):
        with open(self.path, 'w') as f:
            json.dump(j, f)
