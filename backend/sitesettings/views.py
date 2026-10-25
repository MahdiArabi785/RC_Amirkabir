# sitesettings/views.py
from django.http import Http404
from rest_framework import generics, viewsets

from .models import Banner, SiteSettings, Supporter
from .permissions import IsAdminOrReadOnly
from .serializers import BannerSerializer, SiteSettingsSerializer, SupporterSerializer


def _can_see_inactive(user):
    return bool(
        user
        and user.is_authenticated
        and getattr(user, 'is_admin', False)
    )


class SiteSettingsView(generics.RetrieveUpdateAPIView):
    """تک شیء — GET بدون نوشتن DB."""
    serializer_class = SiteSettingsSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self):
        # write: create if missing — read: 404 اگر نبود
        if self.request.method in ('PUT', 'PATCH'):
            return SiteSettings.load()
        try:
            return SiteSettings.objects.get(pk=1)
        except SiteSettings.DoesNotExist:
            raise Http404("تنظیمات سایت هنوز تنظیم نشده است.")


class BannerViewSet(viewsets.ModelViewSet):
    serializer_class = BannerSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if _can_see_inactive(self.request.user):
            return Banner.objects.all()
        return Banner.objects.filter(is_active=True)


class SupporterViewSet(viewsets.ModelViewSet):
    serializer_class = SupporterSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if _can_see_inactive(self.request.user):
            return Supporter.objects.all()
        return Supporter.objects.filter(is_active=True)