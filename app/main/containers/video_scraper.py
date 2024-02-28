from .base import Base
from main.config import config
from main.utils.http import download_file, get


class VideoScraper(Base):

    def __init__(self):
        super().__init__(name=config.VIDEO_SCRAPER_NAME, port=config.VIDEO_SCRAPER_PORT)

    def get_channel_urls(self, channel_id):
        print(f'Getting video URLs for channel ID: {channel_id}')
        response = get(endpoint=f'{self.api}/urls/channel/{channel_id}')

        return response.json()

    def get_playlist_urls(self, playlist_id):
        print(f'Getting video URLs for playlist ID: {playlist_id}')
        response = get(endpoint=f'{self.api}/urls/playlist/{playlist_id}')

        return response.json()

    def get_user_urls(self, user_id):
        print(f'Getting video URLs for user ID: {user_id}')
        response = get(endpoint=f'{self.api}/urls/user/{user_id}')

        return response.json()

    def download_video(self, url):
        print(f'Downloading video at URL: {url}')

        return download_file(endpoint=f'{self.api}/videos/download',
                             json={'url': url})
