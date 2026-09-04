# =============================================================================
# managements/views.py
# ویوهای مدیریتی کامل برای تمام مدل‌های اپلیکیشن‌های موجود
# این فایل شامل تمام کلاس‌های مورد نیاز برای urls.py است
# =============================================================================

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

# میکسین‌ها و مجوزها
from .mixins import LoggingMixin, ApiResponseMixin
from .permissions import IsAdmin, IsAdminOrReadOnly, IsSuperUser
from .filters import *
from .serializers import *
from .models import ActivityLog, ManagementSetting

# ==================== ایمپورت مدل‌های اپلیکیشن‌های موجود ====================
# از accounts (مدل‌های کاربر، مقاله، پروژه تحقیقاتی)
from accounts.models import CustomUser as User, Article, ResearchProject
# از courses (مدل دوره با ویدیوها) - توجه: اینجا از courses.models استفاده می‌شود
from courses.models import Course
# از events (مدل‌های رویداد، فراخوان، خبر)
from events.models import Event, Call, News
# از guides (مدل راهنما)
from guides.models import Guide
# از sitesettings (مدل‌های بنر و تنظیمات سایت)
from sitesettings.models import Banner, SiteSettings


# ==================== 1. مدیریت کاربران (از accounts) ====================
class UserViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت کامل کاربران (CRUD، مسدودیت، ارتقا سطح، عملیات گروهی)
    """
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['email', 'full_name', 'phone']
    ordering_fields = ['date_joined', 'last_login', 'email']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateUpdateSerializer
        return UserListSerializer

    @action(detail=True, methods=['post'])
    def toggle_block(self, request, pk=None):
        """مسدود/رفع مسدودیت کاربر"""
        user = self.get_object()
        if user == request.user:
            return Response({'detail': 'نمی‌توانید خودتان را مسدود کنید.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save()
        self.log_action('block' if not user.is_active else 'unblock', user)
        return Response(UserDetailSerializer(user).data)

    @action(detail=True, methods=['post'])
    def toggle_admin(self, request, pk=None):
        """ارتقا/تنزل سطح دسترسی به ادمین"""
        user = self.get_object()
        if user == request.user:
            return Response({'detail': 'نمی‌توانید سطح دسترسی خودتان را تغییر دهید.'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role == 'admin':
            user.role = 'user'
            user.is_staff = False
        else:
            user.role = 'admin'
            user.is_staff = True
        user.save()
        self.log_action('promote', user)
        return Response(UserDetailSerializer(user).data)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """حذف گروهی کاربران"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'هیچ کاربری انتخاب نشده است.'}, status=status.HTTP_400_BAD_REQUEST)
        count = User.objects.filter(id__in=ids).count()
        User.objects.filter(id__in=ids).delete()
        self.log_action('bulk_delete', None, {'deleted_count': count})
        return Response({'detail': f'{count} کاربر با موفقیت حذف شدند.'})

    @action(detail=False, methods=['post'])
    def bulk_block(self, request):
        """مسدودیت گروهی کاربران"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'هیچ کاربری انتخاب نشده است.'}, status=status.HTTP_400_BAD_REQUEST)
        count = User.objects.filter(id__in=ids).update(is_active=False)
        self.log_action('bulk_block', None, {'blocked_count': count})
        return Response({'detail': f'{count} کاربر با موفقیت مسدود شدند.'})


# ==================== 2. مدیریت مقالات (از accounts) ====================
class ArticleViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت مقالات (CRUD، انتشار، عدم انتشار، عملیات گروهی)
    """
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleManagementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ArticleFilter
    search_fields = ['title', 'abstract', 'content']
    ordering_fields = ['created_at', 'updated_at', 'published_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.status = 'published'
        article.published_at = timezone.now()
        article.save()
        self.log_action('publish', article)
        return Response(ArticleManagementSerializer(article).data)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        article = self.get_object()
        article.status = 'draft'
        article.published_at = None
        article.save()
        self.log_action('unpublish', article)
        return Response(ArticleManagementSerializer(article).data)

    @action(detail=False, methods=['post'])
    def bulk_publish(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'هیچ مقاله‌ای انتخاب نشده است.'}, status=status.HTTP_400_BAD_REQUEST)
        count = Article.objects.filter(id__in=ids).update(status='published', published_at=timezone.now())
        self.log_action('bulk_publish', None, {'published_count': count})
        return Response({'detail': f'{count} مقاله با موفقیت منتشر شدند.'})

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'هیچ مقاله‌ای انتخاب نشده است.'}, status=status.HTTP_400_BAD_REQUEST)
        count = Article.objects.filter(id__in=ids).count()
        Article.objects.filter(id__in=ids).delete()
        self.log_action('bulk_delete', None, {'deleted_count': count})
        return Response({'detail': f'{count} مقاله با موفقیت حذف شدند.'})


# ==================== 3. مدیریت پروژه‌های تحقیقاتی (از accounts) ====================
class ResearchProjectViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت پروژه‌های تحقیقاتی
    """
    queryset = ResearchProject.objects.all().order_by('-created_at')
    serializer_class = ResearchProjectManagementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_date', 'end_date']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()


# ==================== 4. مدیریت دوره‌ها (از courses) ====================
class CourseViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت دوره‌های آموزشی (با ویدیوها)
    توجه: این مدل از courses.models گرفته شده است
    """
    queryset = Course.objects.all().order_by('-created_at')
    serializer_class = CourseManagementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_date', 'end_date']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()

    @action(detail=True, methods=['get'])
    def videos(self, request, pk=None):
        """دریافت لیست ویدیوهای یک دوره"""
        course = self.get_object()
        videos = course.videos.all()
        from courses.serializers import VideoSerializer
        serializer = VideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)


