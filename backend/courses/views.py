# courses/views.py
import os

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Course, Video
from .serializers import CourseDetailSerializer, CourseListSerializer, VideoSerializer
from .utils import VideoStreamer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """دوره‌های فعال — عمومی برای خواندن."""
    queryset = Course.objects.filter(is_active=True)
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    @action(detail=True, methods=['get'], url_path='videos')
    def course_videos(self, request, slug=None):
        course = self.get_object()
        videos = course.videos.all()
        serializer = VideoSerializer(
            videos, many=True, context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class VideoStreamView(generics.GenericAPIView):
    """استریم عمومی فایل ویدیو (فقط دوره‌های فعال)."""
    permission_classes = [AllowAny]

    def get(self, request, video_id):
        video = get_object_or_404(Video, id=video_id, course__is_active=True)

        if not video.video_file:
            raise Http404("فایل ویدیو یافت نشد")

        try:
            file_path = video.video_file.path
        except NotImplementedError:
            raise Http404("این ویدیو با استریم مستقیم فایل سازگار نیست.")

        if not os.path.exists(file_path):
            raise Http404("فایل ویدیو یافت نشد")

        range_header = request.headers.get('Range')
        streamer = VideoStreamer(file_path, range_header)
        return streamer.stream_response()