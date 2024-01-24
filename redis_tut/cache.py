import importlib

from django.conf import settings
from django.core.cache import caches


def import_class_from_string(import_path):
    """
    Import class from string
    :param import_path: string
    :return: class
    """
    # if path given is a class type then return it
    if isinstance(import_path, type):
        return import_path
    module_path, class_name = import_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


CACHE_KEY = list(settings.CACHES.keys())
if CACHE_KEY:
    CACHE_KEY = CACHE_KEY[0]
else:
    CACHE_KEY = "default"
redis_cache = caches[CACHE_KEY]
redis_connection = redis_cache.get_client()


class ModelBaseCache:
    hash_name = None
    model_name = None
    qs_values = []
    redis_key_params = None
    redis_value_fields = []

    def __new__(cls, *args, **kwargs):
        if cls is ModelBaseCache:
            raise TypeError("Cache class cannot be instantiated")
        return super().__new__(cls)

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "hash_name") or not cls.hash_name:
            raise ValueError("Sub Class must have hash_name attribute")
        if not hasattr(cls, "model_name") or not cls.model_name:
            raise ValueError("Sub Class must have model_name attribute")
        if not hasattr(cls, "redis_key_params") or not cls.redis_key_params:
            raise ValueError("Sub Class must have key_params attribute")
        if not hasattr(cls, "redis_value_fields") or not cls.redis_value_fields:
            raise ValueError("Sub Class must have value_fields attribute")
        if not hasattr(cls, "qs_values") or not cls.qs_values:
            raise ValueError("Sub Class must have qs_values attribute")

    @classmethod
    def get_key(cls, key, float_conversion=True):
        key = key.lower()
        value = redis_connection.hget(cls.hash_name, key)
        if not value:
            updated_cache = cls.set_cache()
            value = updated_cache.get(key)

        value = value.decode('utf-8') if isinstance(value, bytes) else value
        # conversion is for value to be converted to float
        if value and float_conversion:
            value = float(value)
        return value

    @classmethod
    def prepare_key(cls, value):
        key = ''
        # separate value to by -
        first = True

        for field in cls.redis_key_params:
            if first:
                sep = ''
            else:
                sep = '-'
            key += sep + str(value[field].lower())
            first = False

        return key

    @classmethod
    def prepare_value(cls, value):
        if len(cls.redis_value_fields) == 1:
            return value[cls.redis_value_fields[0]]
        else:
            # return dict of values
            value_dict = {}
            for field in cls.redis_value_fields:
                value_dict[field] = value[field]
            return value_dict

    @classmethod
    def delete_cache(cls):
        redis_connection.delete(cls.hash_name)

    @classmethod
    def set_cache(cls):
        cls.model_name = import_class_from_string(cls.model_name)

        # don't apply decorator on .all() that will create a recursive loop

        qs_data = cls.model_name.objects.all().values(*cls.qs_values)

        fulfillment_rate_dict = {
            cls.prepare_key(value): cls.prepare_value(value) for value in qs_data
        }

        cls.delete_cache()
        for key, value in fulfillment_rate_dict.items():
            redis_connection.hset(cls.hash_name, key, value)

        return fulfillment_rate_dict

    @classmethod
    def set_cache_decorator(cls, func):
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            cls.set_cache()
            return value

        return wrapper


class CategoryEmissionRates(ModelBaseCache):
    hash_name = "CategoryEmissionRates"
    model_name = "model_cache.models.CategoryEmissionRates"
    qs_values = ["category", "emission_rate"]
    redis_key_params = ["category"]
    redis_value_fields = ["emission_rate"]


class CategoryContributionRates(ModelBaseCache):
    hash_name = "CategoryContributionRates"
    model_name = "model_cache.models.CategoryEmissionRates"
    qs_values = ["category", "green_house_contribution"]
    redis_key_params = ["category", "green_house_contribution"]
    redis_value_fields = ["green_house_contribution"]


set_contribution_revenue_cache_decorator = CategoryContributionRates.set_cache_decorator
set_emission_rate_cache_decorator = CategoryEmissionRates.set_cache_decorator
