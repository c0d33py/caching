from django.db import models


class DevKey(models.Model):
    key = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    reason = models.JSONField(
        default=dict, help_text="Reason for disabling the key", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dev_key"
        verbose_name = "Developer Key"
        verbose_name_plural = "Developer Keys"
        ordering = ["-created_at"]

    def __str__(self):
        return self.key

    def disable(self, reason):
        self.is_active = False
        self.reason = reason
        self.save()

    @classmethod
    def action(cls, action):
        def decorator(func):
            setattr(cls, action, func)
            return func

        return decorator


@DevKey.action("disable")
def dev_key_disabler(instance, validated_data):
    instance.disable(validated_data.get("reason", None))
    return instance


@DevKey.action("enable")
def dev_key_enabler(instance, validated_data):
    instance.is_active = True
    instance.save()
    return instance


@DevKey.action("update")
def dev_key_updater(instance, validated_data):
    instance.key = validated_data.get("key", instance.key)
    instance.save()
    return instance


@DevKey.action("delete")
def dev_key_deleter(instance, validated_data):
    instance.delete()
    return instance
