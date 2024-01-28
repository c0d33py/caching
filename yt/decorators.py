import functools
import hashlib

from django.core.cache import cache
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential


class YouTubeAPIClientException(Exception):
    pass


def _get_cache_key(self, *args, **kwargs):
    args_str = ", ".join(repr(arg) for arg in args)
    kwargs_str = ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
    cache_key = f"youtube_api_client_{hashlib.sha1((args_str + kwargs_str).encode('utf-8')).hexdigest()}"
    return cache_key


def cached_api_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = _get_cache_key(*args, **kwargs)
        cached_response = cache.get(cache_key)

        if cached_response is not None:
            return cached_response

        response = func(*args, **kwargs)
        cache.set(cache_key, response, youtube_api_client.cache_timeout)
        return response

    return wrapper


def retry_api_call(func):
    @functools.wraps(func)
    @retry(
        stop=stop_after_attempt(youtube_api_client.max_retries),
        wait=wait_exponential(
            multiplier=youtube_api_client.backoff_factor, min=1, max=60
        ),
        reraise=True,
    )
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            raise YouTubeAPIClientException(e)

    return wrapper
