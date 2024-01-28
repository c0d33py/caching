import logging
import os
import random
import time

import requests
from googleapiclient.cache import Cache
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeAPIClient:
    def __init__(
        self,
        api_keys,
        cache_dir=None,
        cache_expiry=3600,
        max_retries=3,
        backoff_factor=2,
    ):
        self.api_keys = api_keys
        self.cache_dir = cache_dir
        self.cache_expiry = cache_expiry
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.youtube = None
        self._init_client()

    def _init_client(self):
        for api_key in self.api_keys:
            try:
                self.youtube = build('youtube', 'v3', developerKey=api_key)
                self._setup_cache()
                break
            except HttpError as e:
                print(f"An HTTP error occurred with key {api_key}: {e}")
                continue

        if not self.youtube:
            raise Exception("None of the API keys work.")

    def _setup_cache(self):
        if self.cache_dir:
            cache = Cache(cache_dir=self.cache_dir, expires_sec=self.cache_expiry)
            self.youtube._http = requests.Session()
            self.youtube._http.mount(
                'https://', requests.adapters.HTTPAdapter(cache=cache)
            )

    def _retry_request(self, func, *args, **kwargs):
        retries = 0
        while retries < self.max_retries:
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                print(f"An HTTP error occurred: {e}")
                retries += 1
                time.sleep(self.backoff_factor * 2**retries)

        raise Exception(f"Request failed after {self.max_retries} retries.")

    def search_videos(self, query, max_results=5):
        return self._retry_request(self._search_videos, query, max_results=max_results)

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
        return self._retry_request(self._get_video_details, video_id)

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
