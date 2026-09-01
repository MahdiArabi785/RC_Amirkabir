# courses/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, VideoStreamView

router = DefaultRouter()
router.register('courses', CourseViewSet, basename='course')

urlpatterns = [
    path('', include(router.urls)),
    path('videos/<int:video_id>/stream/', VideoStreamView.as_view(), name='video-stream'),
]