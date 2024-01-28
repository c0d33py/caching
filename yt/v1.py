import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def search_videos(self, query, max_results=5):
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
            return None

    def get_video_details(self, video_id):
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
            return None

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
