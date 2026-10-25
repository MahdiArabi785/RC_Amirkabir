# quizes/serializers.py
"""
سریالایزرهای کاربر و ادمین برای آزمون‌ها.

قواعد امنیتی مهم:
  - is_correct گزینه‌ها هرگز در UserOptionSerializer نمایش داده نمی‌شود.
  - grading_guide و reference_answer هرگز در UserQuestionSerializer نیستند.
  - فایل‌های پاسخ (AnswerAttachment) با URL امن (download_url) نمایش
    داده می‌شوند که در view از نظر مالکیت/ادمین چک می‌شود، نه URL
    مستقیم media.
  - QuizAttempt و Answer ادمین همه‌چیز را می‌بینند.
"""
import os
from decimal import Decimal

from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Answer,
    AnswerAttachment,
    Question,
    QuestionGrading,
    QuestionOption,
    Quiz,
    QuizAssignment,
    QuizAttempt,
)
from .validators import validate_answer_file


# =============================================================================
# Helpers
# =============================================================================
def _abs_url(request, field) -> str | None:
    if not field:
        return None
    try:
        url = field.url
    except (ValueError, OSError):
        return None
    if request:
        return request.build_absolute_uri(url)
    return url


def _reverse_or_none(name, kwargs):
    try:
        return reverse(name, kwargs=kwargs)
    except NoReverseMatch:
        return None


# =============================================================================
# Quiz — کاربر
# =============================================================================
class QuizListSerializer(serializers.ModelSerializer):
    """لیست آزمون‌ها — برای کاربر."""
    course_title = serializers.CharField(
        source='course.title', read_only=True, allow_null=True,
    )
    event_title = serializers.CharField(
        source='event.title', read_only=True, allow_null=True,
    )
    questions_count = serializers.IntegerField(read_only=True)
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'id', 'slug', 'title', 'description',
            'course_title', 'event_title',
            'duration_minutes', 'questions_count',
            'start_at', 'end_at', 'status',
            'total_score', 'user_status',
        ]
        read_only_fields = fields

    def get_user_status(self, obj) -> str:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 'anonymous'
        attempt = (
            obj.attempts
            .filter(user=request.user)
            .order_by('-started_at')
            .first()
        )
        if not attempt:
            return 'not_started'
        return attempt.status


class QuizDetailSerializer(serializers.ModelSerializer):
    """جزئیات آزمون قبل از شروع — بدون سؤالات."""
    course_title = serializers.CharField(
        source='course.title', read_only=True, allow_null=True,
    )
    event_title = serializers.CharField(
        source='event.title', read_only=True, allow_null=True,
    )
    questions_count = serializers.IntegerField(read_only=True)
    can_attempt = serializers.SerializerMethodField()
    active_attempt_uuid = serializers.SerializerMethodField()
    remaining_attempts = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'id', 'slug', 'title', 'description',
            'course_title', 'event_title',
            'duration_minutes', 'questions_count',
            'start_at', 'end_at', 'status',
            'total_score', 'pass_score',
            'max_attempts',
            'allow_back_navigation', 'shuffle_questions',
            'allow_review_after_finish',
            'max_answer_file_size_mb', 'max_files_per_question',
            'can_attempt', 'active_attempt_uuid', 'remaining_attempts',
        ]
        read_only_fields = fields

    def _is_user_assigned(self, quiz, user) -> bool:
        assignments = quiz.assignments.all()
        if not assignments.exists():
            return True   # اگر هیچ assignment ای نیست، عمومی است
        if assignments.filter(assign_all_users=True).exists():
            return True
        return assignments.filter(user=user).exists()

    def get_can_attempt(self, obj) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if obj.status != Quiz.Status.PUBLISHED or not obj.is_active:
            return False
        now = timezone.now()
        if not (obj.start_at <= now <= obj.end_at):
            return False
        if not self._is_user_assigned(obj, request.user):
            return False
        # اگر تلاش فعال دارد، می‌تواند ادامه دهد (حتی اگر به سقف رسیده)
        has_active = obj.attempts.filter(
            user=request.user,
            status=QuizAttempt.Status.IN_PROGRESS,
        ).exists()
        if has_active:
            return True
        count = obj.attempts.filter(user=request.user).count()
        return count < obj.max_attempts

    def get_active_attempt_uuid(self, obj) -> str | None:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        attempt = obj.attempts.filter(
            user=request.user,
            status=QuizAttempt.Status.IN_PROGRESS,
        ).order_by('-started_at').first()
        return str(attempt.uuid) if attempt else None

    def get_remaining_attempts(self, obj) -> int:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        used = obj.attempts.filter(user=request.user).count()
        return max(0, obj.max_attempts - used)


