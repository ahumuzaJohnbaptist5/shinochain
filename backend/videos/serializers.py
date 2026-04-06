from rest_framework import serializers
from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    avatar_url = serializers.CharField(source="user.avatar_url", read_only=True)

    class Meta:
        model = Video
        fields = (
            "id",
            "username",
            "avatar_url",
            "caption",
            "hashtags",
            "status",
            "hls_manifest_url",
            "thumbnail_url",
            "duration",
            "views_count",
            "likes_count",
            "comments_count",
            "created_at",
        )
        read_only_fields = (
            "id",
            "username",
            "avatar_url",
            "status",
            "hls_manifest_url",
            "thumbnail_url",
            "views_count",
            "likes_count",
            "comments_count",
            "created_at",
        )


class PublishVideoSerializer(serializers.Serializer):
    upload_key = serializers.CharField()
    caption = serializers.CharField(allow_blank=True, default="")
    hashtags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        default=list,
    )
    duration = serializers.FloatField(required=False, allow_null=True)
