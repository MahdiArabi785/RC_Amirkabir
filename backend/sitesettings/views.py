# sitesettings/views.py
from rest_framework import generics, viewsets

from .models import Banner, SiteSettings, Supporter
from .permissions import IsAdminOrReadOnly
from .serializers import BannerSerializer, SiteSettingsSerializer, SupporterSerializer


def _can_see_inactive(user):
    return bool(user and user.is_authenticated and getattr(user, 'is_admin', user.is_staff))


class SiteSettingsView(generics.RetrieveUpdateAPIView):
    """تک شیء - همیشه همان رکورد singleton را برمی‌گرداند/ویرایش می‌کند،
    بدون نیاز به id در URL (GET/PATCH /api/site/settings/)."""
    serializer_class = SiteSettingsSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self):
        return SiteSettings.load()


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