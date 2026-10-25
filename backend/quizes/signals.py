# quizes/signals.py
"""
سیگنال‌های مدل quizes.

- recalc_quiz_total: هر تغییر (ایجاد/حذف) روی Question، total_score آزمون
  را دوباره محاسبه می‌کند.
- ensure_single_correct_option: در pre_save هر QuestionOption با is_correct=True،
  بقیه‌ی گزینه‌های همان سؤال را is_correct=False می‌کند تا فقط یک گزینه‌ی
  صحیح داشته باشیم.
"""
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Question, QuestionOption


@receiver([post_save, post_delete], sender=Question)
def recalc_quiz_total(sender, instance, **kwargs):
    try:
        quiz = instance.quiz
    except Exception:
        return
    try:
        quiz.recalculate_total_score()
    except Exception:
        # quiz ممکن است در حال حذف باشد — خطا نده
        pass


@receiver(pre_save, sender=QuestionOption)
def ensure_single_correct_option(sender, instance, **kwargs):
    if not instance.is_correct or not instance.question_id:
        return
    QuestionOption.objects.filter(
        question_id=instance.question_id,
        is_correct=True,
    ).exclude(pk=instance.pk).update(is_correct=False)