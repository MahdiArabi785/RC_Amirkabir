# =============================================================================
# managements/serializers.py
# سریالایزرهای مدیریتی با استفاده از مدل‌های صحیح
# =============================================================================

from rest_framework import serializers
from django.contrib.auth import get_user_model

# مدل‌های accounts
from accounts.models import Article, ResearchProject
# مدل Course از courses (با ویدیوها)
from courses.models import Course
# مدل‌های events
from events.models import Event, Call, News
# مدل‌های guides و sitesettings
from guides.models import Guide
from sitesettings.models import Banner, SiteSettings

from .models import ActivityLog, ManagementSetting

User = get_user_model()


# ==================== کاربران ====================
class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'full_name', 'avatar',
            'role', 'role_display', 'is_admin', 'is_active',
            'is_verified', 'is_superuser', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_superuser', 'is_admin']


class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'full_name', 'first_name', 'last_name',
            'avatar', 'role', 'role_display', 'is_admin', 'is_active',
            'is_verified', 'is_superuser', 'bio', 'organization',
            'field_of_study', 'website', 'linkedin', 'google_scholar',
            'date_joined', 'last_login', 'activity_logs_enabled'
        ]
        read_only_fields = ['id', 'is_superuser', 'date_joined', 'last_login', 'is_admin']


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8, allow_blank=True)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'email', 'phone', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'is_verified', 'bio', 'organization',
            'field_of_study', 'website', 'linkedin', 'google_scholar',
            'password', 'confirm_password'
        ]

    def validate(self, attrs):
        password = attrs.get('password')
        confirm = attrs.get('confirm_password')
        if password and password != confirm:
            raise serializers.ValidationError({"confirm_password": "رمز عبور و تکرار آن مطابقت ندارند."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# ==================== مقالات (accounts) ====================
class ArticleManagementSerializer(serializers.ModelSerializer):
    authors_names = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'abstract', 'content', 'authors', 'authors_names',
            'created_by', 'created_by_name', 'status', 'status_display',
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_authors_names(self, obj):
        return [author.get_full_name() or author.email for author in obj.authors.all()]


# ==================== پروژه‌های تحقیقاتی (accounts) ====================
class ResearchProjectManagementSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source='lead.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ResearchProject
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


# ==================== دوره‌ها (courses) ====================
class CourseManagementSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    students_count = serializers.IntegerField(source='students.count', read_only=True)
    videos_count = serializers.IntegerField(source='videos.count', read_only=True)

    class Meta:
        model = Course  # از courses.models
        fields = [
            'id', 'title', 'slug', 'description', 'thumbnail',
            'teacher', 'teacher_name', 'students', 'students_count',
            'videos_count', 'start_date', 'end_date',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


# ==================== رویدادها (events) ====================
class EventManagementSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    is_upcoming = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'view_count']

    def get_is_upcoming(self, obj):
        return obj.is_upcoming()


class CallManagementSerializer(serializers.ModelSerializer):
    call_type_display = serializers.CharField(source='get_call_type_display', read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Call
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'view_count']

    def get_is_expired(self, obj):
        return obj.is_expired()


class NewsManagementSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'view_count']

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None


# ==================== راهنماها (guides) ====================
class GuideManagementSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Guide
        fields = [
            'id', 'title', 'description', 'file', 'file_url', 'file_size',
            'is_active', 'download_count', 'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'download_count', 'uploaded_at', 'updated_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_file_size(self, obj):
        try:
            return obj.file.size if obj.file else 0
        except (FileNotFoundError, OSError):
            return None


# ==================== بنرها و تنظیمات سایت (sitesettings) ====================
class BannerManagementSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class SiteSettingsSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()

    class Meta:
        model = SiteSettings
        fields = ['site_name', 'tagline', 'logo', 'logo_url', 'favicon', 'favicon_url', 'updated_at']
        read_only_fields = ['updated_at']

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_favicon_url(self, obj):
        request = self.context.get('request')
        if obj.favicon and request:
            return request.build_absolute_uri(obj.favicon.url)
        return None


# ==================== لاگ و تنظیمات مدیریت ====================
class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = ActivityLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']


class ManagementSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementSetting
        fields = ['id', 'key', 'value', 'description', 'updated_at']
        read_only_fields = ['id', 'updated_at']