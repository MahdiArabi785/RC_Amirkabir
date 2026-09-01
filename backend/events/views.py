# events/views.py
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .filters import CallFilter, EventFilter, NewsFilter
from .models import Call, Event, News
from .permissions import IsAdminOrReadOnly
from .serializers import CallSerializer, EventSerializer, NewsSerializer


def _can_see_unpublished(user):
    """معادل is_admin در accounts، با fallback امن به is_staff - همان
    معیاری که در permissions.IsAdminOrReadOnly استفاده شده تا سیاست
    یکسان بماند."""
    return bool(user and user.is_authenticated and getattr(user, 'is_admin', user.is_staff))


class ApiResponseMixin:
    """پاسخ یکپارچه {success, message, data/errors} برای عملیات نوشتنی.

    قبلاً فقط create() این قالب را داشت و update/partial_update همان
    خروجی خام پیش‌فرض DRF را برمی‌گرداندند - یعنی فرانت باید برای هر
    عملیات یک شکل پاسخ متفاوت را مدیریت می‌کرد. الان create/update هر دو
    یک شکل دارند. list/retrieve/destroy عمداً طبق قرارداد استاندارد DRF
    باقی مانده‌اند (retrieve پایین سفارشی شده فقط برای شمارش بازدید، نه
    برای تغییر قالب پاسخ؛ destroy همان 204 No Content استاندارد را
    برمی‌گرداند چون افزودن body به یک پاسخ 204 با HTTP مغایرت دارد)."""

    def get_serializer_errors(self, serializer):
        # قبلاً فقط اولین پیام خطای هر فیلد نگه داشته می‌شد
        # (value[0])؛ اگر یک فیلد چند خطای اعتبارسنجی همزمان داشت،
        # بقیه‌ی پیام‌ها گم می‌شدند.
        return {field: [str(e) for e in errors] for field, errors in serializer.errors.items()}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({
                'success': True,
                'message': 'با موفقیت ایجاد شد',
                'data': serializer.data,
            }, status=status.HTTP_201_CREATED, headers=headers)
        return Response({
            'success': False,
            'errors': self.get_serializer_errors(serializer),
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                'success': True,
                'message': 'با موفقیت به‌روزرسانی شد',
                'data': serializer.data,
            })
        return Response({
            'success': False,
            'errors': self.get_serializer_errors(serializer),
        }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        # قبلاً view_count هرگز افزایش پیدا نمی‌کرد - فیلدش در مدل و
        # سریالایزر بود ولی هیچ‌جا صدا زده نمی‌شد. اینجا هر بار کسی
        # جزئیات یک خبر/رویداد/فراخوان را می‌بیند، شمارنده به‌صورت
        # اتمیک (F expression، نه read-then-write) زیاد می‌شود.
        instance = self.get_object()
        instance.increase_view()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PublishActionsMixin:
    """اکشن‌های publish/unpublish - از متدهای publish()/unpublish() که
    روی PublishMixin مدل تعریف شده استفاده می‌کند (قبلاً این متدها در
    models.py وجود داشتند ولی هیچ endpoint ای صدایشان نمی‌زد)."""

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def publish(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.publish()
        return Response({
            'success': True,
            'message': 'با موفقیت منتشر شد',
            'data': self.get_serializer(obj).data,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def unpublish(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.unpublish()
        return Response({
            'success': True,
            'message': 'از انتشار خارج شد',
            'data': self.get_serializer(obj).data,
        })


# -------------------- ویو ست خبر --------------------
class NewsViewSet(ApiResponseMixin, PublishActionsMixin, viewsets.ModelViewSet):
    queryset = News.objects.filter(is_active=True)
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = NewsFilter
    search_fields = ['title', 'summary', 'content']
    ordering_fields = ['published_at', 'view_count']
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = News.objects.filter(is_active=True)
        if _can_see_unpublished(self.request.user):
            return queryset
        return queryset.filter(is_published=True)


# -------------------- ویو ست رویداد --------------------
class EventViewSet(ApiResponseMixin, PublishActionsMixin, viewsets.ModelViewSet):
    queryset = Event.objects.filter(is_active=True)
    serializer_class = EventSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'summary', 'content']
    ordering_fields = ['start_date', 'view_count']
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Event.objects.filter(is_active=True)
        if _can_see_unpublished(self.request.user):
            return queryset
        return queryset.filter(is_published=True)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        queryset = self.get_queryset().filter(start_date__gte=timezone.now()).order_by('start_date')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# -------------------- ویو ست فراخوان --------------------
class CallViewSet(ApiResponseMixin, PublishActionsMixin, viewsets.ModelViewSet):
    queryset = Call.objects.filter(is_active=True)
    serializer_class = CallSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CallFilter
    search_fields = ['title', 'summary', 'content']
    ordering_fields = ['deadline', 'view_count']
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Call.objects.filter(is_active=True)
        if _can_see_unpublished(self.request.user):
            return queryset
        return queryset.filter(is_published=True)

    @action(detail=False, methods=['get'])
    def open_calls(self, request):
        queryset = self.get_queryset().filter(deadline__gte=timezone.now()).order_by('deadline')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)