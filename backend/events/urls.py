# events/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CallViewSet, EventViewSet, NewsViewSet

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'events', EventViewSet, basename='event')
router.register(r'calls', CallViewSet, basename='call')

urlpatterns = [
    path('', include(router.urls)),
]