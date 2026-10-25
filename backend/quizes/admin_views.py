# quizes/admin_views.py
"""
Admin viewsets برای quizes — یکپارچه با /api/managements/.

همه actions به IsAdmin نیاز دارند.

URLها (پس از register در managements/urls.py):
  GET    /api/managements/quizes/                       — لیست آزمون‌ها
  POST   /api/managements/quizes/                       — ایجاد آزمون
  GET    /api/managements/quizes/<pk>/                  — جزئیات
  PATCH  /api/managements/quizes/<pk>/                  — ویرایش
  DELETE /api/managements/quizes/<pk>/                  — حذف (بدون attempt)
  POST   /api/managements/quizes/<pk>/publish/          — انتشار
  POST   /api/managements/quizes/<pk>/archive/          — آرشیو
  GET    /api/managements/quizes/<pk>/assignments/      — لیست اختصاص‌ها
  POST   /api/managements/quizes/<pk>/assignments/      — تنظیم اختصاص‌ها
  DELETE /api/managements/quizes/<pk>/assignments/      — حذف همه
  GET    /api/managements/quizes/<pk>/stats/            — آمار یک آزمون

  GET    /api/managements/quiz-questions/?quiz_id=...   — لیست سؤالات
  POST   /api/managements/quiz-questions/               — ایجاد سؤال
  PATCH  /api/managements/quiz-questions/<pk>/          — ویرایش سؤال
  DELETE /api/managements/quiz-questions/<pk>/          — حذف (بدون پاسخ)
  GET    /api/managements/quiz-questions/<pk>/options/  — لیست گزینه‌ها
  POST   /api/managements/quiz-questions/<pk>/options/  — افزودن گزینه
  PATCH  /api/managements/quiz-questions/<pk>/options/<option_id>/ — ویرایش
  DELETE /api/managements/quiz-questions/<pk>/options/<option_id>/ — حذف

  GET    /api/managements/quiz-attempts/?quiz_id=...    — لیست تلاش‌ها
  GET    /api/managements/quiz-attempts/<uuid>/         — جزئیات تلاش
  GET    /api/managements/quiz-attempts/<uuid>/answers/ — پاسخ‌های تلاش
  POST   /api/managements/quiz-attempts/<uuid>/force-close/ — بستن اجباری

  GET    /api/managements/quiz-grading/                 — فهرست نیازمند تصحیح
  GET    /api/managements/quiz-grading/<answer_id>/     — جزئیات پاسخ
  POST   /api/managements/quiz-grading/<answer_id>/grade/ — ثبت نمره

  GET    /api/managements/quiz-stats/                   — آمار کلی آزمون‌ها
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdmin

from .models import (
    Answer,
    Question,
    QuestionGrading,
    QuestionOption,
    Quiz,
    QuizAssignment,
    QuizAttempt,
)
from .serializers import (
    AdminOptionSerializer,
    AnswerAdminSerializer,
    AttemptAdminListSerializer,
    GradingSubmitSerializer,
    QuestionAdminSerializer,
    QuestionGradingAdminSerializer,
    QuizAdminDetailSerializer,
    QuizAdminListSerializer,
    QuizAssignmentAdminSerializer,
    QuizAssignmentBulkInputSerializer,
)
from .services import finish_attempt, grade_answer


# =============================================================================
# Quiz
# =============================================================================
class QuizAdminViewSet(viewsets.ModelViewSet):
    """CRUD کامل آزمون + publish/archive + assignments + stats."""
    queryset = (
        Quiz.objects
        .select_related('course', 'event', 'created_by')
        .prefetch_related('questions')
        .order_by('-created_at')
    )
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return QuizAdminListSerializer
        return QuizAdminDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        اگر آزمون تلاش فعال دارد، تغییر فیلدهای حیاتی (مدت، شروع، پایان،
        سقف تلاش) ممنوع است — چون تلاش‌های فعال را می‌شکند.
        """
        instance = serializer.instance
        has_active = instance.attempts.filter(
            status=QuizAttempt.Status.IN_PROGRESS,
        ).exists()
        if has_active:
            for field in (
                'duration_minutes', 'start_at', 'end_at', 'max_attempts',
            ):
                if field in serializer.validated_data:
                    old = getattr(instance, field)
                    new = serializer.validated_data[field]
                    if old != new:
                        raise ValidationError({
                            field: (
                                'این فیلد با وجود تلاش‌های فعال قابل '
                                'تغییر نیست.'
                            ),
                        })
        serializer.save()

    def perform_destroy(self, instance):
        if instance.attempts.exists():
            raise ValidationError({
                'detail': (
                    'این آزمون دارای تلاش‌های ثبت‌شده است و قابل حذف '
                    'نیست. برای غیرفعال‌سازی از archive استفاده کنید.'
                ),
            })
        instance.delete()

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        quiz = self.get_object()
        if quiz.status == Quiz.Status.PUBLISHED:
            return Response(
                {'detail': 'این آزمون قبلاً منتشر شده است.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not quiz.questions.filter(is_active=True).exists():
            return Response(
                {'detail': 'آزمون بدون سؤال قابل انتشار نیست.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if quiz.end_at <= timezone.now():
            return Response(
                {'detail': 'زمان پایان آزمون گذشته است.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        quiz.status = Quiz.Status.PUBLISHED
        quiz.save(update_fields=['status', 'updated_at'])
        return Response(
            QuizAdminDetailSerializer(quiz, context={'request': request}).data,
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        quiz = self.get_object()
        quiz.status = Quiz.Status.ARCHIVED
        quiz.save(update_fields=['status', 'updated_at'])
        return Response(
            QuizAdminDetailSerializer(quiz, context={'request': request}).data,
        )

    @action(detail=True, methods=['get', 'post', 'delete'], url_path='assignments')
    def assignments(self, request, pk=None):
        quiz = self.get_object()

        if request.method == 'GET':
            qs = quiz.assignments.select_related('user')
            return Response(
                QuizAssignmentAdminSerializer(
                    qs, many=True, context={'request': request},
                ).data,
            )

        if request.method == 'DELETE':
            count, _ = quiz.assignments.all().delete()
            return Response({'detail': f'{count} اختصاص حذف شد.'})

        # POST — جایگزینی کامل
        serializer = QuizAssignmentBulkInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            quiz.assignments.all().delete()
            if data['assign_all_users']:
                QuizAssignment.objects.create(quiz=quiz, assign_all_users=True)
            else:
                from accounts.models import CustomUser
                valid_ids = list(
                    CustomUser.objects.filter(
                        id__in=data['user_ids'],
                    ).values_list('id', flat=True)
                )
                QuizAssignment.objects.bulk_create([
                    QuizAssignment(quiz=quiz, user_id=uid)
                    for uid in valid_ids
                ])

        qs = quiz.assignments.select_related('user')
        return Response(
            QuizAssignmentAdminSerializer(
                qs, many=True, context={'request': request},
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        quiz = self.get_object()
        attempts = quiz.attempts.all()
        graded = attempts.filter(
            status=QuizAttempt.Status.GRADED,
            total_score__isnull=False,
        )
        avg = graded.aggregate(s=Sum('total_score'))['s']
        if avg is not None and graded.count() > 0:
            avg_value = str((avg / graded.count()).quantize(Decimal('0.01')))
        else:
            avg_value = None

        pending_answers = Answer.objects.filter(
            question__quiz=quiz,
            question__question_type=Question.QuestionType.DESCRIPTIVE,
            attempt__status=QuizAttempt.Status.SUBMITTED,
        ).filter(
            Q(grading__isnull=True)
            | ~Q(grading__status=QuestionGrading.Status.GRADED),
        ).count()

        return Response({
            'quiz_id': quiz.id,
            'title': quiz.title,
            'status': quiz.status,
            'questions_count': quiz.questions.filter(is_active=True).count(),
            'attempts': {
                'total': attempts.count(),
                'in_progress': attempts.filter(
                    status=QuizAttempt.Status.IN_PROGRESS,
                ).count(),
                'submitted': attempts.filter(
                    status=QuizAttempt.Status.SUBMITTED,
                ).count(),
                'graded': attempts.filter(
                    status=QuizAttempt.Status.GRADED,
                ).count(),
                'expired': attempts.filter(
                    status=QuizAttempt.Status.EXPIRED,
                ).count(),
            },
            'scores': {
                'average': avg_value,
                'max_total_score': str(quiz.total_score),
                'pass_score': (
                    str(quiz.pass_score) if quiz.pass_score else None
                ),
            },
            'grading': {
                'pending_answers': pending_answers,
            },
        })


# =============================================================================
# Question
# =============================================================================
class QuestionAdminViewSet(viewsets.ModelViewSet):
    queryset = (
        Question.objects
        .select_related('quiz')
        .prefetch_related('options')
        .order_by('quiz_id', 'order', 'id')
    )
    serializer_class = QuestionAdminSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        quiz_id = self.request.query_params.get('quiz_id')
        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.quiz.recalculate_total_score()

    def perform_destroy(self, instance):
        if instance.answers.exists():
            raise ValidationError({
                'detail': 'این سؤال دارای پاسخ است و قابل حذف نیست.',
            })
        quiz = instance.quiz
        instance.delete()
        quiz.recalculate_total_score()

    @action(detail=True, methods=['get', 'post'], url_path='options')
    def options(self, request, pk=None):
        question = self.get_object()
        if question.question_type != Question.QuestionType.MCQ:
            return Response(
                {'detail': 'فقط سؤال چهارگزینه‌ای می‌تواند گزینه داشته باشد.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'GET':
            return Response(
                AdminOptionSerializer(
                    question.options.all(), many=True,
                    context={'request': request},
                ).data,
            )

        serializer = AdminOptionSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(question=question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True, methods=['patch', 'delete'],
        url_path=r'options/(?P<option_id>[0-9]+)',
    )
    def option_detail(self, request, pk=None, option_id=None):
        question = self.get_object()
        option = get_object_or_404(
            QuestionOption, id=option_id, question=question,
        )

        if request.method == 'PATCH':
            serializer = AdminOptionSerializer(
                option, data=request.data, partial=True,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        # DELETE
        if question.answers.exists():
            raise ValidationError({
                'detail': 'این سؤال دارای پاسخ است و گزینه‌هایش قابل حذف نیستند.',
            })
        if question.options.count() <= 2:
            raise ValidationError({
                'detail': 'سؤال باید حداقل ۲ گزینه داشته باشد.',
            })
        option.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Attempt (readonly)
# =============================================================================
class QuizAttemptAdminViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        QuizAttempt.objects
        .select_related('quiz', 'user')
        .order_by('-started_at')
    )
    serializer_class = AttemptAdminListSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'uuid'

    def get_queryset(self):
        qs = super().get_queryset()
        quiz_id = self.request.query_params.get('quiz_id')
        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)
        user_id = self.request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        if self.request.query_params.get('needs_grading') == 'true':
            qs = qs.filter(status=QuizAttempt.Status.SUBMITTED)
        return qs

    @action(detail=True, methods=['get'])
    def answers(self, request, uuid=None):
        attempt = self.get_object()
        qs = (
            attempt.answers
            .select_related(
                'question', 'selected_option',
                'grading', 'grading__grader',
            )
            .prefetch_related('attachments')
            .order_by('question__order', 'question_id')
        )
        return Response(
            AnswerAdminSerializer(
                qs, many=True, context={'request': request},
            ).data,
        )

    @action(detail=True, methods=['post'], url_path='force-close')
    def force_close(self, request, uuid=None):
        attempt = self.get_object()
        if attempt.status != QuizAttempt.Status.IN_PROGRESS:
            return Response(
                {'detail': 'این تلاش بسته شده است.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        attempt = finish_attempt(attempt, by_user=False)
        return Response(
            AttemptAdminListSerializer(
                attempt, context={'request': request},
            ).data,
        )


# =============================================================================
# Grading
# =============================================================================
class GradingAdminViewSet(viewsets.ViewSet):
    """صندوق تصحیح — پاسخ‌های تشریحی نیازمند تصحیح."""
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = (
            Answer.objects
            .filter(
                question__question_type=Question.QuestionType.DESCRIPTIVE,
                attempt__status__in=[
                    QuizAttempt.Status.SUBMITTED,
                    QuizAttempt.Status.GRADED,
                ],
            )
            .select_related(
                'question', 'question__quiz',
                'attempt', 'attempt__user',
                'grading', 'grading__grader',
            )
            .prefetch_related('attachments')
            .order_by('-attempt__submitted_at', 'question__order')
        )
        quiz_id = self.request.query_params.get('quiz_id')
        if quiz_id:
            qs = qs.filter(question__quiz_id=quiz_id)
        if self.request.query_params.get('all') != 'true':
            qs = qs.filter(
                Q(grading__isnull=True)
                | ~Q(grading__status=QuestionGrading.Status.GRADED),
            )
        return qs

    def list(self, request):
        qs = self.get_queryset()
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        data = AnswerAdminSerializer(
            page, many=True, context={'request': request},
        ).data
        return paginator.get_paginated_response(data)

    def retrieve(self, request, pk=None):
        answer = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(
            AnswerAdminSerializer(
                answer, context={'request': request},
            ).data,
        )

    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        answer = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = GradingSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        finalize = bool(request.data.get('finalize', True))
        grading = grade_answer(
            answer,
            grader=request.user,
            score=Decimal(str(data['score'])),
            feedback=data['feedback'],
            private_note=data['private_note'],
            finalize=finalize,
        )
        return Response(
            QuestionGradingAdminSerializer(
                grading, context={'request': request},
            ).data,
        )


# =============================================================================
# Dashboard stats
# =============================================================================
class QuizStatsAPIView(APIView):
    """آمار کلی آزمون‌ها — برای کارت‌های داشبورد ادمین."""
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        attempts = QuizAttempt.objects.all()
        pending = Answer.objects.filter(
            question__question_type=Question.QuestionType.DESCRIPTIVE,
            attempt__status=QuizAttempt.Status.SUBMITTED,
        ).filter(
            Q(grading__isnull=True)
            | ~Q(grading__status=QuestionGrading.Status.GRADED),
        ).count()

        return Response({
            'quizzes': {
                'total': Quiz.objects.count(),
                'published': Quiz.objects.filter(
                    status=Quiz.Status.PUBLISHED,
                ).count(),
                'draft': Quiz.objects.filter(
                    status=Quiz.Status.DRAFT,
                ).count(),
                'archived': Quiz.objects.filter(
                    status=Quiz.Status.ARCHIVED,
                ).count(),
                'active_now': Quiz.objects.filter(
                    status=Quiz.Status.PUBLISHED,
                    is_active=True,
                    start_at__lte=now,
                    end_at__gte=now,
                ).count(),
            },
            'attempts': {
                'total': attempts.count(),
                'in_progress': attempts.filter(
                    status=QuizAttempt.Status.IN_PROGRESS,
                ).count(),
                'submitted': attempts.filter(
                    status=QuizAttempt.Status.SUBMITTED,
                ).count(),
                'graded': attempts.filter(
                    status=QuizAttempt.Status.GRADED,
                ).count(),
                'expired': attempts.filter(
                    status=QuizAttempt.Status.EXPIRED,
                ).count(),
            },
            'grading': {
                'pending_answers': pending,
            },
            'questions': {
                'total': Question.objects.count(),
                'mcq': Question.objects.filter(
                    question_type=Question.QuestionType.MCQ,
                ).count(),
                'descriptive': Question.objects.filter(
                    question_type=Question.QuestionType.DESCRIPTIVE,
                ).count(),
            },
        })