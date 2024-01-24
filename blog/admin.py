from django.contrib import admin

from .models import Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'content', 'created_at', 'updated_at')
    list_display_links = ('id', 'title')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_per_page = 25


admin.site.register(Post, PostAdmin)
