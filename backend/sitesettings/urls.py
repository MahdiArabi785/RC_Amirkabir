# sitesettings/urls.py
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import BannerViewSet, SiteSettingsView, SupporterViewSet

app_name = 'sitesettings'   # ← اضافه شد

router = SimpleRouter()
router.register('banners', BannerViewSet, basename='banner')
router.register('supporters', SupporterViewSet, basename='supporter')

urlpatterns = [
    path('settings/', SiteSettingsView.as_view(), name='site-settings'),
    path('', include(router.urls)),
]