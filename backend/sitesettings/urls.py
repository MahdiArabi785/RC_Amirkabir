# sitesettings/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BannerViewSet, SiteSettingsView, SupporterViewSet

router = DefaultRouter()
router.register('banners', BannerViewSet, basename='banner')
router.register('supporters', SupporterViewSet, basename='supporter')

urlpatterns = [
    path('settings/', SiteSettingsView.as_view(), name='site-settings'),
    path('', include(router.urls)),
]