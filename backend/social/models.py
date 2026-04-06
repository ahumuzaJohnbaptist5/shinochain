from django.conf import settings
from django.db import models


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_set",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers_set",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_follow"
        unique_together = ("follower", "following")
        constraints = [
            models.CheckConstraint(
                check=~models.Q(follower=models.F("following")),
                name="no_self_follow",
            )
        ]


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    video = models.ForeignKey(
        "videos.Video",
        on_delete=models.CASCADE,
        related_name="likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_like"
        unique_together = ("user", "video")


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    video = models.ForeignKey(
        "videos.Video",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "social_comment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} on {self.video_id}"
