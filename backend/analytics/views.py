from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnalyticsEvent


class BatchEventView(APIView):
    """Ingest a batch of analytics events in a single request."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        events_data = request.data.get("events")
        if not isinstance(events_data, list) or len(events_data) == 0:
            return Response(
                {"detail": "events must be a non-empty list."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(events_data) > 500:
            return Response(
                {"detail": "Maximum 500 events per request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        to_create = []
        for item in events_data:
            to_create.append(
                AnalyticsEvent(
                    user=request.user,
                    video_id=item.get("video"),
                    event_type=item.get("event_type", ""),
                    payload=item.get("payload", {}),
                )
            )
        AnalyticsEvent.objects.bulk_create(to_create, ignore_conflicts=True)
        return Response({"created": len(to_create)}, status=status.HTTP_201_CREATED)
