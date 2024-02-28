from flask_restx import Namespace, Resource

from main.utils.scraper import Scraper

url_namespace = Namespace('URL',
                          description='API for video URLS',
                          path='/urls')


@url_namespace.route('/channel/<id>')
class Channel(Resource):

    def get(self, id):
        s = Scraper()
        video_urls = s.get_channel_video_urls(_id=id)

        return video_urls


@url_namespace.route('/playlist/<id>')
class Playlist(Resource):

    def get(self, id):
        s = Scraper()
        video_urls = s.get_playlist_video_urls(_id=id)

        return video_urls


@url_namespace.route('/user/<id>')
class User(Resource):

    def get(self, id):
        s = Scraper()
        video_urls = s.get_user_video_urls_v2(_id=id)

        return video_urls
