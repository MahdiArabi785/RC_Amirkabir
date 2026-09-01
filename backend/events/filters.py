# events/filters.py
from django.utils import timezone
from django_filters import rest_framework as filters

from .models import Call, Event, News


# -------------------- فیلتر خبر --------------------
class NewsFilter(filters.FilterSet):
    is_published = filters.BooleanFilter()
    from_date = filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    to_date = filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')

    class Meta:
        model = News
        # نکته: from_date/to_date نام فیلد واقعی مدل نیستند (فقط
        # published_at هست)، پس اینجا نیازی به تکرارشان نیست - چون از
        # قبل به‌صورت صریح در بالا declare شده‌اند، django-filter آن‌ها
        # را مستقل از این لیست اعمال می‌کند.
        fields = ['is_published']


# -------------------- فیلتر رویداد --------------------
class EventFilter(filters.FilterSet):
    event_type = filters.CharFilter(field_name='event_type', lookup_expr='exact')
    is_published = filters.BooleanFilter()
    from_date = filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    to_date = filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')
    is_upcoming = filters.BooleanFilter(method='filter_upcoming')

    class Meta:
        model = Event
        fields = ['event_type', 'is_published']

    def filter_upcoming(self, queryset, name, value):
        if value:
            return queryset.filter(start_date__gte=timezone.now())
        return queryset


# -------------------- فیلتر فراخوان --------------------
class CallFilter(filters.FilterSet):
    call_type = filters.CharFilter(field_name='call_type', lookup_expr='exact')
    is_published = filters.BooleanFilter()
    from_date = filters.DateTimeFilter(field_name='deadline', lookup_expr='gte')
    to_date = filters.DateTimeFilter(field_name='deadline', lookup_expr='lte')
    is_expired = filters.BooleanFilter(method='filter_expired')

    class Meta:
        model = Call
        fields = ['call_type', 'is_published']

    def filter_expired(self, queryset, name, value):
        if value:
            return queryset.filter(deadline__lt=timezone.now())
        return queryset.filter(deadline__gte=timezone.now())