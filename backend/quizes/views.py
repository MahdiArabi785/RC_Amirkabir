# quizes/views.py
"""
Viewهای کاربر برای آزمون‌ها.

همه endpoints به احراز هویت نیاز دارند. IsAttemptOwner برای Attempt/
Answer/Attachment مالکیت را چک می‌کند (ادمین همیشه مجاز است).

نکات امنیتی:
  - QuizListView فقط آزمون‌های assignable به کاربر را برمی‌گرداند
  - QuizDetailView آزمون unpublished را فقط اگر کاربر attempt داشته باشد
    نشان می‌دهد (جلوگیری از IDOR)
  - AttemptDetailView در صورت اتمام زمان، attempt را auto-close می‌کند
  - SaveAnswerView ابتدا زمان را چک می‌کند؛ سپس service.validate
  - Attachment download فقط برای مالک یا ادمین
"""
import logging
import os

from django.db.models import Exists, OuterRef, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AnswerAttachment,
    QuestionGrading,
    Quiz,
    QuizAssignment,
    QuizAttempt,
)
from .permissions import CanTakeQuiz, IsAttemptOwner
from .serializers import (
    AttemptDetailSerializer,
    AttemptResultSerializer,
    AttemptSerializer,
    QuizDetailSerializer,
    QuizListSerializer,
    SaveAnswerInputSerializer,
)
from .services import finish_attempt, save_answer, start_attempt

logger = logging.getLogger(__name__)


# =============================================================================
# Helpers
# =============================================================================
def _filter_assignable(queryset, user):
    """
    آزمون‌هایی که کاربر مجاز است ببیند:
      - هیچ assignment ندارد → عمومی
      - حداقل یک assign_all_users=True → عمومی
      - یا کاربر در جدول assignment است
    """
    has_assignments = QuizAssignment.objects.filter(quiz=OuterRef('pk'))
    has_all_users = QuizAssignment.objects.filter(
        quiz=OuterRef('pk'), assign_all_users=True,
    )
    assigned_to_user = QuizAssignment.objects.filter(
        quiz=OuterRef('pk'), user=user,
    )
    return queryset.annotate(
        _has_assignments=Exists(has_assignments),
        _has_all_users=Exists(has_all_users),
        _assigned=Exists(assigned_to_user),
    ).filter(
        Q(_has_assignments=False) |
        Q(_has_all_users=True) |
        Q(_assigned=True)
    )


# =============================================================================
# List / Detail
# =============================================================================
class QuizListView(generics.ListAPIView):
    """GET /api/quizes/ — لیست آزمون‌های مجاز کاربر."""
    serializer_class = QuizListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Quiz.objects.filter(
            status=Quiz.Status.PUBLISHED,
            is_active=True,
        ).select_related('course', 'event').prefetch_related('questions')
        qs = _filter_assignable(qs, self.request.user)
        return qs.order_by('-start_at', '-id')


class QuizDetailView(generics.RetrieveAPIView):
    """GET /api/quizes/<slug>/ — جزئیات آزمون قبل از شروع."""
    serializer_class = QuizDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user
        qs = Quiz.objects.select_related('course', 'event').prefetch_related(
            'questions', 'assignments',
        )
        # Published/active OR کاربر قبلاً تلاش داشته (تا نتیجه‌اش را ببیند)
        return qs.filter(
            Q(status=Quiz.Status.PUBLISHED, is_active=True) |
            Q(attempts__user=user)
        ).distinct()


