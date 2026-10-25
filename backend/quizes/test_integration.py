# quizes/test_integration.py
"""
تست یکپارچه end-to-end برای همه فازهای quizes.
"""
from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from accounts.models import CustomUser

from .models import (
    Answer, Question, QuestionGrading, QuestionOption,
    Quiz, QuizAssignment, QuizAttempt,
)
from .services import (
    auto_submit_expired, finish_attempt, grade_answer,
    save_answer, start_attempt,
)


def create_admin():
    return CustomUser.objects.create_superuser(
        email='admin@test.com', password='adminpass123',
    )


def create_user(email='student@test.com'):
    u = CustomUser.objects.create_user(email=email, password='userpass123')
    u.is_active = True
    u.save()
    return u


def make_quiz(admin, **overrides):
    now = timezone.now()
    defaults = dict(
        title='آزمون یکپارچه',
        duration_minutes=30,
        start_at=now - timedelta(minutes=5),
        end_at=now + timedelta(hours=2),
        status=Quiz.Status.PUBLISHED,
        is_active=True,
        max_attempts=1,
        max_answer_file_size_mb=5,
        max_files_per_question=3,
        allow_review_after_finish=True,
        created_by=admin,
    )
    defaults.update(overrides)
    return Quiz.objects.create(**defaults)


def make_mcq(quiz, score='5.00'):
    q = Question.objects.create(
        quiz=quiz, order=1, question_type=Question.QuestionType.MCQ,
        text_content='۲+۲ چند است؟', score=Decimal(score),
    )
    QuestionOption.objects.create(question=q, order=1, text='۳', is_correct=False)
    correct = QuestionOption.objects.create(
        question=q, order=2, text='۴', is_correct=True,
    )
    QuestionOption.objects.create(question=q, order=3, text='۵', is_correct=False)
    QuestionOption.objects.create(question=q, order=4, text='۶', is_correct=False)
    return q, correct


def make_desc(quiz, score='5.00'):
    return Question.objects.create(
        quiz=quiz, order=2,
        question_type=Question.QuestionType.DESCRIPTIVE,
        text_content='توضیح دهید.',
        score=Decimal(score),
        grading_guide='راهنمای محرمانه مصحح',
        reference_answer='پاسخ معیار محرمانه',
    )


def make_pdf(name='answer.pdf'):
    return SimpleUploadedFile(
        name, b'%PDF-1.4\n' + b'x' * 50, content_type='application/pdf',
    )


