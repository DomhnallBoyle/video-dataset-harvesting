import os
import shutil
from os.path import dirname as up, join


def setup_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    return directory_path


class Config:
    PROJECT_PATH = up(up(up(__file__)))
    DOWNLOADS_PATH = setup_directory(join(PROJECT_PATH, 'downloads'))
    DATA_PATH = setup_directory(join(PROJECT_PATH, 'data'))
    HOST = '127.0.0.1'

    # database
    DATABASE_USER = os.environ.get('DATABASE_USER', 'admin')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'password')
    DATABASE_HOST = os.environ.get('DATABASE_HOST', '127.0.0.1')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'dataset')
    DATABASE_URL = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:5432/{DATABASE_NAME}'

    # services
    VIDEO_SCRAPER_NAME = 'video-scraper'
    VIDEO_SCRAPER_PORT = os.getenv('VIDEO_SCRAPER_PORT', 8080)

    SPEECH_RECOGNITION_NAME = 'speech-recognition'
    SPEECH_RECOGNITION_PORT = os.getenv('SPEECH_RECOGNITION_PORT', 8081)

    FORCED_ALIGNMENT_NAME = 'forced-alignment'
    FORCED_ALIGNMENT_PORT = os.getenv('FORCED_ALIGNMENT_PORT', 8082)

    FACE_DETECTION_NAME = 'face-detection'
    FACE_DETECTION_PORT = os.getenv('FACE_DETECTION_PORT', 8083)

    SYNC_NET_NAME = 'sync-net'
    SYNC_NET_PORT = os.getenv('SYNC_NET_PORT', 8084)

    HEAD_POSE_ESTIMATION_NAME = 'hope-net'
    HEAD_POSE_ESTIMATION_PORT = os.getenv('HEAD_POSE_ESTIMATION_PORT', 8085)

    FACE_RECOGNITION_NAME = 'face-net'
    FACE_RECOGNITION_PORT = os.getenv('FACE_RECOGNITION_PORT', 8086)


class DevelopmentConfig(Config):
    DEBUG = True


config = {
    'development': DevelopmentConfig
}[os.getenv('ENVIRONMENT', 'development')]()
