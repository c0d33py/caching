from django.db import models
from django.db.models.query import QuerySet

from redis_tut.cache import (
    set_contribution_revenue_cache_decorator,
    set_emission_rate_cache_decorator,
)


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CategoryEmissionRatesQuerySet(QuerySet):
    @set_emission_rate_cache_decorator
    @set_contribution_revenue_cache_decorator
    def update(self, **kwargs):
        return super().update(**kwargs)

    @set_emission_rate_cache_decorator
    @set_contribution_revenue_cache_decorator
    def create(self, **kwargs):
        return super().create(**kwargs)

    @set_emission_rate_cache_decorator
    @set_contribution_revenue_cache_decorator
    def delete(self):
        return super().delete()


class CategoryEmissionRates(models.Model):
    objects = CategoryEmissionRatesQuerySet.as_manager()

    category = models.CharField(max_length=100)
    emission_rate = models.FloatField()
    green_house_contribution = models.FloatField()

    class Meta:
        db_table = "category_emission_rates"

    def __str__(self):
        return f"{self.category} - {self.emission_rate}"

    @set_emission_rate_cache_decorator
    @set_contribution_revenue_cache_decorator
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    @set_emission_rate_cache_decorator
    @set_contribution_revenue_cache_decorator
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)