# =============================================================================
# Question / Option — کاربر
# =============================================================================
class UserOptionSerializer(serializers.ModelSerializer):
    """گزینه — بدون is_correct."""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = QuestionOption
        fields = ['id', 'order', 'text', 'image', 'image_url']

    def get_image_url(self, obj) -> str | None:
        return _abs_url(self.context.get('request'), obj.image)


class UserQuestionSerializer(serializers.ModelSerializer):
    """
    سؤال — بدون grading_guide / reference_answer.
    تصویر و سند صورت سؤال با URL مستقیم media (چون بخشی از سؤال است و
    باید برای شرکت‌کننده قابل مشاهده باشد؛ امکان IDOR وجود ندارد چون
    فایل‌ها به quiz خاص تعلق دارند).
    """
    options = UserOptionSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id', 'order', 'question_type',
            'text_content',
            'image', 'image_url',
            'document', 'document_url',
            'score', 'is_required',
            'options',
        ]

    def get_image_url(self, obj) -> str | None:
        return _abs_url(self.context.get('request'), obj.image)

    def get_document_url(self, obj) -> str | None:
        return _abs_url(self.context.get('request'), obj.document)


# =============================================================================
# AnswerAttachment — کاربر و ادمین
# =============================================================================
class AnswerAttachmentUserSerializer(serializers.ModelSerializer):
    """
    فایل پاسخ — URL امن از طریق endpoint دانلود.

    فیلد file به‌صورت write_only در serializer ورودی استفاده می‌شود؛
    در خروجی، فقط download_url برگردانده می‌شود که در view مالکیت/ادمین
    چک می‌شود.
    """
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = AnswerAttachment
        fields = [
            'id', 'file_name', 'file_size', 'download_url', 'uploaded_at',
        ]

    def get_file_name(self, obj) -> str:
        return os.path.basename(obj.file.name) if obj.file else ''

    def get_file_size(self, obj) -> int | None:
        try:
            return obj.file.size if obj.file else 0
        except (FileNotFoundError, OSError):
            return None

    def get_download_url(self, obj) -> str | None:
        request = self.context.get('request')
        if not request or not obj.file:
            return None
        path = _reverse_or_none(
            'quizes:answer-attachment-download', {'attempt_id': obj.answer.attempt.uuid, 'attachment_id': obj.pk},
        )
        if not path:
            return None
        return request.build_absolute_uri(path)


class AnswerAttachmentAdminSerializer(AnswerAttachmentUserSerializer):
    """همان، ولی اگر Phase 5 URLها نبود، URL مستقیم media را هم می‌دهد."""
    direct_url = serializers.SerializerMethodField()

    class Meta(AnswerAttachmentUserSerializer.Meta):
        fields = AnswerAttachmentUserSerializer.Meta.fields + ['direct_url']

    def get_direct_url(self, obj) -> str | None:
        # برای ادمین مجاز است؛ مالکیت در view چک می‌شود
        return _abs_url(self.context.get('request'), obj.file)


# =============================================================================
# Answer — کاربر
# =============================================================================
class UserAnswerSerializer(serializers.ModelSerializer):
    attachments = AnswerAttachmentUserSerializer(many=True, read_only=True)

    class Meta:
        model = Answer
        fields = [
            'id', 'question', 'selected_option',
            'attachments', 'answered_at',
        ]


# =============================================================================
# QuizAttempt — کاربر
# =============================================================================
class AttemptSerializer(serializers.ModelSerializer):
    seconds_remaining = serializers.IntegerField(read_only=True)
    is_time_up = serializers.BooleanField(read_only=True)
    is_editable = serializers.BooleanField(read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            'uuid', 'quiz', 'quiz_title', 'attempt_number',
            'status', 'started_at', 'deadline_at', 'submitted_at',
            'seconds_remaining', 'is_time_up', 'is_editable',
            'total_score',
        ]
        read_only_fields = fields


