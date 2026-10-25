# quizes/permissions.py
"""
مجوزهای دسترسی برای آزمون‌ها.

قواعد:
  - IsAdmin / IsAdminOrReadOnly: از core.permissions (تنها منبع حقیقت).
  - IsAttemptOwner: صاحب attempt یا ادمین.
  - CanTakeQuiz: کاربر احراز هویت شده (جزئیات در services.start_attempt).
"""
from rest_framework.permissions import BasePermission

from core.permissions import (  # noqa: F401
    IsAdmin,
    IsAdminOrReadOnly,
    is_admin_user,
)

from .models import QuizAttempt


class IsAttemptOwner(BasePermission):
    """
    فقط صاحب attempt (یا ادمین) به منابع آن دسترسی دارد.

    پشتیبانی از سه نوع آبجکت:
      - QuizAttempt (attempt.user)
      - Answer (answer.attempt.user)
      - AnswerAttachment (attachment.answer.attempt.user)
    """
    message = 'شما به این تلاش دسترسی ندارید.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if is_admin_user(request.user):
            return True

        if isinstance(obj, QuizAttempt):
            return obj.user_id == request.user.id

        # Answer
        attempt = getattr(obj, 'attempt', None)
        if attempt is not None:
            return attempt.user_id == request.user.id

        # AnswerAttachment
        answer = getattr(obj, 'answer', None)
        if answer is not None and answer.attempt_id:
            return answer.attempt.user_id == request.user.id

        return False


class CanTakeQuiz(BasePermission):
    """
    احراز هویت شده؛ منطق دقیق (زمان، assignment، سقف تلاش) در
    services.start_attempt انجام می‌شود.
    """
    message = 'برای شرکت در آزمون باید وارد شوید.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)