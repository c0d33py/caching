from rest_framework import serializers


class ChannelSerializers(serializers.Serializer):
    channel_id = serializers.CharField(max_length=100)

    class Meta:
        fields = '__all__'