# =============================================================================
# Start
# =============================================================================
class StartAttemptView(APIView):
    """
    POST /api/quizes/<slug>/start/
    تلاش جدید می‌سازد یا تلاش in_progress موجود را برمی‌گرداند.
    """
    permission_classes = [CanTakeQuiz]

    def post(self, request, slug):
        quiz = get_object_or_404(Quiz, slug=slug)
        attempt = start_attempt(quiz, request.user, request=request)
        serializer = AttemptDetailSerializer(
            attempt, context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


# =============================================================================
# Active attempt
# =============================================================================
class AttemptDetailView(generics.RetrieveAPIView):
    """
    GET /api/quizes/attempt/<uuid:attempt_id>/
    فقط برای attempt در حال انجام (in_progress).
    اگر زمان تمام شده، attempt auto-close می‌شود و 400 با پیام مناسب.
    """
    serializer_class = AttemptDetailSerializer
    permission_classes = [IsAttemptOwner]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'attempt_id'
    queryset = QuizAttempt.objects.select_related('quiz', 'user')

    def get_object(self):
        obj = super().get_object()
        if (
            obj.status == QuizAttempt.Status.IN_PROGRESS
            and obj.is_time_up
        ):
            obj = finish_attempt(obj, by_user=False)
            raise ValidationError({
                'detail': 'زمان آزمون به پایان رسیده است. '
                          'برای دیدن نتیجه به endpoint result بروید.',
                'status': obj.status,
                'code': 'time_up',
            })
        if obj.status != QuizAttempt.Status.IN_PROGRESS:
            raise ValidationError({
                'detail': 'این تلاش بسته شده است. '
                          'برای دیدن نتیجه به endpoint result بروید.',
                'status': obj.status,
                'code': 'attempt_closed',
            })
        return obj


class SaveAnswerView(APIView):
    """
    POST /api/quizes/attempt/<uuid:attempt_id>/save/
    body (JSON) یا (multipart):
      - question_id (int, required)
      - selected_option_id (int, optional) — برای MCQ
      - files (file, multiple, optional) — برای تشریحی
      - replace_attachments (bool, optional) — حذف فایل‌های قبلی
    """
    permission_classes = [IsAttemptOwner]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(QuizAttempt, uuid=attempt_id)
        self.check_object_permissions(request, attempt)

        # auto-close در صورت اتمام زمان
        if (
            attempt.status == QuizAttempt.Status.IN_PROGRESS
            and attempt.is_time_up
        ):
            finish_attempt(attempt, by_user=False)
            attempt.refresh_from_db()

        if attempt.status != QuizAttempt.Status.IN_PROGRESS:
            return Response(
                {
                    'detail': 'این تلاش بسته شده است.',
                    'status': attempt.status,
                    'code': 'attempt_closed',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SaveAnswerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        files = request.FILES.getlist('files') if request.FILES else None
        replace_flag = str(
            request.data.get('replace_attachments', '')
        ).lower() in ('true', '1', 'yes')

        save_answer(
            attempt,
            question_id=serializer.validated_data['question_id'],
            selected_option_id=serializer.validated_data.get('selected_option_id'),
            files=files if files else None,
            replace_attachments=replace_flag,
        )

        attempt.refresh_from_db()
        return Response(
            AttemptDetailSerializer(
                attempt, context={'request': request},
            ).data,
        )


class FinishAttemptView(APIView):
    """
    POST /api/quizes/attempt/<uuid:attempt_id>/finish/
    idempotent — اگر قبلاً بسته شده، همان نتیجه برمی‌گردد.
    """
    permission_classes = [IsAttemptOwner]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(QuizAttempt, uuid=attempt_id)
        self.check_object_permissions(request, attempt)

        attempt = finish_attempt(attempt, by_user=True)
        return Response(
            AttemptSerializer(attempt, context={'request': request}).data,
        )


class AttemptResultView(generics.RetrieveAPIView):
    """
    GET /api/quizes/attempt/<uuid:attempt_id>/result/
    نتیجه نهایی. اگر attempt هنوز in_progress باشد، 400.
    """
    serializer_class = AttemptResultSerializer
    permission_classes = [IsAttemptOwner]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'attempt_id'
    queryset = QuizAttempt.objects.select_related('quiz', 'user')

    def get_object(self):
        obj = super().get_object()
        if obj.status == QuizAttempt.Status.IN_PROGRESS:
            # اگر زمان تمام شده، ببندش تا نتیجه قابل مشاهده شود
            if obj.is_time_up:
                obj = finish_attempt(obj, by_user=False)
            else:
                raise ValidationError({
                    'detail': 'این تلاش هنوز بسته نشده است.',
                    'code': 'attempt_in_progress',
                })
        return obj


# =============================================================================
# Secure attachment download
# =============================================================================
class AnswerAttachmentDownloadView(APIView):
    """
    GET /api/quizes/attempt/<uuid:attempt_id>/attachments/<int:attachment_id>/download/

    فقط مالک answer یا ادمین. فایل با FileResponse استریم می‌شود تا:
      - فایل main در media مستقیماً از URL باز نشود
      - Content-Disposition: attachment امن باشد
    """
    permission_classes = [IsAttemptOwner]

    def get(self, request, attempt_id, attachment_id):
        attachment = get_object_or_404(
            AnswerAttachment.objects.select_related(
                'answer__attempt__user',
            ),
            id=attachment_id,
            answer__attempt__uuid=attempt_id,
        )
        self.check_object_permissions(request, attachment)

        if not attachment.file:
            raise Http404('فایل موجود نیست.')

        try:
            fh = attachment.file.open('rb')
        except (FileNotFoundError, OSError):
            raise Http404('فایل روی دیسک پیدا نشد.')

        filename = os.path.basename(attachment.file.name) or 'answer'
        return FileResponse(
            fh,
            as_attachment=True,
            filename=filename,
            content_type='application/octet-stream',
        )