# courses/urls.py
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import CourseViewSet, VideoStreamView

router = SimpleRouter()
router.register('', CourseViewSet, basename='course')

urlpatterns = [
    path('stream/<int:video_id>/', VideoStreamView.as_view(), name='video-stream'),
    path('', include(router.urls)),
]