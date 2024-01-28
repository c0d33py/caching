import logging
import os
import random
import time

import requests
from django.core.cache import cache
from tenacity import RetryError, retry, stop_after_attempts, wait_exponential


class YouTubeAPIClient:
    def __init__(
        self,
        api_keys,
        cache_timeout=3600,
        max_retries=3,
        backoff_factor=2,
    ):
        self.api_keys = api_keys
        self.cache_timeout = cache_timeout
        self.youtube = None
        self._init_client()

    def _init_client(self):
        for api_key in self.api_keys:
            try:
                self.youtube = build('youtube', 'v3', developerKey=api_key)
                break
            except HttpError as e:
                print(f"An HTTP error occurred with key {api_key}: {e}")
                continue

        if not self.youtube:
            raise Exception("None of the API keys work.")

    @retry(
        stop=stop_after_attempts(self.max_retries),
        wait=wait_exponential(multiplier=self.backoff_factor, min=1, max=60),
        reraise=True,
    )
    def _request(self, method, *args, **kwargs):
        cache_key = self._get_cache_key(*args, **kwargs)
        cached_response = cache.get(cache_key)

        if cached_response is not None:
            return cached_response

        response = method(*args, **kwargs)
        cache.set(cache_key, response, self.cache_timeout)
        return response

    def _get_cache_key(self, *args, **kwargs):
        args_str = ", ".join(repr(arg) for arg in args)
        kwargs_str = ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
        return f"youtube_api_client_{hashlib.sha1((args_str + kwargs_str).encode('utf-8')).hexdigest()}"

    def search_videos(self, query, max_results=5):
        return self._request(self._search_videos, query, max_results=max_results)

    @retry(
        stop=stop_after_attempts(self.max_retries),
        wait=wait_exponential(multiplier=self.backoff_factor, min=1, max=60),
        reraise=True,
    )
    def _search_videos(self, query, max_results=5):
        try:
            response = (
                self.youtube.search()
                .list(q=query, part='snippet', maxResults=max_results, type='video')
                .execute()
            )

            videos = []
            for item in response['items']:
                video = {
                    'title': item['snippet']['title'],
                    'id': item['id']['videoId'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                }
                videos.append(video)

            return videos

        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            raise

    def get_video_details(self, video_id):
        return self._request(self._get_video_details, video_id)

    @retry(
        stop=stop_after_attempts(self.max_retries),
        wait=wait_exponential(multiplier=self.backoff_factor, min=1, max=60),
        reraise=True,
    )
    def _get_video_details(self, video_id):
        try:
            response = (
                self.youtube.videos()
                .list(id=video_id, part='snippet,contentDetails,statistics')
                .execute()
            )

            video = response['items'][0]
            details = {
                'title': video['snippet']['title'],
                'published_at': video['snippet']['publishedAt'],
                'channel_title': video['snippet']['channelTitle'],
                'duration': self._convert_duration(video['contentDetails']['duration']),
                'view_count': int(video['statistics']['viewCount']),
                'like_count': int(video['statistics']['likeCount']),
                'dislike_count': int(video['statistics']['dislikeCount']),
                'comment_count': int(video['statistics']['commentCount']),
            }

            return details

        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            raise

    def _convert_duration(self, duration):
        # Convert duration from ISO 8601 format to a more readable format
        # Example: PT1H23M3S -> (1, 23, 3)
        duration_parts = duration.split('PT')[-1].split('H')
        hours = int(duration_parts[0]) if duration_parts[0] else 0
        minutes = int(duration_parts[1].split('M')[0]) if len(duration_parts) > 1 else 0
        seconds = (
            int(duration_parts[1].split('S')[0])
            if len(duration_parts) > 1
            else int(duration_parts[0].split('M')[0])
        )

        return hours, minutes, seconds