class AttemptDetailSerializer(AttemptSerializer):
    """
    تلاش + سؤالات + پاسخ‌ها + وضعیت هر سؤال.

    allow_back_navigation و shuffle_questions در quiz سطح تعریف شده‌اند؛
    فرانت با استفاده از همین پاسخ + quiz detail، این دو را در UI اعمال
    می‌کند. خود backend اجازه‌ی ذخیره‌ی پاسخ برای هر سؤالی را می‌دهد.
    """
    questions = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()
    questions_status = serializers.SerializerMethodField()

    class Meta(AttemptSerializer.Meta):
        fields = AttemptSerializer.Meta.fields + [
            'questions', 'answers', 'questions_status',
        ]
        read_only_fields = fields

    def get_questions(self, obj):
        qs = obj.quiz.questions.filter(is_active=True).prefetch_related(
            'options',
        ).order_by('order', 'id')
        return UserQuestionSerializer(
            qs, many=True, context=self.context,
        ).data

    def get_answers(self, obj):
        qs = obj.answers.select_related(
            'selected_option', 'question',
        ).prefetch_related('attachments')
        return UserAnswerSerializer(qs, many=True, context=self.context).data

    def get_questions_status(self, obj):
        # بهینه: یک بار لیست پاسخ‌ها را می‌گیریم
        answers = {
            a.question_id: a
            for a in obj.answers.prefetch_related('attachments')
        }
        result = []
        for q in obj.quiz.questions.filter(is_active=True).only('id', 'order'):
            a = answers.get(q.id)
            answered = False
            if a is not None:
                if a.selected_option_id:
                    answered = True
                else:
                    answered = a.attachments.exists()
            result.append({
                'question_id': q.id,
                'order': q.order,
                'answered': answered,
            })
        return result


# =============================================================================
# Serializer های ورودی (validation)
# =============================================================================
class SaveAnswerInputSerializer(serializers.Serializer):
    """ورودی ذخیره پاسخ. فایل‌ها در view از request.FILES خوانده می‌شوند."""
    question_id = serializers.IntegerField()
    selected_option_id = serializers.IntegerField(
        required=False, allow_null=True, default=None,
    )


class GradingSubmitSerializer(serializers.Serializer):
    """ورودی تصحیح سؤال تشریحی توسط مصحح."""
    score = serializers.DecimalField(max_digits=6, decimal_places=2)
    feedback = serializers.CharField(required=False, allow_blank=True, default='')
    private_note = serializers.CharField(
        required=False, allow_blank=True, default='',
    )


# =============================================================================
# Admin serializers — Quiz
# =============================================================================
class QuizAdminListSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(read_only=True)
    attempts_count = serializers.SerializerMethodField()
    created_by_email = serializers.CharField(
        source='created_by.email', read_only=True, allow_null=True,
    )

    class Meta:
        model = Quiz
        fields = [
            'id', 'slug', 'title', 'status', 'is_active',
            'duration_minutes', 'questions_count', 'attempts_count',
            'start_at', 'end_at', 'total_score',
            'created_by_email', 'created_at', 'updated_at',
        ]

    def get_attempts_count(self, obj) -> int:
        return obj.attempts.count()


class QuizAdminDetailSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(read_only=True)
    created_by_email = serializers.CharField(
        source='created_by.email', read_only=True, allow_null=True,
    )

    class Meta:
        model = Quiz
        fields = '__all__'
        read_only_fields = [
            'id', 'slug', 'total_score',
            'created_by', 'created_at', 'updated_at',
        ]

    def validate(self, attrs):
        start = attrs.get('start_at', getattr(self.instance, 'start_at', None))
        end = attrs.get('end_at', getattr(self.instance, 'end_at', None))
        if start and end and end <= start:
            raise serializers.ValidationError(
                {'end_at': 'زمان پایان باید بعد از زمان شروع باشد.'}
            )
        return attrs


class QuizAssignmentAdminSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(
        source='user.email', read_only=True, allow_null=True,
    )

    class Meta:
        model = QuizAssignment
        fields = ['id', 'quiz', 'user', 'user_email', 'assign_all_users', 'created_at']
        read_only_fields = ['id', 'created_at']


