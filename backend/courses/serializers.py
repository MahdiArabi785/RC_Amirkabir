# courses/serializers.py
from rest_framework import serializers

from .models import Course, Video


class VideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'video_file', 'video_url',
            'thumbnail', 'thumbnail_url', 'order', 'duration', 'created_at'
        ]
        read_only_fields = ['created_at']

    def get_video_url(self, obj):
        # قبلاً فقط مسیر نسبی فایل (video_file) برمی‌گشت. سایر اپ‌های
        # همین پروژه (accounts/events/guides) همیشه یک URL کامل و
        # مستقیماً قابل‌استفاده برمی‌گردانند - برای هماهنگی و چون فرانت
        # باید دقیقاً بداند برای استریم/دانلود کجا درخواست بزند، همین
        # الگو اینجا هم اضافه شد.
        request = self.context.get('request')
        if obj.video_file and request:
            return request.build_absolute_uri(obj.video_file.url)
        return None

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None


class CourseListSerializer(serializers.ModelSerializer):
    """سریالایزر مختصر برای لیست دوره‌ها"""
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'description', 'thumbnail', 'thumbnail_url', 'created_at', 'is_active']

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None


class CourseDetailSerializer(serializers.ModelSerializer):
    """سریالایزر کامل با ویدیوهای مرتبط"""
    videos = VideoSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description',
            'thumbnail', 'thumbnail_url', 'videos', 'created_at',
            'updated_at', 'is_active'
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None