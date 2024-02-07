import concurrent.futures
import time
from contextlib import contextmanager
from itertools import count, cycle

from django.core.cache import cache
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rest_framework import status
from rest_framework.generics import views
from rest_framework.response import Response

from gclient.models import DevKey

from .helper import NoKeyClient
from .serializers import ChannelSerializers

nokey_client = NoKeyClient()


class YouTubeAPIClient:
    """
    A class to manage the YouTube API client
    """

    API_KEYS_CACHE_KEY = 'api_keys'

    def __init__(self):
        self.api_keys = self._get_api_keys()
        self.youtube_clients = cycle(
            self._create_client(api_key) for api_key in self.api_keys
        )
        self.current_client = next(self.youtube_clients)

    def _get_api_keys(self):
        api_keys = cache.get(self.API_KEYS_CACHE_KEY)
        if api_keys is None:
            api_keys = list(
                DevKey.objects.filter(is_active=True).values_list('key', flat=True)
            )

        cache.set(self.API_KEYS_CACHE_KEY, api_keys)
        return api_keys

    def _create_client(self, api_key):
        return build('youtube', 'v3', developerKey=api_key)

    def _rotate_client(self):
        self.current_client = next(self.youtube_clients)

    # @contextmanager
    # def current_client_context(self):
    #     try:
    #         yield self.current_client
    #     finally:
    #         self.quota_exceeded = False

    # def handle_rate_limit(func):
    #     def wrapper(self, *args, **kwargs):
    #         while True:
    #             with self.current_client_context() as client:
    #                 try:
    #                     return func(client, *args, **kwargs)
    #                 except HttpError as e:
    #                     if e.resp.status == 403 and 'quotaExceeded' in str(e):
    #                         self.quota_exceeded = True
    #                         self._rotate_client()
    #                         time.sleep(20)  # Wait for 60 seconds before trying again
    #                     else:
    #                         raise e

    #     return wrapper

    # @handle_rate_limit
    # def search(self, query, max_results=10):
    #     with self.current_client_context() as client:
    #         return (
    #             client.search()
    #             .list(q=query, part='id,snippet', maxResults=max_results)
    #             .execute()
    #         )

    # @handle_rate_limit
    # def videos(self, video_ids, part='snippet,contentDetails,statistics'):
    #     with self.current_client_context() as client:
    #         return client.videos().list(id=','.join(video_ids), part=part).execute()

    # def search_concurrent(self, queries, max_results=10):
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         futures = [
    #             executor.submit(self.search, query, max_results) for query in queries
    #         ]
    #     responses = [future.result() for future in futures]
    #     return [response['items'] for response in responses]

    # def videos_concurrent(self, video_ids, part='snippet,contentDetails,statistics'):
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         futures = [
    #             executor.submit(self.videos, [video_id], part) for video_id in video_ids
    #         ]
    #     responses = [future.result() for future in futures]
    #     return [response['items'] for response in responses]


class ChannelView(views.APIView):
    """
    API endpoint that allows users to be viewed or edited..
    """

    serializer_class = ChannelSerializers

    def get(self, request):
        return Response(status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            channel_id = serializer.validated_data['channel_id']

            # use _search method to get the data
            data = nokey_client._search(channel_id)
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
