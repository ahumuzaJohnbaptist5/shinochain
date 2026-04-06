from django.conf import settings
from django.db import models


class AnalyticsEvent(models.Model):
    EVENT_VIEW = "view"
    EVENT_LIKE = "like"
    EVENT_SHARE = "share"
    EVENT_COMMENT = "comment"
    EVENT_PLAY = "play"
    EVENT_PAUSE = "pause"
    EVENT_CHOICES = [
        (EVENT_VIEW, "View"),
        (EVENT_LIKE, "Like"),
        (EVENT_SHARE, "Share"),
        (EVENT_COMMENT, "Comment"),
        (EVENT_PLAY, "Play"),
        (EVENT_PAUSE, "Pause"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analytics_events",
    )
    video = models.ForeignKey(
        "videos.Video",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analytics_events",
    )
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_event"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} – {self.created_at}"
