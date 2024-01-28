from typing import Any, Dict, List, Tuple

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from decorators import cached_api_call, retry_api_call


class YouTubeAPIClient:
    def __init__(
        self,
        api_keys: List[str],
        cache_timeout: int = 3600,
        max_retries: int = 3,
        backoff_factor: int = 2,
    ):
        # Create a dictionary of API clients using the provided keys.
        # If an API client fails to initialize, try the next key.
        # If none of the keys work, raise an exception.

        self.api_keys = api_keys
        self.cache_timeout = cache_timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
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

    @retry_api_call
    @cached_api_call
    def _search_videos(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
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

    @retry_api_call
    @cached_api_call
    def _get_video_details(self, video_id: str) -> Dict[str, Any]:
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

    def _convert_duration(self, duration: str) -> Tuple[int, int, int]:
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

    def search_videos(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        return self._search_videos(query, max_results=max_results)

    def get_video_details(self, video_id: str) -> Dict[str, Any]:
        return self._get_video_details(video_id)