# =============================================================================
# Admin serializers — Question / Option
# =============================================================================
class AdminOptionSerializer(serializers.ModelSerializer):
    """گزینه با is_correct — فقط ادمین."""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = QuestionOption
        fields = ['id', 'order', 'text', 'image', 'image_url', 'is_correct']

    def get_image_url(self, obj) -> str | None:
        return _abs_url(self.context.get('request'), obj.image)


class QuestionAdminSerializer(serializers.ModelSerializer):
    options = AdminOptionSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_url(self, obj) -> str | None:
        return _abs_url(self.context.get('request'), obj.image)

    def get_document_url(self, obj) -> str | None:
        return _abs_url(self.context.get('request'), obj.document)

    def validate(self, attrs):
        qtype = attrs.get(
            'question_type',
            getattr(self.instance, 'question_type', None),
        )
        text = attrs.get('text_content', getattr(self.instance, 'text_content', ''))
        image = attrs.get('image', getattr(self.instance, 'image', None))
        document = attrs.get('document', getattr(self.instance, 'document', None))
        if qtype and not (text or image or document):
            raise serializers.ValidationError(
                'صورت سؤال باید حداقل شامل متن، تصویر یا سند باشد.'
            )
        return attrs


# =============================================================================
# Admin serializers — Attempt / Answer / Grading
# =============================================================================
class AttemptAdminListSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            'uuid', 'quiz', 'quiz_title', 'user', 'user_email',
            'attempt_number', 'status',
            'started_at', 'deadline_at', 'submitted_at', 'graded_at',
            'total_score', 'submitted_by_user',
        ]


class AnswerAdminSerializer(serializers.ModelSerializer):
    attachments = AnswerAttachmentAdminSerializer(many=True, read_only=True)
    question_order = serializers.IntegerField(
        source='question.order', read_only=True,
    )
    question_type = serializers.CharField(
        source='question.question_type', read_only=True,
    )
    question_score = serializers.DecimalField(
        source='question.score',
        max_digits=6, decimal_places=2, read_only=True,
    )
    selected_option_is_correct = serializers.SerializerMethodField()
    grading = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = [
            'id', 'attempt', 'question',
            'question_order', 'question_type', 'question_score',
            'selected_option', 'selected_option_is_correct',
            'attachments', 'answered_at', 'grading',
        ]

    def get_selected_option_is_correct(self, obj) -> bool | None:
        if obj.selected_option_id:
            return obj.selected_option.is_correct
        return None

    def get_grading(self, obj):
        g = getattr(obj, 'grading', None)
        if g is None:
            return None
        return QuestionGradingAdminSerializer(g, context=self.context).data


class QuestionGradingAdminSerializer(serializers.ModelSerializer):
    grader_email = serializers.CharField(
        source='grader.email', read_only=True, allow_null=True,
    )

    class Meta:
        model = QuestionGrading
        fields = [
            'id', 'answer', 'grader', 'grader_email',
            'score', 'feedback', 'private_note',
            'status', 'graded_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'grader', 'status', 'graded_at',
            'created_at', 'updated_at',
        ]

# =============================================================================
# Phase 4 — Result serializers (کاربر نتایج را می‌بیند)
# =============================================================================
class AnswerResultSerializer(serializers.ModelSerializer):
    """
    جزئیات یک پاسخ برای نمایش نتیجه.

    - برای MCQ: is_correct و awarded_score محاسبه‌شده را برمی‌گرداند.
    - برای تشریحی: فقط وقتی grading.status == GRADED، score/feedback
      برمی‌گردد؛ وگرنه فقط {'status': ...}.
    """
    question_order = serializers.IntegerField(
        source='question.order', read_only=True,
    )
    question_type = serializers.CharField(
        source='question.question_type', read_only=True,
    )
    question_text = serializers.CharField(
        source='question.text_content', read_only=True,
    )
    question_score = serializers.DecimalField(
        source='question.score',
        max_digits=6, decimal_places=2, read_only=True,
    )
    selected_option_text = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()
    awarded_score = serializers.SerializerMethodField()
    grading = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = [
            'id', 'question',
            'question_order', 'question_type', 'question_text',
            'question_score',
            'selected_option', 'selected_option_text',
            'is_correct', 'awarded_score',
            'grading', 'answered_at',
        ]

    def get_selected_option_text(self, obj):
        return obj.selected_option.text if obj.selected_option else None

    def get_is_correct(self, obj):
        if (
            obj.question.question_type == 'mcq'
            and obj.selected_option_id
        ):
            return obj.selected_option.is_correct
        return None

    def get_awarded_score(self, obj):
        from .services import _mcq_score_for_answer
        if obj.question.question_type == 'mcq':
            return str(_mcq_score_for_answer(obj))
        try:
            g = obj.grading
        except QuestionGrading.DoesNotExist:
            return None
        if g.status != QuestionGrading.Status.GRADED:
            return None
        return str(g.score) if g.score is not None else None

    def get_grading(self, obj):
        if obj.question.question_type != 'descriptive':
            return None
        try:
            g = obj.grading
        except QuestionGrading.DoesNotExist:
            return None
        if g.status != QuestionGrading.Status.GRADED:
            return {'status': g.status}
        return {
            'status': g.status,
            'score': str(g.score) if g.score is not None else None,
            'feedback': g.feedback,
        }


