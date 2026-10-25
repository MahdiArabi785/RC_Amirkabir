# quizes/models.py
"""
مدل‌های آزمون آنلاین.

اصول طراحی:
- زمان شروع و deadline سمت سرور و غیرقابل‌تغییر بعد از start
- پاسخ صحیح در سریالایزر کاربر حذف می‌شود (نه در مدل)
- یکتایی Answer(attempt, question) از داده‌ی تکراری جلوگیری می‌کند
- یکتایی QuizAttempt(quiz, user, attempt_number) از تلاش تکراری
- فایل‌های آپلودی با validator سخت‌گیرانه (پسوند + حجم)
- is_correct هرگز در __str__ یا لاگ عمومی چاپ نمی‌شود
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q, Sum
from django.utils import timezone
from django.utils.text import slugify


# =============================================================================
# Validators
# =============================================================================
ALLOWED_ANSWER_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']
ALLOWED_QUESTION_DOC_EXTENSIONS = ['pdf', 'docx', 'doc']
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']


def validate_file_size(value, max_mb):
    """بررسی حجم فایل بر اساس مگابایت."""
    if value.size > max_mb * 1024 * 1024:
        raise ValidationError(
            f'حجم فایل نباید بیشتر از {max_mb} مگابایت باشد.'
        )


def answer_upload_path(instance, filename):
    """
    مسیر امن فایل پاسخ: answers/<attempt_uuid>/<answer_uuid>/<sanitized_name>.
    از نام فایل اصلی صرفاً پسوند و نسخه‌ی sanitized استفاده می‌شود تا از
    path traversal و نام‌های مخرب جلوگیری شود.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'bin'
    safe_name = f'{uuid.uuid4().hex}.{ext}'
    return f'answers/{instance.answer.attempt.uuid}/{instance.answer.uuid}/{safe_name}'


