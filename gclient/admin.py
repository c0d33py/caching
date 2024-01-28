from django.contrib import admin

from .models import DevKey


@admin.register(DevKey)
class DevKeyAdmin(admin.ModelAdmin):
    list_display = ["key", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["key"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "key",
                    "is_active",
                    "reason",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    actions = ["enable", "disable"]

    def enable(self, request, queryset):
        queryset.update(is_active=True)

    enable.short_description = "Enable selected developer keys"

    def disable(self, request, queryset):
        queryset.update(is_active=False)

    disable.short_description = "Disable selected developer keys"
