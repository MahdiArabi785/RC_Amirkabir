# =============================================================================
# managements/urls.py
# =============================================================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'articles', ArticleViewSet, basename='articles')
router.register(r'research-projects', ResearchProjectViewSet, basename='research-projects')
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'events', EventViewSet, basename='events')
router.register(r'calls', CallViewSet, basename='calls')
router.register(r'news', NewsViewSet, basename='news')
router.register(r'guides', GuideViewSet, basename='guides')
router.register(r'banners', BannerViewSet, basename='banners')
router.register(r'activity-logs', ActivityLogViewSet, basename='activity-logs')
router.register(r'management-settings', ManagementSettingViewSet, basename='management-settings')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('site-settings/', SiteSettingsView.as_view(), name='site-settings'),
]