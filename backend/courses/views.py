# courses/views.py
import os

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Course, Video
from .serializers import CourseDetailSerializer, CourseListSerializer, VideoSerializer
from .utils import VideoStreamer


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ویو برای دوره‌ها (فقط خواندنی)
    """
    queryset = Course.objects.filter(is_active=True)
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    @action(detail=True, methods=['get'], url_path='videos')
    def course_videos(self, request, slug=None):
        """برگرداندن لیست ویدیوهای یک دوره به صورت جداگانه"""
        course = self.get_object()
        videos = course.videos.all()
        # قبلاً context (شامل request) به این سریالایزر پاس داده
        # نمی‌شد؛ یعنی هر فیلد URL مطلق (video_url/thumbnail_url) در
        # همین endpoint خاص همیشه None برمی‌گشت، برخلاف list/retrieve
        # معمولی دوره که context را خودکار از get_serializer() می‌گیرند.
        serializer = VideoSerializer(videos, many=True, context=self.get_serializer_context())
        return Response(serializer.data)


class VideoStreamView(generics.GenericAPIView):
    """
    ویو مخصوص استریم فایل ویدیو
    """

    def get(self, request, video_id):
        # قبلاً get_object_or_404(Video, id=video_id) بدون فیلتر روی
        # وضعیت دوره بود - یعنی حتی اگر دوره‌ای غیرفعال (is_active=False)
        # می‌شد، ویدیوهایش با شناسه‌ی مستقیم همچنان قابل استریم بودند و
        # کنترل دسترسی CourseViewSet (که فقط دوره‌های فعال را نشان
        # می‌دهد) عملاً دور زده می‌شد.
        video = get_object_or_404(Video, id=video_id, course__is_active=True)

        if not video.video_file:
            raise Http404("فایل ویدیو یافت نشد")

        try:
            file_path = video.video_file.path
        except NotImplementedError:
            # storage backend ای که مسیر فایل‌سیستمی ندارد (مثلاً S3) -
            # استریم Range-based این کد فقط با فایل‌سیستم محلی کار می‌کند.
            raise Http404("این ویدیو با استریم مستقیم فایل سازگار نیست.")

        if not os.path.exists(file_path):
            raise Http404("فایل ویدیو یافت نشد")

        range_header = request.headers.get('Range')
        streamer = VideoStreamer(file_path, range_header)
        return streamer.stream_response()