from django.core.cache import cache
from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        cache.delete('posts')
        super().save(*args, **kwargs)


class CategoryEmissionRates(models.Model):
    category = models.CharField(max_length=100)
    emission_rate = models.FloatField()
    green_house_contribution = models.FloatField()

    class Meta:
        db_table = "category_emission_rates"

    def __str__(self):
        return f"{self.category} - {self.emission_rate}"
        return f"{self.category} - {self.emission_rate}"
