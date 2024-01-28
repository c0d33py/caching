from django.shortcuts import render
from rest_framework import response, status, views
from rest_framework.generics import views

from .serializers import ChannelSerializers


class ChannelView(views.APIView):
    def post(self, request):
        serializer = ChannelSerializers(data=request.data)
        if serializer.is_valid():
            channel = serializer.save()
            return response.Response(
                {"id": channel.id, "name": channel.name}, status=status.HTTP_201_CREATED
            )
        else:
            return response.Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
        serializer = ChannelSerializers('channels', many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
