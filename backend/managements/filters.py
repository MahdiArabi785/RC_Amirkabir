# =============================================================================
# managements/filters.py
# فیلترهای پیشرفته برای هر مدل با استفاده از django-filter
# =============================================================================

import django_filters
from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Article, Course
from events.models import Event, Call, News
from guides.models import Guide
from sitesettings.models import Banner
from django.utils import timezone

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    full_name = django_filters.CharFilter(field_name='full_name', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    phone = django_filters.CharFilter(field_name='phone', lookup_expr='icontains')
    role = django_filters.ChoiceFilter(choices=User.ROLE_CHOICES)
    is_active = django_filters.BooleanFilter()
    is_verified = django_filters.BooleanFilter()
    date_joined_after = django_filters.DateFilter(field_name='date_joined', lookup_expr='gte')
    date_joined_before = django_filters.DateFilter(field_name='date_joined', lookup_expr='lte')
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'role', 'is_active', 'is_verified']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(full_name__icontains=value) |
            models.Q(email__icontains=value) |
            models.Q(phone__icontains=value)
        )


class ArticleFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Article.STATUS_CHOICES)
    created_at_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    author = django_filters.ModelChoiceFilter(field_name='authors', queryset=User.objects.all())
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = Article
        fields = ['title', 'status', 'author']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(abstract__icontains=value) |
            models.Q(content__icontains=value)
        )


class CourseFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    teacher = django_filters.ModelChoiceFilter(field_name='teacher', queryset=User.objects.all())
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = Course
        fields = ['title', 'is_active', 'teacher']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value)
        )


class EventFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    event_type = django_filters.ChoiceFilter(choices=Event.EventType.choices)
    is_published = django_filters.BooleanFilter()
    start_date_after = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_before = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    is_upcoming = django_filters.BooleanFilter(method='filter_upcoming')
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = Event
        fields = ['title', 'event_type', 'is_published']

    def filter_upcoming(self, queryset, name, value):
        if value:
            return queryset.filter(start_date__gte=timezone.now())
        return queryset

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(summary__icontains=value) |
            models.Q(content__icontains=value)
        )


class CallFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    call_type = django_filters.ChoiceFilter(choices=Call.CallType.choices)
    is_published = django_filters.BooleanFilter()
    deadline_after = django_filters.DateFilter(field_name='deadline', lookup_expr='gte')
    deadline_before = django_filters.DateFilter(field_name='deadline', lookup_expr='lte')
    is_expired = django_filters.BooleanFilter(method='filter_expired')
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = Call
        fields = ['title', 'call_type', 'is_published']

    def filter_expired(self, queryset, name, value):
        if value:
            return queryset.filter(deadline__lt=timezone.now())
        return queryset.filter(deadline__gte=timezone.now())

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(summary__icontains=value) |
            models.Q(content__icontains=value)
        )


class NewsFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    is_published = django_filters.BooleanFilter()
    published_at_after = django_filters.DateFilter(field_name='published_at', lookup_expr='gte')
    published_at_before = django_filters.DateFilter(field_name='published_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = News
        fields = ['title', 'is_published']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(summary__icontains=value) |
            models.Q(content__icontains=value)
        )


class GuideFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = Guide
        fields = ['title', 'is_active']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value)
        )


class BannerFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Banner
        fields = ['title', 'is_active']