# guides/serializers.py
from rest_framework import serializers

from .models import Guide


class GuideSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Guide
        fields = [
            'id', 'title', 'description', 'file',
            'file_url', 'file_size', 'is_active', 'download_count',
            'uploaded_at', 'updated_at',
        ]
        read_only_fields = ['id', 'download_count', 'uploaded_at', 'updated_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_file_size(self, obj):
        # قبلاً اگر رکورد در دیتابیس بود ولی فایل فیزیکی از روی
        # دیسک/storage حذف شده بود، obj.file.size یک استثنا پرتاب
        # می‌کرد و کل درخواست (حتی لیست گرفتن راهنماها) با خطای 500
        # می‌ترکید.
        if not obj.file:
            return 0
        try:
            return obj.file.size
        except (FileNotFoundError, OSError):
            return None