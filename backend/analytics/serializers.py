from rest_framework import serializers
from .models import AnalyticsEvent


class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = ("id", "user", "video", "event_type", "payload", "created_at")
        read_only_fields = ("id", "user", "created_at")


class BatchAnalyticsEventSerializer(serializers.Serializer):
    events = serializers.ListField(child=AnalyticsEventSerializer(), min_length=1, max_length=500)