def question_asset_path(instance, filename):
    """مسیر امن تصویر/سند صورت سؤال."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'bin'
    safe_name = f'{uuid.uuid4().hex}.{ext}'
    return f'quizzes/questions/{instance.quiz.pk}/{safe_name}'


# =============================================================================
# Quiz
# =============================================================================
class Quiz(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'پیش‌نویس'
        PUBLISHED = 'published', 'منتشر شده'
        ARCHIVED = 'archived', 'آرشیو شده'

    title = models.CharField('عنوان', max_length=255)
    slug = models.SlugField(
        'نامک', max_length=255, unique=True, allow_unicode=True, blank=True,
    )
    description = models.TextField('توضیحات', blank=True)

    course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='quizzes',
        verbose_name='دوره مرتبط',
    )
    event = models.ForeignKey(
        'events.Event', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='quizzes',
        verbose_name='رویداد مرتبط',
    )

    duration_minutes = models.PositiveIntegerField(
        'مدت آزمون (دقیقه)',
        validators=[MinValueValidator(1)],
        help_text='پس از شروع، این زمان قابل تغییر نیست.',
    )
    start_at = models.DateTimeField(
        'زمان شروع پذیرش آزمون',
        help_text='قبل از این زمان، کاربر نمی‌تواند آزمون را شروع کند.',
    )
    end_at = models.DateTimeField(
        'مهلت پایان پذیرش آزمون',
        help_text='پس از این زمان، شروع تلاش جدید ممکن نیست.',
    )

    is_active = models.BooleanField('فعال', default=True, db_index=True)
    status = models.CharField(
        'وضعیت', max_length=20, choices=Status.choices,
        default=Status.DRAFT, db_index=True,
    )

    max_attempts = models.PositiveSmallIntegerField(
        'حداکثر تعداد تلاش', default=1,
        validators=[MinValueValidator(1)],
    )
    allow_back_navigation = models.BooleanField(
        'امکان بازگشت به سؤال قبلی', default=True,
    )
    shuffle_questions = models.BooleanField(
        'ترتیب تصادفی سؤالات', default=False,
    )
    allow_review_after_finish = models.BooleanField(
        'امکان مشاهده پاسخ‌ها پس از اتمام', default=False,
    )

    total_score = models.DecimalField(
        'نمره کل', max_digits=7, decimal_places=2, default=Decimal('0.00'),
        help_text='به‌صورت خودکار از مجموع نمرات سؤالات محاسبه می‌شود.',
    )
    pass_score = models.DecimalField(
        'نمره قبولی', max_digits=7, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    negative_marking = models.BooleanField(
        'اعمال نمره منفی', default=False,
    )

    max_answer_file_size_mb = models.PositiveSmallIntegerField(
        'حداکثر حجم هر فایل پاسخ (MB)', default=5,
    )
    max_files_per_question = models.PositiveSmallIntegerField(
        'حداکثر تعداد فایل برای هر سؤال', default=3,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_quizzes',
        verbose_name='ایجادکننده',
    )
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ بروزرسانی', auto_now=True)

    class Meta:
        verbose_name = 'آزمون'
        verbose_name_plural = 'آزمون‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['start_at', 'end_at']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_at__gt=F('start_at')),
                name='quiz_end_after_start',
            ),
            models.CheckConstraint(
                condition=Q(duration_minutes__gt=0),
                name='quiz_duration_positive',
            ),
            models.CheckConstraint(
                condition=Q(max_attempts__gte=1),
                name='quiz_max_attempts_min_1',
            ),
            models.CheckConstraint(
                condition=Q(max_answer_file_size_mb__gte=1),
                name='quiz_file_size_min_1',
            ),
            models.CheckConstraint(
                condition=Q(max_files_per_question__gte=1),
                name='quiz_max_files_min_1',
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or 'quiz'
            candidate = base
            counter = 1
            while Quiz.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                counter += 1
                candidate = f'{base}-{counter}'
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def is_open_for_registration(self) -> bool:
        """آیا در پنجره‌ی زمانی و منتشرشده و فعال است؟"""
        if self.status != self.Status.PUBLISHED or not self.is_active:
            return False
        now = timezone.now()
        return self.start_at <= now <= self.end_at

    @property
    def questions_count(self) -> int:
        return self.questions.filter(is_active=True).count()

    def recalculate_total_score(self):
        """مجموع نمرات سؤالات فعال را در total_score می‌نویسد."""
        total = self.questions.filter(is_active=True).aggregate(
            s=Sum('score'),
        )['s'] or Decimal('0.00')
        self.total_score = total
        self.save(update_fields=['total_score'])


# =============================================================================
# QuizAssignment — مجوز شرکت
# =============================================================================
class QuizAssignment(models.Model):
    """
    هر آزمون می‌تواند برای:
      - همه‌ی کاربران (user=None, assign_all_users=True) — عمومی
      - کاربران مشخص (user=...)
    در صورت وجود حداقل یک ردیف با assign_all_users=True، آزمون برای همه باز
    است. در غیر این صورت فقط کاربران در جدول مجازند.
    """
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='assignments',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='quiz_assignments',
    )
    assign_all_users = models.BooleanField(
        'اختصاص به همه کاربران', default=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'اختصاص آزمون'
        verbose_name_plural = 'اختصاص‌های آزمون'
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(assign_all_users=True, user__isnull=True) |
                    Q(assign_all_users=False, user__isnull=False)
                ),
                name='quiz_assignment_valid_target',
            ),
            models.UniqueConstraint(
                fields=['quiz', 'user'],
                condition=Q(user__isnull=False),
                name='quiz_assignment_unique_user',
            ),
        ]

    def __str__(self):
        if self.assign_all_users:
            return f'{self.quiz} → همه'
        return f'{self.quiz} → {self.user}'


# =============================================================================
# Question
# =============================================================================
class Question(models.Model):
    class QuestionType(models.TextChoices):
        MCQ = 'mcq', 'چهارگزینه‌ای'
        DESCRIPTIVE = 'descriptive', 'تشریحی'

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions',
    )
    order = models.PositiveIntegerField('ترتیب', default=0)
    question_type = models.CharField(
        'نوع سؤال', max_length=20, choices=QuestionType.choices,
        db_index=True,
    )

    text_content = models.TextField(
        'صورت سؤال (متن)', blank=True,
        help_text='می‌تواند با فایل تصویر یا PDF ترکیب شود.',
    )
    image = models.ImageField(
        'تصویر صورت سؤال',
        upload_to=question_asset_path,
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
        ],
    )
    document = models.FileField(
        'فایل PDF یا Word صورت سؤال',
        upload_to=question_asset_path,
        blank=True, null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_QUESTION_DOC_EXTENSIONS,
            ),
        ],
    )

    score = models.DecimalField(
        'نمره سؤال', max_digits=6, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    is_required = models.BooleanField('اجباری', default=True)
    is_active = models.BooleanField('فعال', default=True, db_index=True)

    grading_guide = models.TextField(
        'راهنمای تصحیح (خصوصی)', blank=True,
        help_text='فقط برای مصحح نمایش داده می‌شود.',
    )
    reference_answer = models.TextField(
        'پاسخ معیار (خصوصی)', blank=True,
        help_text='پس از تصحیح و در صورت مجاز بودن، می‌تواند منتشر شود.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سؤال'
        verbose_name_plural = 'سؤالات'
        ordering = ['order', 'id']
        constraints = [
            models.CheckConstraint(
                condition=Q(score__gt=0),
                name='question_score_positive',
            ),
        ]
        indexes = [
            models.Index(fields=['quiz', 'is_active', 'order']),
        ]

    def __str__(self):
        return f'Q{self.order} — {self.get_question_type_display()}'

    def clean(self):
        super().clean()
        if self.question_type == self.QuestionType.MCQ:
            if self.pk and self.options.count() < 2:
                raise ValidationError(
                    'سؤال چهارگزینه‌ای باید حداقل دو گزینه داشته باشد.'
                )
        elif self.question_type == self.QuestionType.DESCRIPTIVE:
            if self.pk and self.options.exists():
                raise ValidationError(
                    'سؤال تشریحی نباید گزینه داشته باشد.'
                )


# =============================================================================
# QuestionOption
# =============================================================================
class QuestionOption(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='options',
    )
    order = models.PositiveSmallIntegerField('ترتیب', default=0)
    text = models.CharField('متن گزینه', max_length=500, blank=True)
    image = models.ImageField(
        'تصویر گزینه',
        upload_to=question_asset_path,
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
        ],
    )
    # هشدار: هرگز در serializer کاربر نمایش داده نمی‌شود.
    is_correct = models.BooleanField('پاسخ صحیح', default=False)

    class Meta:
        verbose_name = 'گزینه'
        verbose_name_plural = 'گزینه‌ها'
        ordering = ['order', 'id']
        constraints = [
            models.CheckConstraint(
                condition=Q(text__gt='') | Q(image__isnull=False),
                name='question_option_has_content',
            ),
        ]

    def __str__(self):
        return self.text[:50] or f'گزینه #{self.pk}'

    def clean(self):
        super().clean()
        if self.question_id and self.question.question_type != Question.QuestionType.MCQ:
            raise ValidationError('فقط سؤال چهارگزینه‌ای می‌تواند گزینه داشته باشد.')


# =============================================================================
# QuizAttempt
# =============================================================================
class QuizAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'در حال انجام'
        SUBMITTED = 'submitted', 'ارسال شده'
        GRADED = 'graded', 'تصحیح شده'
        EXPIRED = 'expired', 'منقضی شده'
        CANCELLED = 'cancelled', 'لغو شده'

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='attempts',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    attempt_number = models.PositiveSmallIntegerField('شماره تلاش', default=1)

    status = models.CharField(
        'وضعیت', max_length=20, choices=Status.choices,
        default=Status.IN_PROGRESS, db_index=True,
    )

    started_at = models.DateTimeField('زمان شروع', auto_now_add=True)
    deadline_at = models.DateTimeField(
        'مهلت پایان تلاش',
        help_text='معادل min(started_at + duration, quiz.end_at).',
    )
    submitted_at = models.DateTimeField('زمان ارسال', null=True, blank=True)
    graded_at = models.DateTimeField('زمان تصحیح', null=True, blank=True)

    total_score = models.DecimalField(
        'نمره کسب‌شده', max_digits=7, decimal_places=2,
        null=True, blank=True,
    )

    submitted_by_user = models.BooleanField(
        'ارسال توسط کاربر', default=False,
        help_text='False یعنی سیستم به‌خاطر پایان زمان بسته است.',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'تلاش آزمون'
        verbose_name_plural = 'تلاش‌های آزمون'
        ordering = ['-started_at']
        constraints = [
            models.UniqueConstraint(
                fields=['quiz', 'user', 'attempt_number'],
                name='quizattempt_unique_number',
            ),
            models.CheckConstraint(
                condition=Q(deadline_at__gte=F('started_at')),
                name='quizattempt_deadline_after_start',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['quiz', 'status']),
            models.Index(fields=['deadline_at']),
        ]

    def __str__(self):
        return f'{self.user} → {self.quiz} #{self.attempt_number}'

    @property
    def is_time_up(self) -> bool:
        return timezone.now() >= self.deadline_at

    @property
    def is_editable(self) -> bool:
        return self.status == self.Status.IN_PROGRESS and not self.is_time_up

    @property
    def seconds_remaining(self) -> int:
        if self.status != self.Status.IN_PROGRESS:
            return 0
        remaining = (self.deadline_at - timezone.now()).total_seconds()
        return max(0, int(remaining))

    def finish(self, by_user: bool = True):
        """
        بستن تلاش. در پایان زمان یا ثبت نهایی کاربر.
        باید در یک transaction با select_for_update صدا زده شود.
        """
        self.status = self.Status.SUBMITTED
        self.submitted_at = timezone.now()
        self.submitted_by_user = by_user
        self.save(update_fields=[
            'status', 'submitted_at', 'submitted_by_user',
        ])


# =============================================================================
# Answer
# =============================================================================
class Answer(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True,
    )
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name='answers',
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answers',
    )

    selected_option = models.ForeignKey(
        QuestionOption, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='answers',
    )

    answered_at = models.DateTimeField('زمان پاسخ', auto_now=True)

    class Meta:
        verbose_name = 'پاسخ'
        verbose_name_plural = 'پاسخ‌ها'
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'question'],
                name='answer_unique_per_question',
            ),
        ]
        indexes = [
            models.Index(fields=['attempt', 'question']),
        ]

    def __str__(self):
        return f'Answer #{self.pk} (attempt={self.attempt_id})'

    def clean(self):
        super().clean()
        if not self.question_id or not self.attempt_id:
            return
        if self.attempt.quiz_id != self.question.quiz_id:
            raise ValidationError('سؤال به آزمون این تلاش تعلق ندارد.')
        if self.selected_option_id:
            if self.selected_option.question_id != self.question_id:
                raise ValidationError('گزینه به این سؤال تعلق ندارد.')


# =============================================================================
# AnswerAttachment (فقط تشریحی)
# =============================================================================
class AnswerAttachment(models.Model):
    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, related_name='attachments',
    )
    file = models.FileField(
        'فایل پاسخ',
        upload_to=answer_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_ANSWER_EXTENSIONS),
        ],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'فایل پاسخ'
        verbose_name_plural = 'فایل‌های پاسخ'
        ordering = ['uploaded_at']

    def __str__(self):
        return f'Attachment #{self.pk}'


# =============================================================================
# QuestionGrading — تصحیح سؤالات تشریحی
# =============================================================================
class QuestionGrading(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار تصحیح'
        IN_PROGRESS = 'in_progress', 'در حال تصحیح'
        GRADED = 'graded', 'تصحیح شده'

    answer = models.OneToOneField(
        Answer, on_delete=models.CASCADE, related_name='grading',
    )
    grader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='graded_answers',
    )
    score = models.DecimalField(
        'نمره', max_digits=6, decimal_places=2,
        null=True, blank=True,
    )
    feedback = models.TextField(
        'بازخورد برای کاربر', blank=True,
    )
    private_note = models.TextField(
        'یادداشت خصوصی', blank=True,
    )
    status = models.CharField(
        'وضعیت', max_length=20, choices=Status.choices,
        default=Status.PENDING, db_index=True,
    )
    graded_at = models.DateTimeField('زمان تصحیح', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تصحیح'
        verbose_name_plural = 'تصحیح‌ها'

    def __str__(self):
        return f'Grading #{self.pk} — {self.get_status_display()}'

    def clean(self):
        super().clean()
        if self.score is not None and self.answer_id:
            q = self.answer.question
            if self.score < 0:
                raise ValidationError({'score': 'نمره نمی‌تواند منفی باشد.'})
            if self.score > q.score:
                raise ValidationError({
                    'score': f'نمره نمی‌تواند بیشتر از {q.score} باشد.',
                })