import os
import re
import zipfile

from youtube_dl import YoutubeDL

from main import DOWNLOADS_PATH

YOUTUBE_VIDEO_URL_REGEX = r'.+watch\?v=.+'


class Logger:

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def hook(d):
    pass


def find(key, dictionary):
    for k, v in dictionary.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict):
                    for result in find(key, d):
                        yield result


EXTENSIONS = ['en.vtt', 'info.json', 'mp4', 'wav']
ARC_NAMES = ['transcript', 'data', 'video', 'audio']


class Scraper:
    """
    /channel/<id>: <id> is a unique ID made up of random letters and numbers. This is standard for channels
    /c/<id>: <id> can custom e.g. TheOfficeUS. Easier to share with others
    /user/<id>: legacy URL. Older channels may have usernames.
    /<id>: this is the best way to find channels by user e.g. TheOfficeUS. It resolves to /c and /user
    """

    def __init__(self):
        self.options = {
            'format': 'best',
            'outtmpl': os.path.join(DOWNLOADS_PATH, f'%(id)s.mp4'),
            'writeinfojson': True,
            'prefer_ffmpeg': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'keepvideo': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'logger': Logger(),
            'progress_hooks': [hook],
            'quiet': True
        }

    def download_video(self, url):
        with YoutubeDL(self.options) as dl:
            dl.download([url])

            # extract video id
            video_info = dl.extract_info(url, download=False)
            video_id = video_info['id']

            video_path = os.path.join(DOWNLOADS_PATH, f'{video_id}')
            video_files = [f'{video_path}.{extension}' for extension in EXTENSIONS]

            # zip files together
            video_zip_path = f'{video_path}.zip'
            with zipfile.ZipFile(video_zip_path, 'w') as f:
                for i, video_file in enumerate(video_files):
                    if os.path.exists(video_file):
                        f.write(video_file, arcname=f'{ARC_NAMES[i]}.{EXTENSIONS[i]}')

            # free up storage
            for video_file in video_files:
                if os.path.exists(video_file):
                    os.remove(video_file)

            return video_zip_path

    def extract_urls(self, url):
        with YoutubeDL() as ydl:
            channel_info = ydl.extract_info(url, download=False)

        webpage_urls = list(find('webpage_url', channel_info))  # recursively search for the key
        webpage_urls = list(set(webpage_urls))  # remove duplicates
        video_urls = [
            url for url in webpage_urls
            if re.match(YOUTUBE_VIDEO_URL_REGEX, url)
        ]

        return video_urls

    def get_channel_video_urls(self, _id):
        url = f'http://youtube.com/channel/{_id}'

        return self.extract_urls(url)

    def get_playlist_video_urls(self, _id):
        url = f'http://youtube.com/playlist?list={_id}'

        return self.extract_urls(url)

    def get_user_video_urls(self, _id):
        url = f'http://youtube.com/user/{_id}'

        return self.extract_urls(url)

    def get_user_video_urls_v2(self, _id):
        url = f'http://youtube.com/{_id}'

        return self.extract_urls(url)
