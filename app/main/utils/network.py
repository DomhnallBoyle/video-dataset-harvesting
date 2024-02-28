import socket
from contextlib import closing

from main import config


def is_socket_open(port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((config.HOST, port)) == 0:
            return True

        return False
