# quizes/tests.py
"""
تست‌های quizes — پوشش:
  - permissions (admin, anonymous, owner)
  - start_attempt (time windows, assignment, max attempts, idempotent)
  - save_answer (MCQ, descriptive, file validation, deadline)
  - finish_attempt (score, pending grading)
  - grade_answer (bounds, finalize, attempt auto-complete)
  - security (is_correct/grading_guide hidden, IDOR, download)
"""
from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from accounts.models import CustomUser

from .models import (
    Answer,
    Question,
    QuestionGrading,
    QuestionOption,
    Quiz,
    QuizAssignment,
    QuizAttempt,
)
from .services import (
    finish_attempt,
    grade_answer,
    save_answer,
    start_attempt,
)


# =============================================================================
# Helpers
# =============================================================================
def create_admin():
    return CustomUser.objects.create_superuser(
        email='admin@test.com', password='adminpass123',
    )


def create_user(email='u@test.com'):
    u = CustomUser.objects.create_user(email=email, password='userpass123')
    u.is_active = True
    u.save()
    return u


def create_quiz(admin, **overrides):
    now = timezone.now()
    defaults = dict(
        title='آزمون تستی',
        description='توضیح',
        duration_minutes=30,
        start_at=now - timedelta(minutes=5),
        end_at=now + timedelta(hours=2),
        status=Quiz.Status.PUBLISHED,
        is_active=True,
        max_attempts=1,
        max_answer_file_size_mb=5,
        max_files_per_question=3,
        created_by=admin,
    )
    defaults.update(overrides)
    return Quiz.objects.create(**defaults)


def create_mcq(quiz, score='5.00'):
    q = Question.objects.create(
        quiz=quiz, order=1, question_type=Question.QuestionType.MCQ,
        text_content='۲+۲ چند است؟', score=Decimal(score),
    )
    QuestionOption.objects.create(
        question=q, order=1, text='۳', is_correct=False,
    )
    opt_correct = QuestionOption.objects.create(
        question=q, order=2, text='۴', is_correct=True,
    )
    QuestionOption.objects.create(
        question=q, order=3, text='۵', is_correct=False,
    )
    QuestionOption.objects.create(
        question=q, order=4, text='۶', is_correct=False,
    )
    return q, opt_correct


def create_descriptive(quiz, score='5.00'):
    return Question.objects.create(
        quiz=quiz, order=2,
        question_type=Question.QuestionType.DESCRIPTIVE,
        text_content='توضیح دهید.',
        score=Decimal(score),
        grading_guide='راهنمای محرمانه',
        reference_answer='پاسخ محرمانه',
    )


def valid_pdf(name='answer.pdf'):
    return SimpleUploadedFile(
        name, b'%PDF-1.4\n%fake pdf content\n', content_type='application/pdf',
    )


def invalid_pdf(name='answer.pdf'):
    return SimpleUploadedFile(
        name, b'NOT A PDF CONTENT', content_type='application/pdf',
    )


def invalid_ext(name='answer.exe'):
    return SimpleUploadedFile(
        name, b'MZ\x90\x00', content_type='application/octet-stream',
    )


