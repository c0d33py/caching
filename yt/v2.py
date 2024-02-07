import concurrent.futures
import time
from contextlib import contextmanager
from functools import partial
from itertools import cycle

from django.core.cache import cache
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gclient.models import DevKey


class YouTubeAPIClient:
    """
    A class to manage the youtube api client
    """

    def __init__(self):
        self.api_keys_cache_key = 'api_keys'
        self.api_keys = self.get_api_keys()
        self.youtube_clients = cycle(
            self.create_client(api_key) for api_key in self.api_keys
        )

        self.current_client = next(self.youtube_clients)
        self.quota_exceeded = False

    def get_api_keys(self):
        """Get the API keys from the cache or query the database."""
        api_keys = cache.get(self.api_keys_cache_key)
        if api_keys is None:
            api_keys = list(DevKey.objects.filter(is_active=True))
            cache.set(self.api_keys_cache_key, [api_key.key for api_key in api_keys])
        return api_keys

    def create_client(self, api_key):
        return build('youtube', 'v3', developerKey=api_key)

    @contextmanager
    def current_client_context(self):
        try:
            yield self.current_client
        finally:
            self.quota_exceeded = False

    def rotate_client(self):
        self.current_client = next(self.youtube_clients)

    def handle_rate_limit(func):
        def wrapper(self, *args, **kwargs):
            while True:
                with self.current_client_context() as client:
                    try:
                        return func(client, *args, **kwargs)
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
        with self.current_client_context() as client:
            return (
                client.search()
                .list(q=query, part='id,snippet', maxResults=max_results)
                .execute()
            )

    @handle_rate_limit
    def videos(self, video_ids, part='snippet,contentDetails,statistics'):
        with self.current_client_context() as client:
            return client.videos().list(id=','.join(video_ids), part=part).execute()

    def search_concurrent(self, queries, max_results=10):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.search, query, max_results) for query in queries
            ]
        responses = [future.result() for future in futures]
        return [response['items'] for response in responses]

    def videos_concurrent(self, video_ids, part='snippet,contentDetails,statistics'):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.videos, [video_id], part) for video_id in video_ids
            ]
        responses = [future.result() for future in futures]
        return [response['items'] for response in responses]