# ==================== 5. مدیریت رویدادها (از events) ====================
class EventViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت رویدادها
    """
    queryset = Event.objects.all().order_by('-start_date')
    serializer_class = EventManagementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'summary', 'content', 'location']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()


# ==================== 6. مدیریت فراخوان‌ها (از events) ====================
class CallViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت فراخوان‌ها
    """
    queryset = Call.objects.all().order_by('deadline')
    serializer_class = CallManagementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CallFilter
    search_fields = ['title', 'summary', 'content']
    ordering_fields = ['deadline', 'created_at']
    ordering = ['deadline']

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()


# ==================== 7. مدیریت اخبار (از events) ====================
class NewsViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت اخبار
    """
    queryset = News.objects.all().order_by('-published_at')
    serializer_class = NewsManagementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = NewsFilter
    search_fields = ['title', 'summary', 'content']
    ordering_fields = ['published_at', 'created_at']
    ordering = ['-published_at']

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        news = self.get_object()
        news.publish()
        self.log_action('publish', news)
        return Response(NewsManagementSerializer(news).data)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        news = self.get_object()
        news.unpublish()
        self.log_action('unpublish', news)
        return Response(NewsManagementSerializer(news).data)


# ==================== 8. مدیریت راهنماها (از guides) ====================
class GuideViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت فایل‌های راهنما
    """
    queryset = Guide.objects.all().order_by('-uploaded_at')
    serializer_class = GuideManagementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = GuideFilter
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'download_count']
    ordering = ['-uploaded_at']

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()


# ==================== 9. مدیریت بنرها (از sitesettings) ====================
class BannerViewSet(LoggingMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """
    مدیریت بنرهای صفحه اصلی
    """
    queryset = Banner.objects.all().order_by('order', '-created_at')
    serializer_class = BannerManagementSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BannerFilter
    search_fields = ['title', 'subtitle']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        self.log_action('delete', instance)
        instance.delete()


# ==================== 10. تنظیمات سایت (از sitesettings) ====================
class SiteSettingsView(generics.RetrieveUpdateAPIView):
    """
    دریافت و بروزرسانی تنظیمات کلی سایت (Singleton)
    """
    serializer_class = SiteSettingsSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self):
        return SiteSettings.load()


# ==================== 11. لاگ فعالیت‌ها (مدل داخلی) ====================
class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    مشاهده لاگ‌های فعالیت (فقط سوپرادمین)
    """
    queryset = ActivityLog.objects.all().order_by('-timestamp')
    serializer_class = ActivityLogSerializer
    permission_classes = [IsSuperUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user', 'action', 'model_name']
    search_fields = ['object_repr', 'user__email', 'user__full_name']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']


# ==================== 12. تنظیمات مدیریت (مدل داخلی) ====================
class ManagementSettingViewSet(viewsets.ModelViewSet):
    """
    مدیریت تنظیمات پنل مدیریت (فقط سوپرادمین)
    """
    queryset = ManagementSetting.objects.all()
    serializer_class = ManagementSettingSerializer
    permission_classes = [IsSuperUser]
    lookup_field = 'key'


# ==================== 13. داشبورد آمار ====================
class DashboardStatsView(generics.GenericAPIView):
    """
    آمار کلی سیستم برای داشبورد (با کش ۵ دقیقه‌ای)
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        cache_key = 'dashboard_stats'
        data = cache.get(cache_key)

        if data is None:
            now = timezone.now()
            week_ago = now - timedelta(days=7)

            data = {
                # آمار کاربران
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'blocked_users': User.objects.filter(is_active=False).count(),
                'new_users_7d': User.objects.filter(date_joined__gte=week_ago).count(),
                'admins_count': User.objects.filter(role='admin').count(),

                # آمار مقالات
                'total_articles': Article.objects.count(),
                'published_articles': Article.objects.filter(status='published').count(),
                'draft_articles': Article.objects.filter(status='draft').count(),

                # آمار پروژه‌های تحقیقاتی
                'total_research_projects': ResearchProject.objects.count(),

                # آمار دوره‌ها (از courses)
                'total_courses': Course.objects.count(),
                'active_courses': Course.objects.filter(is_active=True).count(),

                # آمار رویدادها
                'total_events': Event.objects.count(),
                'upcoming_events': Event.objects.filter(start_date__gte=now).count(),

                # آمار فراخوان‌ها
                'total_calls': Call.objects.count(),
                'open_calls': Call.objects.filter(deadline__gte=now).count(),

                # آمار اخبار
                'total_news': News.objects.count(),
                'published_news': News.objects.filter(is_published=True).count(),

                # آمار راهنماها
                'total_guides': Guide.objects.count(),
                'total_downloads': Guide.objects.aggregate(Sum('download_count'))['download_count__sum'] or 0,

                # آمار بنرها
                'total_banners': Banner.objects.count(),

                # داده‌های نمودار (۷ روز اخیر)
                'chart_data': {
                    'labels': [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)],
                    'new_users': [
                        User.objects.filter(date_joined__date=(now - timedelta(days=i)).date()).count()
                        for i in range(6, -1, -1)
                    ],
                    'new_articles': [
                        Article.objects.filter(created_at__date=(now - timedelta(days=i)).date()).count()
                        for i in range(6, -1, -1)
                    ],
                },
                'recent_activities': ActivityLogSerializer(
                    ActivityLog.objects.select_related('user')[:10],
                    many=True
                ).data
            }

            # کش به مدت ۵ دقیقه
            cache.set(cache_key, data, 300)

        return Response(data)