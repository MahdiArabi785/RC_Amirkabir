# quizes/services.py
"""
منطق کسب‌وکار آزمون.

نکات امنیتی مهم:
- همه زمان‌ها از timezone.now() سمت سرور محاسبه می‌شوند (نه از
  تایمر مرورگر).
- select_for_update در start/finish از race condition جلوگیری می‌کند.
- save_answer پس از deadline یا status != in_progress رد می‌شود.
- validate_answer_file پسوند + حجم + magic bytes فایل را چک می‌کند.
- selected_option باید به همان question تعلق داشته باشد (جلوگیری از IDOR).
- answer از طریق (attempt, question) unique به‌روزرسانی می‌شود، نه تکرار.
- نمره‌ی منفی در صورت فعال بودن، -score/(n-1) برای هر پاسخ غلط است و
  نمره‌ی کل هرگز منفی نمی‌شود.
"""
import logging
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import (
    Answer,
    AnswerAttachment,
    Question,
    QuestionGrading,
    QuestionOption,
    Quiz,
    QuizAttempt,
)
from .validators import validate_answer_file

logger = logging.getLogger(__name__)


# =============================================================================
# Helpers
# =============================================================================
def _num_options(question: Question) -> int:
    """تعداد گزینه‌های یک سؤال (حداقل ۱ برای جلوگیری از تقسیم بر صفر)."""
    return max(1, question.options.count())


def _get_grading_or_none(answer: Answer):
    """دستیابی امن به reverse OneToOne — None اگر وجود ندارد."""
    try:
        return answer.grading
    except QuestionGrading.DoesNotExist:
        return None


def _mcq_score_for_answer(answer: Answer) -> Decimal:
    """
    نمره‌ی یک پاسخ MCQ:
      - پاسخ صحیح → score
      - پاسخ غلط + منفی‌گیری → -score/(n-1)
      - پاسخ غلط بدون منفی‌گیری → 0
      - بی‌پاسخ → 0
    """
    question = answer.question
    if answer.selected_option_id is None:
        return Decimal('0.00')
    if answer.selected_option.is_correct:
        return question.score
    if answer.attempt.quiz.negative_marking:
        n = _num_options(question)
        if n > 1:
            return -(question.score / Decimal(n - 1))
    return Decimal('0.00')


def _ensure_attempt_writable(attempt: QuizAttempt) -> None:
    """اگر تلاش قابل ویرایش نیست، ValidationError می‌دهد."""
    if attempt.status != QuizAttempt.Status.IN_PROGRESS:
        raise ValidationError({
            'detail': 'این تلاش دیگر قابل ویرایش نیست.',
        })
    if attempt.is_time_up:
        raise ValidationError({
            'detail': 'زمان آزمون به پایان رسیده است.',
            'code': 'time_up',
        })


def _ensure_user_assigned(quiz: Quiz, user) -> None:
    """
    اگر هیچ assignment ای وجود ندارد → عمومی.
    اگر حداقل یک assign_all_users → همه مجازند.
    وگرنه فقط کاربرانی که در جدول هستند.
    """
    assignments = quiz.assignments.all()
    if not assignments.exists():
        return
    if assignments.filter(assign_all_users=True).exists():
        return
    if not assignments.filter(user=user).exists():
        raise PermissionDenied('شما مجاز به شرکت در این آزمون نیستید.')


