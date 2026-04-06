from django.urls import path
from .views import FeedView, PresignedUploadView, PublishVideoView, SearchView

urlpatterns = [
    path("uploads/video", PresignedUploadView.as_view(), name="video-presigned-upload"),
    path("videos", PublishVideoView.as_view(), name="video-publish"),
    path("feed", FeedView.as_view(), name="video-feed"),
    path("search", SearchView.as_view(), name="video-search"),
]
