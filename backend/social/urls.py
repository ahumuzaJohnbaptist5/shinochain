from django.urls import path
from .views import CommentListCreateView, FollowView, LikeView

urlpatterns = [
    path("videos/<uuid:pk>/like", LikeView.as_view(), name="video-like"),
    path(
        "videos/<uuid:pk>/comments",
        CommentListCreateView.as_view(),
        name="video-comments",
    ),
    path("users/<int:pk>/follow", FollowView.as_view(), name="user-follow"),
]