# =============================================================================
# Public API — Start
# =============================================================================
@transaction.atomic
def start_attempt(quiz: Quiz, user, request=None) -> QuizAttempt:
    """
    شروع یا ادامه‌ی تلاش.

    - اگر تلاش in_progress موجود باشد، همان را برمی‌گرداند (ادامه).
    - اگر منقضی شده باشد، auto-submit می‌کند و در صورت مجاز بودن تلاش
      جدید می‌سازد.
    - quiz باید published + active و در پنجره‌ی زمانی باشد.
    - کاربر باید مجاز باشد (assignment).
    - سقف max_attempts رعایت می‌شود.
    """
    now = timezone.now()

    # ۱. اعتبارسنجی اولیه
    if quiz.status != Quiz.Status.PUBLISHED or not quiz.is_active:
        raise ValidationError({'detail': 'این آزمون در دسترس نیست.'})
    if now < quiz.start_at:
        raise ValidationError({
            'detail': 'زمان شروع آزمون هنوز فرا نرسیده است.',
        })
    if now > quiz.end_at:
        raise ValidationError({'detail': 'مهلت شرکت در آزمون گذشته است.'})

    _ensure_user_assigned(quiz, user)

    # ۲. تلاش in_progress فعلی را با قفل بگیر
    existing = (
        QuizAttempt.objects
        .select_for_update()
        .filter(
            quiz=quiz,
            user=user,
            status=QuizAttempt.Status.IN_PROGRESS,
        )
        .order_by('-started_at')
        .first()
    )
    if existing is not None:
        if not existing.is_time_up:
            return existing
        # منقضی: ببندش و بعد تلاش جدید بساز
        finish_attempt(existing, by_user=False)
        existing.refresh_from_db()

    # ۳. تلاش‌های منقضی دیگر (مثلاً اگر قبلاً بدون پایان رها شده بودند)
    expired_qs = (
        QuizAttempt.objects
        .select_for_update()
        .filter(
            quiz=quiz,
            user=user,
            status=QuizAttempt.Status.IN_PROGRESS,
            deadline_at__lt=now,
        )
    )
    for att in list(expired_qs):
        finish_attempt(att, by_user=False)

    # ۴. سقف تلاش
    used = QuizAttempt.objects.filter(quiz=quiz, user=user).count()
    if used >= quiz.max_attempts:
        raise PermissionDenied(
            'شما به حداکثر تعداد تلاش مجاز رسیده‌اید.'
        )

    # ۵. deadline = min(now + duration, quiz.end_at)
    deadline = min(
        now + timedelta(minutes=quiz.duration_minutes),
        quiz.end_at,
    )

    # ۶. ساخت تلاش
    ip = None
    ua = ''
    if request is not None:
        try:
            from core.utils import get_client_ip
            ip = get_client_ip(request) or None
        except Exception:
            ip = None
        ua = (request.META.get('HTTP_USER_AGENT') or '')[:500]

    return QuizAttempt.objects.create(
        quiz=quiz,
        user=user,
        attempt_number=used + 1,
        deadline_at=deadline,
        ip_address=ip,
        user_agent=ua,
    )


# =============================================================================
# Public API — Save answer
# =============================================================================
@transaction.atomic
def save_answer(
    attempt: QuizAttempt,
    question_id: int,
    selected_option_id: int | None = None,
    files=None,
    replace_attachments: bool = False,
) -> Answer:
    """
    ذخیره‌ی پاسخ کاربر به یک سؤال.

    - MCQ: selected_option_id باید به همان question تعلق داشته باشد.
    - تشریحی: هر فایل جداگانه validate می‌شود؛ مجموع فایل‌ها از
      max_files_per_question تجاوز نمی‌کند.
    - replace_attachments=True: فایل‌های قبلی حذف، سپس فایل‌های جدید اضافه.
    - بدون فایل/گزینه: رکورد Answer ساخته/بروز می‌شود ولی «پاسخ» حساب نمی‌شود.
    """
    _ensure_attempt_writable(attempt)

    question = Question.objects.filter(
        id=question_id,
        quiz=attempt.quiz,
        is_active=True,
    ).first()
    if question is None:
        raise ValidationError({'detail': 'سؤال یافت نشد.'})

    # ── MCQ ──
    if question.question_type == Question.QuestionType.MCQ:
        if selected_option_id is None:
            raise ValidationError({'detail': 'انتخاب گزینه الزامی است.'})
        option = QuestionOption.objects.filter(
            id=selected_option_id, question=question,
        ).first()
        if option is None:
            raise ValidationError({'detail': 'گزینه نامعتبر است.'})

        answer, _ = Answer.objects.get_or_create(
            attempt=attempt, question=question,
        )
        answer.selected_option = option
        answer.save(update_fields=['selected_option', 'answered_at'])
        # فایل‌های پاسخ قبلی (در صورت وجود) پاک شوند
        answer.attachments.all().delete()
        return answer

    # ── تشریحی ──
    if selected_option_id is not None:
        raise ValidationError({'detail': 'سؤال تشریحی گزینه ندارد.'})

    answer, _ = Answer.objects.get_or_create(
        attempt=attempt, question=question,
    )

    if replace_attachments:
        answer.attachments.all().delete()

    if not files:
        return answer

    new_files = list(files)
    existing_count = answer.attachments.count()
    if existing_count + len(new_files) > attempt.quiz.max_files_per_question:
        raise ValidationError({
            'detail': (
                f'حداکثر {attempt.quiz.max_files_per_question} فایل برای '
                'هر سؤال مجاز است.'
            ),
        })

    max_mb = attempt.quiz.max_answer_file_size_mb
    for f in new_files:
        try:
            validate_answer_file(f, max_mb)
        except DjangoValidationError as exc:
            raise ValidationError({'detail': exc.messages})

    for f in new_files:
        AnswerAttachment.objects.create(answer=answer, file=f)

    return answer

