from typing import Dict, List, Union

import requests
from timedelta_isoformat import timedelta


def get_batch_size(_list: List[str], batch_size: int = 10) -> List[List[str]]:
    return [_list[i : i + batch_size] for i in range(0, len(_list), batch_size)]


def parse_iso8601_duration(duration: str):
    if duration is None:
        return None

    try:
        duration_components = timedelta.fromisoformat(duration)
    except (ValueError, TypeError):
        duration_components = duration

    return duration_components


class NoKeyClient:
    BASE_URL = 'https://yt.lemnoslife.com/noKey/'

    def __init__(self):
        self.session = requests.Session()

    def _create_client(self, query: str, params: dict) -> Union[Dict, str]:
        url = self.BASE_URL + query
        response = self.session.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            return f"Error in API request: {response.status_code} {response.text}"

    def _search(self, channel_id: str) -> Union[List[Dict], str]:
        query = 'search'
        params = {
            'channelId': channel_id,
            'part': 'id',
            'order': 'date',
            'maxResults': 50,
            'publishedAfter': '2024-02-03T00:00:00Z',
            'publishedBefore': '2024-02-03T23:59:59Z',
        }

        try:
            items = self._get_all_items(query, params)
            video_ids = [item.get('id', {}).get('videoId', None) for item in items]
            return self._get_video_details_by_id(video_ids)

        except requests.exceptions.RequestException as e:
            return f"Error in API request: {str(e)}"
        except KeyError as ke:
            return f"KeyError: {str(ke)}"

    def _get_all_items(self, url: str, params: dict) -> List[Dict]:
        items_list = []
        next_page_token = None

        while True:
            if next_page_token:
                params['pageToken'] = next_page_token

            response = self._create_client(url, params)

            if isinstance(response, str):
                return response

            items = response.get('items', [])
            next_page_token = response.get('nextPageToken', None)

            if not items:
                break

            items_list.extend(items)

            if not next_page_token:
                break

        return items_list

    def _get_video_details_by_id(self, video_ids: List[str]) -> List[dict]:
        video_details = []

        for current_batch in get_batch_size(video_ids):
            print('current_batch', current_batch)

            query = 'videos'
            params = {
                'id': ','.join(current_batch),
                'part': 'snippet,statistics,contentDetails',
            }

            response = self._create_client(query, params)

            if isinstance(response, str):
                return response

            video_details.extend(response.get('items', []))

        return self.get_extract_video_details(video_details)

    def get_extract_video_details(self, videos: List[Dict]) -> List[Dict]:
        extracted_videos = []

        for video in videos:
            video_id = video.get('id', None)
            snippet = video.get('snippet', {})
            statistics = video.get('statistics', {})
            content = video.get('contentDetails', {})
            print('content', content)
            if video_id:
                extracted_videos.append(
                    {
                        'id': video_id,
                        'title': snippet.get('title', None),
                        'published_at': snippet.get('publishedAt', None),
                        'channel_title': snippet.get('channelTitle', None),
                        'thumbnail': snippet.get('thumbnails', {})
                        .get('medium', {})
                        .get('url', None),
                        'duration': parse_iso8601_duration(
                            content.get('duration', None)
                        ),
                        'view_count': statistics.get('viewCount', None),
                        'like_count': statistics.get('likeCount', None),
                        'comment_count': statistics.get('commentCount', None),
                    }
                )

        return extracted_videos