# =============================================================================
# 1. Permissions
# =============================================================================
class QuizPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = create_admin()
        self.user = create_user()

    def test_admin_can_create_quiz(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post('/api/managements/quizes/', {
            'title': 'آزمون جدید',
            'duration_minutes': 20,
            'start_at': (timezone.now() + timedelta(minutes=5)).isoformat(),
            'end_at': (timezone.now() + timedelta(hours=1)).isoformat(),
            'max_attempts': 1,
            'max_answer_file_size_mb': 5,
            'max_files_per_question': 3,
        }, format='json')
        self.assertEqual(r.status_code, 201, r.data)

    def test_non_admin_cannot_create_quiz(self):
        self.client.force_authenticate(self.user)
        r = self.client.post('/api/managements/quizes/', {
            'title': 'x', 'duration_minutes': 10,
            'start_at': timezone.now().isoformat(),
            'end_at': (timezone.now() + timedelta(hours=1)).isoformat(),
        }, format='json')
        self.assertIn(r.status_code, (401, 403))

    def test_anonymous_cannot_list_user_quizzes(self):
        r = self.client.get('/api/quizes/')
        self.assertIn(r.status_code, (401, 403))

    def test_authenticated_user_can_list_quizzes(self):
        create_quiz(self.admin)
        self.client.force_authenticate(self.user)
        r = self.client.get('/api/quizes/')
        self.assertEqual(r.status_code, 200)


# =============================================================================
# 2. Start attempt
# =============================================================================
class StartAttemptTests(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user()

    def test_start_creates_attempt(self):
        quiz = create_quiz(self.admin)
        attempt = start_attempt(quiz, self.user)
        self.assertEqual(attempt.status, QuizAttempt.Status.IN_PROGRESS)
        self.assertEqual(attempt.user, self.user)
        self.assertIsNotNone(attempt.deadline_at)
        self.assertLessEqual(attempt.deadline_at, quiz.end_at)

    def test_start_before_start_at_fails(self):
        quiz = create_quiz(
            self.admin,
            start_at=timezone.now() + timedelta(hours=1),
            end_at=timezone.now() + timedelta(hours=2),
        )
        with self.assertRaises(ValidationError):
            start_attempt(quiz, self.user)

    def test_start_after_end_at_fails(self):
        quiz = create_quiz(
            self.admin,
            start_at=timezone.now() - timedelta(hours=3),
            end_at=timezone.now() - timedelta(minutes=1),
        )
        with self.assertRaises(ValidationError):
            start_attempt(quiz, self.user)

    def test_start_unassigned_user_fails(self):
        quiz = create_quiz(self.admin)
        other = create_user('other@test.com')
        QuizAssignment.objects.create(quiz=quiz, user=other)
        with self.assertRaises(PermissionDenied):
            start_attempt(quiz, self.user)

    def test_start_twice_returns_same_attempt(self):
        quiz = create_quiz(self.admin)
        a1 = start_attempt(quiz, self.user)
        a2 = start_attempt(quiz, self.user)
        self.assertEqual(a1.pk, a2.pk)
        self.assertEqual(
            QuizAttempt.objects.filter(quiz=quiz, user=self.user).count(), 1,
        )

    def test_start_exceeds_max_attempts_fails(self):
        quiz = create_quiz(self.admin, max_attempts=1)
        a1 = start_attempt(quiz, self.user)
        finish_attempt(a1, by_user=True)
        with self.assertRaises(PermissionDenied):
            start_attempt(quiz, self.user)

    def test_start_allowed_if_not_published_fails(self):
        quiz = create_quiz(self.admin, status=Quiz.Status.DRAFT)
        with self.assertRaises(ValidationError):
            start_attempt(quiz, self.user)


# =============================================================================
# 3. Save answer
# =============================================================================
class SaveAnswerTests(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user()
        self.quiz = create_quiz(self.admin)
        self.mcq, self.correct_opt = create_mcq(self.quiz)
        self.desc = create_descriptive(self.quiz)
        self.attempt = start_attempt(self.quiz, self.user)

    def test_save_mcq_answer(self):
        save_answer(
            self.attempt, self.mcq.id,
            selected_option_id=self.correct_opt.id,
        )
        ans = Answer.objects.get(attempt=self.attempt, question=self.mcq)
        self.assertEqual(ans.selected_option_id, self.correct_opt.id)

    def test_save_mcq_with_option_of_other_question_rejected(self):
        # گزینه‌ی سؤال دیگر را به این سؤال بدهیم — باید رد شود
        other_q, _ = create_mcq(self.quiz, score='3.00')
        bad_opt = other_q.options.first()
        with self.assertRaises(ValidationError):
            save_answer(
                self.attempt, self.mcq.id,
                selected_option_id=bad_opt.id,
            )

    def test_save_descriptive_with_valid_file(self):
        save_answer(
            self.attempt, self.desc.id,
            files=[valid_pdf()],
        )
        ans = Answer.objects.get(attempt=self.attempt, question=self.desc)
        self.assertEqual(ans.attachments.count(), 1)

    def test_save_invalid_extension_rejected(self):
        with self.assertRaises(ValidationError):
            save_answer(
                self.attempt, self.desc.id,
                files=[invalid_ext()],
            )

    def test_save_fake_pdf_rejected(self):
        with self.assertRaises(ValidationError):
            save_answer(
                self.attempt, self.desc.id,
                files=[invalid_pdf()],
            )

    def test_save_exceeds_max_files_rejected(self):
        self.quiz.max_files_per_question = 1
        self.quiz.save(update_fields=['max_files_per_question'])
        save_answer(self.attempt, self.desc.id, files=[valid_pdf()])
        with self.assertRaises(ValidationError):
            save_answer(self.attempt, self.desc.id, files=[valid_pdf('b.pdf')])

    def test_save_after_deadline_fails(self):
        past = timezone.now() - timedelta(minutes=10)
        QuizAttempt.objects.filter(pk=self.attempt.pk).update(
            started_at=past - timedelta(minutes=30),
            deadline_at=past,
        )
        self.attempt.refresh_from_db()
        with self.assertRaises(ValidationError):
            save_answer(
                self.attempt, self.mcq.id,
                selected_option_id=self.correct_opt.id,
            )


# =============================================================================
# 4. Finish attempt
# =============================================================================
class FinishAttemptTests(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user()

    def test_finish_all_mcq_graded_immediately(self):
        quiz = create_quiz(self.admin)
        mcq, correct_opt = create_mcq(quiz, score='5.00')
        attempt = start_attempt(quiz, self.user)
        save_answer(attempt, mcq.id, selected_option_id=correct_opt.id)
        attempt = finish_attempt(attempt, by_user=True)
        self.assertEqual(attempt.status, QuizAttempt.Status.GRADED)
        self.assertEqual(attempt.total_score, Decimal('5.00'))

    def test_finish_wrong_mcq_zero_score(self):
        quiz = create_quiz(self.admin)
        mcq, _ = create_mcq(quiz, score='5.00')
        wrong_opt = mcq.options.filter(is_correct=False).first()
        attempt = start_attempt(quiz, self.user)
        save_answer(attempt, mcq.id, selected_option_id=wrong_opt.id)
        attempt = finish_attempt(attempt, by_user=True)
        self.assertEqual(attempt.total_score, Decimal('0.00'))

    def test_finish_with_descriptive_pending_stays_submitted(self):
        quiz = create_quiz(self.admin)
        mcq, correct_opt = create_mcq(quiz, score='5.00')
        desc = create_descriptive(quiz, score='5.00')
        attempt = start_attempt(quiz, self.user)
        save_answer(attempt, mcq.id, selected_option_id=correct_opt.id)
        save_answer(attempt, desc.id, files=[valid_pdf()])
        attempt = finish_attempt(attempt, by_user=True)
        self.assertEqual(attempt.status, QuizAttempt.Status.SUBMITTED)
        self.assertIsNone(attempt.total_score)

    def test_finish_is_idempotent(self):
        quiz = create_quiz(self.admin)
        attempt = start_attempt(quiz, self.user)
        a1 = finish_attempt(attempt, by_user=True)
        a2 = finish_attempt(attempt, by_user=True)
        self.assertEqual(a1.status, a2.status)
        self.assertEqual(a1.submitted_at, a2.submitted_at)


# =============================================================================
# 5. Grading
# =============================================================================
class GradingTests(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user()
        self.quiz = create_quiz(self.admin, max_attempts=1)
        self.mcq, self.correct_opt = create_mcq(self.quiz, score='5.00')
        self.desc = create_descriptive(self.quiz, score='5.00')
        self.attempt = start_attempt(self.quiz, self.user)
        save_answer(
            self.attempt, self.mcq.id,
            selected_option_id=self.correct_opt.id,
        )
        save_answer(self.attempt, self.desc.id, files=[valid_pdf()])
        self.attempt = finish_attempt(self.attempt, by_user=True)
        self.answer = Answer.objects.get(
            attempt=self.attempt, question=self.desc,
        )

    def test_grade_finalize_completes_attempt(self):
        grade_answer(
            self.answer, self.admin,
            score=Decimal('4.50'), feedback='خوب',
            finalize=True,
        )
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, QuizAttempt.Status.GRADED)
        self.assertEqual(self.attempt.total_score, Decimal('9.50'))

    def test_grade_out_of_range_fails(self):
        with self.assertRaises(ValidationError):
            grade_answer(
                self.answer, self.admin,
                score=Decimal('10.00'), finalize=True,
            )

    def test_grade_negative_fails(self):
        with self.assertRaises(ValidationError):
            grade_answer(
                self.answer, self.admin,
                score=Decimal('-1.00'), finalize=True,
            )

    def test_grade_save_temporarily_keeps_attempt_submitted(self):
        grade_answer(
            self.answer, self.admin,
            score=Decimal('4.00'), finalize=False,
        )
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, QuizAttempt.Status.SUBMITTED)


# =============================================================================
# 6. Security
# =============================================================================
class SecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = create_admin()
        self.user1 = create_user('u1@test.com')
        self.user2 = create_user('u2@test.com')
        self.quiz = create_quiz(self.admin)
        self.mcq, _ = create_mcq(self.quiz, score='5.00')
        self.desc = create_descriptive(self.quiz, score='5.00')

    def test_user_does_not_see_is_correct(self):
        self.client.force_authenticate(self.user1)
        r = self.client.post(
            f'/api/quizes/{self.quiz.slug}/start/', format='json',
        )
        self.assertEqual(r.status_code, 200)
        # پاسخ شامل سؤالات و گزینه‌هاست — نباید is_correct داشته باشد
        questions = r.data['questions']
        self.assertTrue(len(questions) > 0)
        for q in questions:
            for opt in q['options']:
                self.assertNotIn('is_correct', opt)

    def test_user_does_not_see_grading_guide(self):
        self.client.force_authenticate(self.user1)
        r = self.client.post(
            f'/api/quizes/{self.quiz.slug}/start/', format='json',
        )
        for q in r.data['questions']:
            self.assertNotIn('grading_guide', q)
            self.assertNotIn('reference_answer', q)

    def test_user_cannot_see_other_users_attempt(self):
        attempt2 = start_attempt(self.quiz, self.user2)
        self.client.force_authenticate(self.user1)
        r = self.client.get(f'/api/quizes/attempt/{attempt2.uuid}/')
        self.assertIn(r.status_code, (403, 404))

    def test_user_cannot_save_answer_to_other_users_attempt(self):
        attempt2 = start_attempt(self.quiz, self.user2)
        self.client.force_authenticate(self.user1)
        r = self.client.post(
            f'/api/quizes/attempt/{attempt2.uuid}/save/',
            {'question_id': self.mcq.id}, format='json',
        )
        self.assertIn(r.status_code, (403, 404))


# =============================================================================
# 7. Attachment download
# =============================================================================
class AttachmentDownloadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = create_admin()
        self.user1 = create_user('u1@test.com')
        self.user2 = create_user('u2@test.com')
        self.quiz = create_quiz(self.admin)
        self.mcq, _ = create_mcq(self.quiz)
        self.desc = create_descriptive(self.quiz)
        self.attempt = start_attempt(self.quiz, self.user1)
        save_answer(self.attempt, self.desc.id, files=[valid_pdf()])
        ans = Answer.objects.get(attempt=self.attempt, question=self.desc)
        self.attachment = ans.attachments.first()

    def test_owner_can_download(self):
        self.client.force_authenticate(self.user1)
        r = self.client.get(
            f'/api/quizes/attempt/{self.attempt.uuid}/attachments/'
            f'{self.attachment.id}/download/'
        )
        self.assertEqual(r.status_code, 200)

    def test_stranger_cannot_download(self):
        self.client.force_authenticate(self.user2)
        r = self.client.get(
            f'/api/quizes/attempt/{self.attempt.uuid}/attachments/'
            f'{self.attachment.id}/download/'
        )
        self.assertIn(r.status_code, (403, 404))

    def test_admin_can_download(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get(
            f'/api/quizes/attempt/{self.attempt.uuid}/attachments/'
            f'{self.attachment.id}/download/'
        )
        self.assertEqual(r.status_code, 200)


# =============================================================================
# 8. Signal behavior
# =============================================================================
class SignalTests(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_recalc_total_score_on_question_create(self):
        quiz = create_quiz(self.admin)
        self.assertEqual(quiz.total_score, Decimal('0.00'))
        create_mcq(quiz, score='5.00')
        quiz.refresh_from_db()
        self.assertEqual(quiz.total_score, Decimal('5.00'))

    def test_only_one_correct_option(self):
        quiz = create_quiz(self.admin)
        q = Question.objects.create(
            quiz=quiz, order=1,
            question_type=Question.QuestionType.MCQ,
            text_content='x', score=Decimal('1.00'),
        )
        a = QuestionOption.objects.create(question=q, text='A', is_correct=True)
        b = QuestionOption.objects.create(question=q, text='B', is_correct=True)
        a.refresh_from_db()
        self.assertFalse(a.is_correct)
        self.assertTrue(b.is_correct)