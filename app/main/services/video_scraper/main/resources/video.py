import glob
import io
import os

from flask import after_this_request, request, send_file
from flask_restx import Namespace, reqparse, Resource

from main import DOWNLOADS_PATH
from main.utils.scraper import Scraper


video_namespace = Namespace('Video',
                            description='API for video retrieval and download',
                            path='/videos')


@video_namespace.route('/download')
class Download(Resource):

    url_parser = reqparse.RequestParser(bundle_errors=True)
    url_parser.add_argument('url', location='json', required=True)

    @video_namespace.expect(url_parser)
    def post(self):
        data = request.json
        url = data['url']

        s = Scraper()
        zip_path = s.download_video(url=url)

        # store zip in memory to delete from disk
        return_data = io.BytesIO()
        with open(zip_path, 'rb') as f:
            return_data.write(f.read())
        return_data.seek(0)

        os.remove(zip_path)

        @after_this_request
        def clean_up_downloads(response):
            # make sure directory clean - even if there is an error
            for file in glob.glob(os.path.join(DOWNLOADS_PATH, '*')):
                os.remove(file)

            return response

        return send_file(return_data, as_attachment=True, attachment_filename='video.zip')
