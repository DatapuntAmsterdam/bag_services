from rest_framework import serializers

from bag import models


class Autocomplete(serializers.Serializer):
    query = serializers.CharField()
    items = serializers.ListField(child=serializers.CharField())

    def update(self, instance, validated_data):
        raise ValueError("readonly")

    def create(self, validated_data):
        raise ValueError("readonly")


