# quizes/admin.py
"""
Django admin registration برای quizes.
"""
from django.contrib import admin

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


# =============================================================================
# Inlines
# =============================================================================
class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0
    fields = ['order', 'text', 'image', 'is_correct']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['order', 'question_type', 'text_content', 'score', 'is_active']
    ordering = ['order']


class QuizAssignmentInline(admin.TabularInline):
    model = QuizAssignment
    extra = 0
    fields = ['user', 'assign_all_users']
    autocomplete_fields = ['user']


class AnswerAttachmentInline(admin.TabularInline):
    model = AnswerAttachment
    extra = 0
    fields = ['file', 'uploaded_at']
    readonly_fields = ['uploaded_at']


# =============================================================================
# Quiz
# =============================================================================
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'status', 'is_active', 'duration_minutes',
        'questions_count', 'total_score', 'start_at', 'end_at',
    ]
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'total_score', 'created_by', 'created_at', 'updated_at',
    ]
    inlines = [QuizAssignmentInline, QuestionInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'title', 'slug', 'description', 'course', 'event',
            ),
        }),
        ('زمان‌بندی', {
            'fields': ('duration_minutes', 'start_at', 'end_at'),
        }),
        ('انتشار', {
            'fields': ('status', 'is_active'),
        }),
        ('سیاست آزمون', {
            'fields': (
                'max_attempts', 'allow_back_navigation',
                'shuffle_questions', 'allow_review_after_finish',
            ),
        }),
        ('نمره', {
            'fields': ('total_score', 'pass_score', 'negative_marking'),
        }),
        ('محدودیت فایل پاسخ', {
            'fields': (
                'max_answer_file_size_mb', 'max_files_per_question',
            ),
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# Question
# =============================================================================
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'quiz', 'order', 'question_type',
        'score', 'is_required', 'is_active',
    ]
    list_filter = ['question_type', 'is_active', 'is_required']
    search_fields = ['text_content', 'quiz__title']
    autocomplete_fields = ['quiz']
    inlines = [QuestionOptionInline]
    ordering = ['quiz', 'order']
    readonly_fields = ['created_at', 'updated_at']


# =============================================================================
# QuestionOption — باید ثبت شود تا autocomplete_fields در AnswerAdmin کار کند
# =============================================================================
@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'order', 'text', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['text']   # ← لازم برای autocomplete
    autocomplete_fields = ['question']
    ordering = ['question', 'order']
    readonly_fields = []


# =============================================================================
# Attempt
# =============================================================================
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'uuid', 'quiz', 'user', 'attempt_number',
        'status', 'started_at', 'deadline_at',
        'submitted_at', 'total_score',
    ]
    list_filter = ['status', 'started_at']
    search_fields = ['user__email', 'quiz__title', 'uuid']
    autocomplete_fields = ['quiz', 'user']
    ordering = ['-started_at']
    date_hierarchy = 'started_at'
    readonly_fields = [
        'uuid', 'started_at', 'deadline_at', 'submitted_at',
        'graded_at', 'total_score', 'submitted_by_user',
        'ip_address', 'user_agent',
    ]


# =============================================================================
# Answer + Attachment
# =============================================================================
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'attempt', 'question', 'selected_option', 'answered_at',
    ]
    list_filter = ['answered_at']
    search_fields = ['attempt__uuid', 'question__text_content']
    # selected_option حالا با ثبت QuestionOptionAdmin قابل autocomplete است
    autocomplete_fields = ['attempt', 'question', 'selected_option']
    inlines = [AnswerAttachmentInline]
    readonly_fields = ['answered_at']


@admin.register(AnswerAttachment)
class AnswerAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'answer', 'uploaded_at']
    list_filter = ['uploaded_at']
    readonly_fields = ['uploaded_at']


# =============================================================================
# Grading
# =============================================================================
@admin.register(QuestionGrading)
class QuestionGradingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'answer', 'grader', 'score', 'status', 'graded_at',
    ]
    list_filter = ['status', 'graded_at']
    search_fields = ['answer__attempt__uuid', 'grader__email']
    autocomplete_fields = ['answer', 'grader']
    readonly_fields = ['created_at', 'updated_at']