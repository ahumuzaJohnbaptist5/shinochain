from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Comment, Follow, Like

User = get_user_model()


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    avatar_url = serializers.CharField(source="user.avatar_url", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "username", "avatar_url", "text", "created_at")
        read_only_fields = ("id", "username", "avatar_url", "created_at")


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ("id", "user", "video", "created_at")
        read_only_fields = ("id", "user", "video", "created_at")


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("id", "follower", "following", "created_at")
        read_only_fields = ("id", "follower", "following", "created_at")
