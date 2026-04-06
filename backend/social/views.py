from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from videos.models import Video
from .models import Comment, Follow, Like
from .serializers import CommentSerializer

User = get_user_model()


class LikeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        video = Video.objects.filter(pk=pk).first()
        if video is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        _, created = Like.objects.get_or_create(user=request.user, video=video)
        if created:
            Video.objects.filter(pk=pk).update(likes_count=video.likes_count + 1)
        return Response({"liked": True}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        video = Video.objects.filter(pk=pk).first()
        if video is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        deleted, _ = Like.objects.filter(user=request.user, video=video).delete()
        if deleted:
            Video.objects.filter(pk=pk).update(
                likes_count=max(0, video.likes_count - 1)
            )
        return Response({"liked": False}, status=status.HTTP_200_OK)


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(video_id=self.kwargs["pk"]).select_related("user")

    def perform_create(self, serializer):
        video = Video.objects.filter(pk=self.kwargs["pk"]).first()
        if video is None:
            from rest_framework.exceptions import NotFound
            raise NotFound("Video not found.")
        with transaction.atomic():
            comment = serializer.save(user=self.request.user, video=video)
            Video.objects.filter(pk=self.kwargs["pk"]).update(
                comments_count=video.comments_count + 1
            )
        return comment


class FollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        target = User.objects.filter(pk=pk).first()
        if target is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if target == request.user:
            return Response(
                {"detail": "Cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST
            )
        _, created = Follow.objects.get_or_create(
            follower=request.user, following=target
        )
        if created:
            User.objects.filter(pk=pk).update(
                followers_count=target.followers_count + 1
            )
            User.objects.filter(pk=request.user.pk).update(
                following_count=request.user.following_count + 1
            )
        return Response({"following": True}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        target = User.objects.filter(pk=pk).first()
        if target is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        deleted, _ = Follow.objects.filter(
            follower=request.user, following=target
        ).delete()
        if deleted:
            User.objects.filter(pk=pk).update(
                followers_count=max(0, target.followers_count - 1)
            )
            User.objects.filter(pk=request.user.pk).update(
                following_count=max(0, request.user.following_count - 1)
            )
        return Response({"following": False}, status=status.HTTP_200_OK)
