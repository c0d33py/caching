from django.urls import path

from .views import index, post_create, posts_clean

urlpatterns = [
    path('', index, name='index'),
    path('create/', post_create, name='post_create'),
    path('clean/', posts_clean, name='posts_clean'),
]