# =============================================================================
# Public API — Finish
# =============================================================================
@transaction.atomic
def finish_attempt(
    attempt: QuizAttempt,
    by_user: bool = True,
) -> QuizAttempt:
    """
    بستن تلاش.

    - idempotent: اگر قبلاً بسته شده، بدون تغییر برمی‌گردد.
    - MCQها تصحیح خودکار می‌شوند.
    - اگر پاسخ تشریحی دارای فایل وجود دارد → SUBMITTED (منتظر تصحیح).
    - وگرنه → GRADED و نمره نهایی نوشته می‌شود.
    - by_user=False یعنی سیستم به‌خاطر پایان زمان بسته است.
    """
    attempt = QuizAttempt.objects.select_for_update().get(pk=attempt.pk)
    if attempt.status != QuizAttempt.Status.IN_PROGRESS:
        return attempt

    if by_user and attempt.is_time_up:
        by_user = False

    mcq_total = Decimal('0.00')
    descriptive_pending = False

    for ans in attempt.answers.select_related(
        'question', 'selected_option', 'attempt__quiz',
    ).prefetch_related('attachments'):
        q = ans.question
        if q.question_type == Question.QuestionType.MCQ:
            mcq_total += _mcq_score_for_answer(ans)
        else:
            if ans.attachments.exists():
                g = _get_grading_or_none(ans)
                if g is None or g.status != QuestionGrading.Status.GRADED:
                    descriptive_pending = True

    now = timezone.now()
    if descriptive_pending:
        attempt.status = QuizAttempt.Status.SUBMITTED
        attempt.total_score = None
        attempt.graded_at = None
    else:
        attempt.status = QuizAttempt.Status.GRADED
        attempt.total_score = max(Decimal('0.00'), mcq_total)
        attempt.graded_at = now

    attempt.submitted_at = now
    attempt.submitted_by_user = by_user
    attempt.save(update_fields=[
        'status', 'submitted_at', 'submitted_by_user',
        'total_score', 'graded_at',
    ])
    return attempt


def auto_submit_expired() -> int:
    """
    تلاش‌های in_progress که deadline آن‌ها گذشته را می‌بندد.
    برمی‌گرداند تعداد تلاش‌های بسته‌شده.

    توصیه: یک cron/task این تابع را هر ۱-۲ دقیقه صدا بزند تا تلاش‌های
    رهاشده سریع بسته شوند. حتی اگر فراموش شود، start_attempt و
    finish_attempt هم به‌طور ضمنی همین کار را انجام می‌دهند.
    """
    now = timezone.now()
    expired_ids = list(
        QuizAttempt.objects
        .filter(
            status=QuizAttempt.Status.IN_PROGRESS,
            deadline_at__lte=now,
        )
        .values_list('pk', flat=True)
    )
    closed = 0
    for pk in expired_ids:
        try:
            with transaction.atomic():
                att = QuizAttempt.objects.select_for_update().get(pk=pk)
                if att.status != QuizAttempt.Status.IN_PROGRESS:
                    continue
                finish_attempt(att, by_user=False)
                closed += 1
        except QuizAttempt.DoesNotExist:
            continue
        except Exception:
            logger.exception('auto_submit failed for attempt pk=%s', pk)
    if closed:
        logger.info('auto_submit_expired: closed %d attempts', closed)
    return closed


