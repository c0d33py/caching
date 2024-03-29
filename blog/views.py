from django.core import serializers
from django.core.cache import cache
from django.shortcuts import HttpResponse, redirect, render

from .models import Post


def generate_random_posts():
    title = 'This is a new post'
    content = 'This is the content of the new post'
    return Post.objects.create(title=title, content=content)


def index(request):
    posts = cache.get('post_qs')
    if not posts:
        posts = Post.objects.active()

    context = {
        'posts': posts,
    }
    return render(request, 'index.html', context)


def post_create(request):
    post = generate_random_posts()
    print(post)
    return redirect('index')


def posts_clean(request):
    cache.clear()
    return redirect('index')