class AttemptResultSerializer(serializers.ModelSerializer):
    """
    نتیجه نهایی یک تلاش.

    - اگر quiz.allow_review_after_finish=False باشد، فقط تعداد پاسخ‌ها
      برگردانده می‌شود، نه جزئیات.
    - passed فقط وقتی total_score و pass_score هر دو موجود باشند محاسبه
      می‌شود (وگرنه null).
    - result_status: final (GRADED) | pending_grading (SUBMITTED) | ...
    """
    quiz_title = serializers.CharField(
        source='quiz.title', read_only=True,
    )
    quiz_slug = serializers.CharField(
        source='quiz.slug', read_only=True,
    )
    quiz_total_score = serializers.DecimalField(
        source='quiz.total_score',
        max_digits=7, decimal_places=2, read_only=True,
    )
    pass_score = serializers.DecimalField(
        source='quiz.pass_score',
        max_digits=7, decimal_places=2, read_only=True,
    )
    allow_review = serializers.BooleanField(
        source='quiz.allow_review_after_finish', read_only=True,
    )
    passed = serializers.SerializerMethodField()
    result_status = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = [
            'uuid', 'quiz', 'quiz_title', 'quiz_slug',
            'attempt_number', 'status', 'result_status',
            'started_at', 'submitted_at', 'graded_at',
            'total_score', 'quiz_total_score',
            'pass_score', 'passed',
            'allow_review', 'answers',
        ]
        read_only_fields = fields

    def get_passed(self, obj):
        if obj.total_score is None or obj.quiz.pass_score is None:
            return None
        return obj.total_score >= obj.quiz.pass_score

    def get_result_status(self, obj) -> str:
        if obj.status == QuizAttempt.Status.GRADED:
            return 'final'
        if obj.status == QuizAttempt.Status.SUBMITTED:
            return 'pending_grading'
        return obj.status

    def get_answers(self, obj):
        if not obj.quiz.allow_review_after_finish:
            return {
                'available': False,
                'count': obj.answers.count(),
                'hint': 'جزئیات پس از مجاز شدن توسط مدیر قابل مشاهده است.',
            }
        qs = (
            obj.answers
            .select_related('question', 'selected_option')
            .prefetch_related('attachments', 'grading')
            .order_by('question__order', 'question_id')
        )
        return {
            'available': True,
            'items': AnswerResultSerializer(
                qs, many=True, context=self.context,
            ).data,
        }

# =============================================================================
# Phase 5 — Admin input serializers
# =============================================================================
class QuizAssignmentBulkInputSerializer(serializers.Serializer):
    """
    ورودی مدیریت اختصاص‌های آزمون:
      - {assign_all_users: true}  → آزمون برای همه باز
      - {user_ids: [1, 2, 3]}     → فقط این کاربران
    نمی‌توانند همزمان باشند.
    """
    assign_all_users = serializers.BooleanField(default=False)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list,
    )

    def validate(self, attrs):
        if not attrs['assign_all_users'] and not attrs['user_ids']:
            raise serializers.ValidationError(
                'یا assign_all_users=true بفرستید یا حداقل یک user_id.'
            )
        if attrs['assign_all_users'] and attrs['user_ids']:
            raise serializers.ValidationError(
                'assign_all_users و user_ids نمی‌توانند همزمان باشند.'
            )
        return attrs