class FullQuizLifecycleTest(TestCase):
    def setUp(self):
        self.admin_client = APIClient()
        self.student_client = APIClient()
        self.admin = create_admin()
        self.student = create_user()
        self.admin_client.force_authenticate(self.admin)
        self.student_client.force_authenticate(self.student)

    def test_step_01_admin_creates_quiz(self):
        now = timezone.now()
        r = self.admin_client.post('/api/managements/quizes/', {
            'title': 'آزمون پایان‌ترم',
            'description': 'فصل ۱ تا ۳',
            'duration_minutes': 45,
            'start_at': (now - timedelta(minutes=1)).isoformat(),
            'end_at': (now + timedelta(hours=3)).isoformat(),
            'max_attempts': 1,
            'max_answer_file_size_mb': 5,
            'max_files_per_question': 3,
            'allow_review_after_finish': True,
        }, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['title'], 'آزمون پایان‌ترم')
        self.assertEqual(r.data['status'], 'draft')

    def test_step_02_admin_creates_mcq_and_options(self):
        quiz = make_quiz(self.admin)
        r = self.admin_client.post('/api/managements/quiz-questions/', {
            'quiz': quiz.id, 'order': 1, 'question_type': 'mcq',
            'text_content': 'پایتخت ایران؟', 'score': '5.00',
            'is_required': True,
        }, format='json')
        self.assertEqual(r.status_code, 201)
        qid = r.data['id']
        for i, (text, is_corr) in enumerate([
            ('تهران', True), ('شیراز', False),
            ('اصفهان', False), ('مشهد', False),
        ]):
            rr = self.admin_client.post(
                f'/api/managements/quiz-questions/{qid}/options/',
                {'order': i + 1, 'text': text, 'is_correct': is_corr},
                format='json',
            )
            self.assertEqual(rr.status_code, 201, rr.data)
        quiz.refresh_from_db()
        self.assertEqual(quiz.total_score, Decimal('5.00'))

    def test_step_03_admin_creates_descriptive_question(self):
        quiz = make_quiz(self.admin)
        r = self.admin_client.post('/api/managements/quiz-questions/', {
            'quiz': quiz.id, 'order': 2, 'question_type': 'descriptive',
            'text_content': 'پاسخ را بارگذاری کنید.', 'score': '5.00',
            'grading_guide': 'راهنمای محرمانه',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['question_type'], 'descriptive')

    def test_step_04_admin_publishes_and_assigns(self):
        quiz = make_quiz(self.admin, status=Quiz.Status.DRAFT)
        make_mcq(quiz)
        r = self.admin_client.post(
            f'/api/managements/quizes/{quiz.id}/publish/', format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['status'], 'published')
        r = self.admin_client.post(
            f'/api/managements/quizes/{quiz.id}/assignments/',
            {'assign_all_users': True}, format='json',
        )
        self.assertEqual(r.status_code, 200)

    def test_step_05_student_can_see_and_start(self):
        quiz = make_quiz(self.admin)
        make_mcq(quiz)
        r = self.student_client.get('/api/quizes/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        r = self.student_client.get(f'/api/quizes/{quiz.slug}/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data['can_attempt'])
        r = self.student_client.post(
            f'/api/quizes/{quiz.slug}/start/', format='json',
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIn('uuid', r.data)
        self.assertEqual(r.data['status'], 'in_progress')
        self.assertGreater(r.data['seconds_remaining'], 0)

    def test_step_06_student_does_not_see_correct_answers(self):
        quiz = make_quiz(self.admin)
        make_mcq(quiz)
        make_desc(quiz)
        r = self.student_client.post(
            f'/api/quizes/{quiz.slug}/start/', format='json',
        )
        self.assertEqual(r.status_code, 200)
        for q in r.data['questions']:
            self.assertNotIn('grading_guide', q)
            self.assertNotIn('reference_answer', q)
            for opt in q['options']:
                self.assertNotIn('is_correct', opt)

    def test_step_07_student_saves_mcq_and_file(self):
        quiz = make_quiz(self.admin)
        mcq, correct = make_mcq(quiz, score='5.00')
        desc = make_desc(quiz, score='5.00')
        attempt = start_attempt(quiz, self.student)
        r = self.student_client.post(
            f'/api/quizes/attempt/{attempt.uuid}/save/',
            {'question_id': mcq.id, 'selected_option_id': correct.id},
            format='json',
        )
        self.assertEqual(r.status_code, 200, r.data)
        r = self.student_client.post(
            f'/api/quizes/attempt/{attempt.uuid}/save/',
            {'question_id': desc.id, 'files': [make_pdf()]},
            format='multipart',
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(
            Answer.objects.filter(attempt=attempt).count(), 2,
        )

    def test_step_08_student_finishes_attempt(self):
        quiz = make_quiz(self.admin)
        mcq, correct = make_mcq(quiz, score='5.00')
        desc = make_desc(quiz, score='5.00')
        attempt = start_attempt(quiz, self.student)
        save_answer(attempt, mcq.id, selected_option_id=correct.id)
        save_answer(attempt, desc.id, files=[make_pdf()])
        r = self.student_client.post(
            f'/api/quizes/attempt/{attempt.uuid}/finish/', format='json',
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['status'], 'submitted')

    def test_step_09_student_sees_pending_result(self):
        quiz = make_quiz(self.admin)
        mcq, correct = make_mcq(quiz)
        desc = make_desc(quiz)
        attempt = start_attempt(quiz, self.student)
        save_answer(attempt, mcq.id, selected_option_id=correct.id)
        save_answer(attempt, desc.id, files=[make_pdf()])
        finish_attempt(attempt, by_user=True)
        r = self.student_client.get(
            f'/api/quizes/attempt/{attempt.uuid}/result/', format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['result_status'], 'pending_grading')
        self.assertIsNone(r.data['passed'])

    def test_step_10_admin_sees_pending_grading(self):
        quiz = make_quiz(self.admin)
        mcq, correct = make_mcq(quiz)
        desc = make_desc(quiz)
        attempt = start_attempt(quiz, self.student)
        save_answer(attempt, mcq.id, selected_option_id=correct.id)
        save_answer(attempt, desc.id, files=[make_pdf()])
        finish_attempt(attempt, by_user=True)
        r = self.admin_client.get('/api/managements/quiz-grading/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['question_type'], 'descriptive')

    def test_step_11_admin_grades_and_attempt_finalized(self):
        quiz = make_quiz(self.admin, pass_score=Decimal('7.00'))
        mcq, correct = make_mcq(quiz, score='5.00')
        desc = make_desc(quiz, score='5.00')
        attempt = start_attempt(quiz, self.student)
        save_answer(attempt, mcq.id, selected_option_id=correct.id)
        save_answer(attempt, desc.id, files=[make_pdf()])
        finish_attempt(attempt, by_user=True)
        answer = Answer.objects.get(attempt=attempt, question=desc)
        r = self.admin_client.post(
            f'/api/managements/quiz-grading/{answer.id}/grade/',
            {'score': '4.50', 'feedback': 'خوب بود', 'finalize': True},
            format='json',
        )
        self.assertEqual(r.status_code, 200, r.data)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, QuizAttempt.Status.GRADED)
        self.assertEqual(attempt.total_score, Decimal('9.50'))

    def test_step_12_student_sees_final_result(self):
        quiz = make_quiz(self.admin, pass_score=Decimal('7.00'))
        mcq, correct = make_mcq(quiz, score='5.00')
        desc = make_desc(quiz, score='5.00')
        attempt = start_attempt(quiz, self.student)
        save_answer(attempt, mcq.id, selected_option_id=correct.id)
        save_answer(attempt, desc.id, files=[make_pdf()])
        finish_attempt(attempt, by_user=True)
        answer = Answer.objects.get(attempt=attempt, question=desc)
        grade_answer(
            answer, self.admin, score=Decimal('4.50'),
            feedback='خوب', finalize=True,
        )
        r = self.student_client.get(
            f'/api/quizes/attempt/{attempt.uuid}/result/', format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['result_status'], 'final')
        self.assertEqual(r.data['total_score'], '9.50')
        self.assertTrue(r.data['passed'])
        self.assertTrue(r.data['answers']['available'])


class TimeAndDeadlineTests(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user()

    def test_attempt_deadline_is_min_of_duration_and_end_at(self):
        quiz = make_quiz(
            self.admin,
            duration_minutes=30,
            end_at=timezone.now() + timedelta(minutes=10),
        )
        attempt = start_attempt(quiz, self.user)
        delta = (attempt.deadline_at - attempt.started_at).total_seconds()
        self.assertLess(abs(delta - 600), 5)

    def test_start_before_window_rejected(self):
        quiz = make_quiz(
            self.admin,
            start_at=timezone.now() + timedelta(hours=1),
            end_at=timezone.now() + timedelta(hours=2),
        )
        with self.assertRaises(ValidationError):
            start_attempt(quiz, self.user)

    def test_start_after_window_rejected(self):
        quiz = make_quiz(
            self.admin,
            start_at=timezone.now() - timedelta(hours=2),
            end_at=timezone.now() - timedelta(minutes=1),
        )
        with self.assertRaises(ValidationError):
            start_attempt(quiz, self.user)

    def test_save_answer_after_deadline_rejected(self):
        quiz = make_quiz(self.admin)
        mcq, _ = make_mcq(quiz)
        attempt = start_attempt(quiz, self.user)
        past = timezone.now() - timedelta(minutes=10)
        QuizAttempt.objects.filter(pk=attempt.pk).update(
            started_at=past - timedelta(minutes=30),
            deadline_at=past,
        )
        attempt.refresh_from_db()
        with self.assertRaises(ValidationError):
            save_answer(
                attempt, mcq.id,
                selected_option_id=mcq.options.first().id,
            )

    def test_auto_submit_closes_expired(self):
        quiz = make_quiz(self.admin)
        attempt = start_attempt(quiz, self.user)
        past = timezone.now() - timedelta(minutes=10)
        QuizAttempt.objects.filter(pk=attempt.pk).update(
            started_at=past - timedelta(minutes=30),
            deadline_at=past,
        )
        closed = auto_submit_expired()
        self.assertGreaterEqual(closed, 1)
        attempt.refresh_from_db()
        self.assertNotEqual(attempt.status, QuizAttempt.Status.IN_PROGRESS)


class SecurityIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = create_admin()
        self.user1 = create_user('u1@test.com')
        self.user2 = create_user('u2@test.com')
        self.quiz = make_quiz(self.admin)
        self.mcq, _ = make_mcq(self.quiz)
        self.desc = make_desc(self.quiz)

    def test_user_cannot_access_other_user_attempt(self):
        attempt2 = start_attempt(self.quiz, self.user2)
        self.client.force_authenticate(self.user1)
        r = self.client.get(f'/api/quizes/attempt/{attempt2.uuid}/')
        self.assertIn(r.status_code, (403, 404))

    def test_user_cannot_save_to_other_user_attempt(self):
        attempt2 = start_attempt(self.quiz, self.user2)
        self.client.force_authenticate(self.user1)
        r = self.client.post(
            f'/api/quizes/attempt/{attempt2.uuid}/save/',
            {'question_id': self.mcq.id}, format='json',
        )
        self.assertIn(r.status_code, (403, 404))

    def test_stranger_cannot_download_attachment(self):
        attempt1 = start_attempt(self.quiz, self.user1)
        save_answer(attempt1, self.desc.id, files=[make_pdf()])
        ans = Answer.objects.get(attempt=attempt1, question=self.desc)
        att = ans.attachments.first()
        self.client.force_authenticate(self.user2)
        r = self.client.get(
            f'/api/quizes/attempt/{attempt1.uuid}/attachments/{att.id}/download/'
        )
        self.assertIn(r.status_code, (403, 404))

    def test_anonymous_cannot_access_quizes(self):
        r = self.client.get('/api/quizes/')
        self.assertIn(r.status_code, (401, 403))

    def test_non_admin_cannot_access_managements(self):
        self.client.force_authenticate(self.user1)
        r = self.client.get('/api/managements/quizes/')
        self.assertIn(r.status_code, (401, 403))

    def test_invalid_file_extension_rejected(self):
        attempt = start_attempt(self.quiz, self.user1)
        bad = SimpleUploadedFile(
            'x.exe', b'MZ\x90', content_type='application/octet-stream',
        )
        with self.assertRaises(ValidationError):
            save_answer(attempt, self.desc.id, files=[bad])

    def test_fake_pdf_rejected(self):
        attempt = start_attempt(self.quiz, self.user1)
        fake = SimpleUploadedFile(
            'x.pdf', b'NOT PDF', content_type='application/pdf',
        )
        with self.assertRaises(ValidationError):
            save_answer(attempt, self.desc.id, files=[fake])


class AttemptLimitsTests(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user()

    def test_max_attempts_enforced(self):
        quiz = make_quiz(self.admin, max_attempts=1)
        attempt = start_attempt(quiz, self.user)
        finish_attempt(attempt, by_user=True)
        with self.assertRaises(PermissionDenied):
            start_attempt(quiz, self.user)

    def test_second_start_returns_same_attempt(self):
        quiz = make_quiz(self.admin)
        a1 = start_attempt(quiz, self.user)
        a2 = start_attempt(quiz, self.user)
        self.assertEqual(a1.pk, a2.pk)

    def test_unassigned_user_rejected(self):
        quiz = make_quiz(self.admin)
        other = create_user('other@test.com')
        QuizAssignment.objects.create(quiz=quiz, user=other)
        with self.assertRaises(PermissionDenied):
            start_attempt(quiz, self.user)


class GradingIntegrationTests(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user = create_user()
        self.quiz = make_quiz(self.admin)
        self.mcq, self.correct = make_mcq(self.quiz, score='5.00')
        self.desc = make_desc(self.quiz, score='5.00')
        self.attempt = start_attempt(self.quiz, self.user)
        save_answer(
            self.attempt, self.mcq.id,
            selected_option_id=self.correct.id,
        )
        save_answer(self.attempt, self.desc.id, files=[make_pdf()])
        finish_attempt(self.attempt, by_user=True)
        self.answer = Answer.objects.get(
            attempt=self.attempt, question=self.desc,
        )

    def test_grade_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            grade_answer(
                self.answer, self.admin,
                score=Decimal('10.00'), finalize=True,
            )

    def test_negative_score_rejected(self):
        with self.assertRaises(ValidationError):
            grade_answer(
                self.answer, self.admin,
                score=Decimal('-1.00'), finalize=True,
            )

    def test_partial_grading_keeps_submitted(self):
        grade_answer(
            self.answer, self.admin,
            score=Decimal('4.00'), finalize=False,
        )
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, QuizAttempt.Status.SUBMITTED)

    def test_finalize_completes(self):
        grade_answer(
            self.answer, self.admin,
            score=Decimal('4.00'), finalize=True,
        )
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, QuizAttempt.Status.GRADED)
        self.assertEqual(self.attempt.total_score, Decimal('9.00'))


class SignalIntegrationTests(TestCase):
    def setUp(self):
        self.admin = create_admin()

    def test_quiz_total_score_auto_updated(self):
        quiz = make_quiz(self.admin)
        self.assertEqual(quiz.total_score, Decimal('0.00'))
        make_mcq(quiz, score='5.00')
        quiz.refresh_from_db()
        self.assertEqual(quiz.total_score, Decimal('5.00'))
        make_desc(quiz, score='3.00')
        quiz.refresh_from_db()
        self.assertEqual(quiz.total_score, Decimal('8.00'))

    def test_question_delete_recalculates_total(self):
        quiz = make_quiz(self.admin)
        mcq, _ = make_mcq(quiz, score='5.00')
        quiz.refresh_from_db()
        self.assertEqual(quiz.total_score, Decimal('5.00'))
        mcq.delete()
        quiz.refresh_from_db()
        self.assertEqual(quiz.total_score, Decimal('0.00'))

    def test_only_one_correct_option(self):
        quiz = make_quiz(self.admin)
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