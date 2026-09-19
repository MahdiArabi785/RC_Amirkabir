# guides/views.py
from django.http import FileResponse, Http404
from rest_framework import viewsets
from rest_framework.decorators import action

from .models import Guide
from .permissions import IsAdminOrReadOnly
from .serializers import GuideSerializer


def _can_see_inactive(user):
    return bool(user and user.is_authenticated and getattr(user, 'is_admin', user.is_staff))


class GuideViewSet(viewsets.ModelViewSet):
    queryset = Guide.objects.filter(is_active=True)
    serializer_class = GuideSerializer
    permission_classes = [IsAdminOrReadOnly]
    def get_queryset(self):
        if _can_see_inactive(self.request.user):
            return Guide.objects.all()
        return Guide.objects.filter(is_active=True)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        guide = self.get_object()

        if not guide.file:
            raise Http404("فایلی برای این راهنما ثبت نشده است.")

        try:
            file_handle = guide.file.open('rb')
        except (FileNotFoundError, OSError):
            raise Http404("فایل مورد نظر یافت نشد.")

        guide.increase_download()
        return FileResponse(file_handle, as_attachment=True, filename=guide.filename())