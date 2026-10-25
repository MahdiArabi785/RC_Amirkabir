# quizes/urls.py
from django.urls import path

from . import views

app_name = 'quizes'

urlpatterns = [
    # Ù„ÛŒØ³Øª Ùˆ Ø¬Ø²Ø¦ÛŒØ§Øª
    path('', views.QuizListView.as_view(), name='quiz-list'),
    path('<str:slug>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    path('<str:slug>/start/', views.StartAttemptView.as_view(), name='quiz-start'),

    # ØªÙ„Ø§Ø´ ÙØ¹Ø§Ù„
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

    # Ø¯Ø§Ù†Ù„ÙˆØ¯ Ø§Ù…Ù† ÙØ§ÛŒÙ„ Ù¾Ø§Ø³Ø®
    path(
        'attempt/<uuid:attempt_id>/attachments/<int:attachment_id>/download/',
        views.AnswerAttachmentDownloadView.as_view(),
        name='answer-attachment-download',
    ),
]
