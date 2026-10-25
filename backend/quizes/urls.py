# quizes/urls.py
from django.urls import path

from . import views

app_name = 'quizes'

urlpatterns = [
    # لیست و جزئیات
    path('', views.QuizListView.as_view(), name='quiz-list'),
    path('<slug:slug>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    path('<slug:slug>/start/', views.StartAttemptView.as_view(), name='quiz-start'),

    # تلاش فعال
    path(
        'attempt/<uuid:attempt_id>/',
        views.AttemptDetailView.as_view(),
        name='attempt-detail',
    ),
    path(
        'attempt/<uuid:attempt_id>/save/',
        views.SaveAnswerView.as_view(),
        name='attempt-save',
    ),
    path(
        'attempt/<uuid:attempt_id>/finish/',
        views.FinishAttemptView.as_view(),
        name='attempt-finish',
    ),
    path(
        'attempt/<uuid:attempt_id>/result/',
        views.AttemptResultView.as_view(),
        name='attempt-result',
    ),

    # دانلود امن فایل پاسخ
    path(
        'attempt/<uuid:attempt_id>/attachments/<int:attachment_id>/download/',
        views.AnswerAttachmentDownloadView.as_view(),
        name='answer-attachment-download',
    ),
]