from operator import is_

from django.core.cache import cache
from django.db import models


class PostManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class ActiveModelMixin(models.Model):
    is_active = models.BooleanField(default=True)

    objects = PostManager()

    class Meta:
        abstract = True


class CachedModelManager(models.Manager):
    def get_queryset(self):
        cache_key = f"{self.model.__name__.lower()}_qs"
        qs = cache.get(cache_key)
        if not qs:
            qs = super().get_queryset()
            cache.set(cache_key, qs)
        return qs

    def create(self, *args, **kwargs):
        cache.delete(f"{self.model.__name__.lower()}_qs")
        return super().create(*args, **kwargs)

    def update(self, *args, **kwargs):
        cache.delete(f"{self.model.__name__.lower()}_qs")
        return super().update(*args, **kwargs)

    def delete(self, *args, **kwargs):
        cache.delete(f"{self.model.__name__.lower()}_qs")
        return super().delete(*args, **kwargs)

    def bulk_create(self, *args, **kwargs):
        cache.delete(f"{self.model.__name__.lower()}_qs")
        return super().bulk_create(*args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        cache.delete(f"{self.model.__name__.lower()}_qs")
        return super().bulk_update(*args, **kwargs)

    def bulk_delete(self, *args, **kwargs):
        cache.delete(f"{self.model.__name__.lower()}_qs")
        return super().bulk_delete(*args, **kwargs)

    def get_or_create(self, *args, **kwargs):
        cache.delete(f"{self.model.__name__.lower()}_qs")
        return super().get_or_create(*args, **kwargs)

    def update_or_create(self, *args, **kwargs):
        cache.delete(f"{self.model.__name__.lower()}_qs")
        return super().update_or_create(*args, **kwargs)

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class Post(ActiveModelMixin, models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CachedModelManager()

    def __str__(self):
        return self.title


class CategoryEmissionRates(models.Model):
    category = models.CharField(max_length=100)
    emission_rate = models.FloatField()
    green_house_contribution = models.FloatField()

    class Meta:
        db_table = "category_emission_rates"

    def __str__(self):
        return f"{self.category} - {self.emission_rate}"
        return f"{self.category} - {self.emission_rate}"