# =============================================================================
# Public API — Grading
# =============================================================================
@transaction.atomic
def grade_answer(
    answer: Answer,
    grader,
    score: Decimal,
    feedback: str = '',
    private_note: str = '',
    finalize: bool = False,
) -> QuestionGrading:
    """
    تصحیح یک سؤال تشریحی.

    - score باید در بازه [0, answer.question.score] باشد.
    - finalize=False: ذخیره‌ی موقت (status=IN_PROGRESS).
    - finalize=True: نهایی (status=GRADED, graded_at=now) و در صورت کامل
      بودن همه‌ی تصحیح‌ها، attempt نیز GRADED می‌شود.
    """
    if answer.question.question_type != Question.QuestionType.DESCRIPTIVE:
        raise ValidationError({'detail': 'این سؤال تشریحی نیست.'})

    max_score = answer.question.score
    if score < 0:
        raise ValidationError({'score': 'نمره نمی‌تواند منفی باشد.'})
    if score > max_score:
        raise ValidationError({
            'score': f'نمره نمی‌تواند بیشتر از {max_score} باشد.',
        })

    grading, _ = QuestionGrading.objects.get_or_create(answer=answer)
    grading.grader = grader
    grading.score = score
    grading.feedback = feedback
    grading.private_note = private_note
    if finalize:
        grading.status = QuestionGrading.Status.GRADED
        grading.graded_at = timezone.now()
    elif grading.status == QuestionGrading.Status.PENDING:
        grading.status = QuestionGrading.Status.IN_PROGRESS
    grading.save()

    if finalize:
        _finalize_attempt_if_complete(answer.attempt)

    return grading


@transaction.atomic
def _finalize_attempt_if_complete(attempt: QuizAttempt) -> bool:
    """
    اگر همه‌ی سؤالات تشریحی دارای فایل، grading نهایی دارند، نمره‌ی کل
    را محاسبه و attempt را GRADED می‌کند. True اگر attempt نهایی شد.
    """
    attempt = QuizAttempt.objects.select_for_update().get(pk=attempt.pk)

    if attempt.status != QuizAttempt.Status.SUBMITTED:
        return False

    total = Decimal('0.00')
    for ans in attempt.answers.select_related(
        'question', 'selected_option', 'attempt__quiz',
    ).prefetch_related('attachments'):
        q = ans.question
        if q.question_type == Question.QuestionType.MCQ:
            total += _mcq_score_for_answer(ans)
            continue

        # تشریحی
        if not ans.attachments.exists():
            continue
        g = _get_grading_or_none(ans)
        if g is None or g.status != QuestionGrading.Status.GRADED:
            return False
        total += (g.score or Decimal('0.00'))

    attempt.total_score = max(Decimal('0.00'), total)
    attempt.status = QuizAttempt.Status.GRADED
    attempt.graded_at = timezone.now()
    attempt.save(update_fields=['total_score', 'status', 'graded_at'])
    return True


def attempt_needs_grading(attempt: QuizAttempt) -> bool:
    """آیا این attempt پاسخ تشریحی با فایل دارد که تصحیح نهایی نشده؟"""
    if attempt.status != QuizAttempt.Status.SUBMITTED:
        return False
    for ans in attempt.answers.filter(
        question__question_type=Question.QuestionType.DESCRIPTIVE,
    ).prefetch_related('attachments'):
        if not ans.attachments.exists():
            continue
        g = _get_grading_or_none(ans)
        if g is None or g.status != QuestionGrading.Status.GRADED:
            return True
    return False


# =============================================================================
# Helpers عمومی برای views
# =============================================================================
def get_latest_attempt(quiz: Quiz, user) -> QuizAttempt | None:
    """آخرین تلاش کاربر (هر وضعیتی) برای یک آزمون."""
    return (
        quiz.attempts
        .filter(user=user)
        .order_by('-started_at')
        .first()
    )


def get_active_attempt(quiz: Quiz, user) -> QuizAttempt | None:
    """تلاش فعال (in_progress) کاربر، در صورت وجود."""
    return (
        quiz.attempts
        .filter(
            user=user,
            status=QuizAttempt.Status.IN_PROGRESS,
        )
        .order_by('-started_at')
        .first()
    )