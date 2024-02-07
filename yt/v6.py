import time
from itertools import cycle

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeAPIClient:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.youtube_clients = cycle(
            self.create_client(api_key) for api_key in self.api_keys
        )
        self.current_client = next(self.youtube_clients)
        self.quota_exceeded = False

    def create_client(self, api_key):
        return build('youtube', 'v3', developerKey=api_key)

    def rotate_client(self):
        self.current_client = next(self.youtube_clients)
        self.quota_exceeded = False

    def handle_rate_limit(func):
        def wrapper(self, *args, **kwargs):
            while True:
                try:
                    return func(self, *args, **kwargs)
                except HttpError as e:
                    if e.resp.status == 403 and 'quotaExceeded' in str(e):
                        self.quota_exceeded = True
                        self.rotate_client()
                        time.sleep(60)  # Wait for 60 seconds before trying again
                    else:
                        raise e

        return wrapper

    @handle_rate_limit
    def search(self, query, max_results=10):
        response = (
            self.current_client.search()
            .list(q=query, part='id,snippet', maxResults=max_results)
            .execute()
        )
        return response['items']

    @handle_rate_limit
    def get_video_details(self, video_id):
        response = (
            self.current_client.videos()
            .list(id=video_id, part='snippet,contentDetails,statistics')
            .execute()
        )
        return response['items'][0]
