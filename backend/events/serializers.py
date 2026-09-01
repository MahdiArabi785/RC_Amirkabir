# events/serializers.py
from rest_framework import serializers

from .models import Call, Event, News


# -------------------- سریالایزر خبر --------------------
class NewsSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            'id', 'slug', 'title', 'summary', 'content',
            'cover_image', 'cover_image_url', 'source',
            'is_published', 'published_at', 'view_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'view_count', 'published_at', 'created_at', 'updated_at']

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None


# -------------------- سریالایزر رویداد --------------------
class EventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'slug', 'title', 'summary', 'content',
            'event_type', 'event_type_display',
            'start_date', 'end_date', 'location',
            'cover_image', 'cover_image_url',
            'capacity', 'registration_deadline',
            'is_published', 'published_at', 'view_count',
            'is_upcoming', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'view_count', 'published_at', 'created_at', 'updated_at']

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_is_upcoming(self, obj):
        return obj.is_upcoming()

    def validate(self, attrs):
        # قبلاً هیچ اعتبارسنجی‌ای بین start_date/end_date وجود نداشت،
        # یعنی می‌شد رویدادی با تاریخ پایان قبل از تاریخ شروع ساخت.
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {'end_date': 'تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.'}
            )

        registration_deadline = attrs.get(
            'registration_deadline', getattr(self.instance, 'registration_deadline', None)
        )
        if registration_deadline and start_date and registration_deadline > start_date:
            raise serializers.ValidationError(
                {'registration_deadline': 'مهلت ثبت‌نام نمی‌تواند بعد از تاریخ شروع رویداد باشد.'}
            )
        return attrs


# -------------------- سریالایزر فراخوان --------------------
class CallSerializer(serializers.ModelSerializer):
    call_type_display = serializers.CharField(source='get_call_type_display', read_only=True)
    document_url = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Call
        fields = [
            'id', 'slug', 'title', 'summary', 'content',
            'call_type', 'call_type_display',
            'deadline', 'contact_email', 'contact_phone',
            'document', 'document_url',
            'is_published', 'published_at', 'view_count',
            'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'view_count', 'published_at', 'created_at', 'updated_at']

    def get_document_url(self, obj):
        request = self.context.get('request')
        if obj.document and request:
            return request.build_absolute_uri(obj.document.url)
        return None

    def get_is_expired(self, obj):
        return obj.is_expired()