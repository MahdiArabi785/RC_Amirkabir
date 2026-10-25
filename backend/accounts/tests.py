# accounts/tests.py
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Article, CustomUser
from .services import OTPService


class UserManagerTests(TestCase):
    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email=None, password='x')

    def test_create_user_normalizes_blank_phone_to_none(self):
        u1 = CustomUser.objects.create_user(
            email='a@example.com', phone='', password='pass12345',
        )
        u2 = CustomUser.objects.create_user(
            email='b@example.com', phone='', password='pass12345',
        )
        self.assertIsNone(u1.phone)
        self.assertIsNone(u2.phone)

    def test_create_superuser_sets_admin_role(self):
        admin = CustomUser.objects.create_superuser(
            email='admin@example.com', password='pass12345',
        )
        self.assertTrue(admin.is_admin)


class OTPServiceTests(TestCase):
    def test_verify_wrong_code_fails(self):
        user = CustomUser.objects.create_user(
            email='otp@example.com', password='pass12345', is_active=True,
        )
        OTPService.send_otp('otp@example.com')
        user.refresh_from_db()
        wrong = '000000' if user.otp_code != '000000' else '111111'
        self.assertFalse(OTPService.verify_otp(user, wrong))

    def test_verify_correct_code_succeeds(self):
        user = CustomUser.objects.create_user(
            email='otp2@example.com', password='pass12345', is_active=True,
        )
        OTPService.send_otp('otp2@example.com')
        user.refresh_from_db()
        self.assertTrue(OTPService.verify_otp(user, user.otp_code))
        self.assertTrue(user.is_verified)
        self.assertIsNone(user.otp_code)

    def test_send_otp_does_not_create_unknown_user(self):
        result = OTPService.send_otp('unknown@example.com')
        self.assertIsNone(result)
        self.assertEqual(
            CustomUser.objects.filter(email='unknown@example.com').count(), 0,
        )


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_signup_creates_inactive_user(self):
        response = self.client.post('/api/accounts/signup/', {
            'email': 'new@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(email='new@example.com')
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_verified)

    def test_login_returns_jwt(self):
        user = CustomUser.objects.create_user(
            email='login@example.com', password='pass12345',
        )
        user.is_active = True
        user.save()
        response = self.client.post('/api/accounts/login/', {
            'identifier': 'login@example.com',
            'password': 'pass12345',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_profile_requires_auth(self):
        response = self.client.get('/api/accounts/profile/')
        self.assertIn(response.status_code, (401, 403))


class ArticleAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = CustomUser.objects.create_superuser(
            email='lead@example.com', password='pass12345',
        )

    def test_admin_can_create_article_with_created_by(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/accounts/articles/', {
            'title': 'تست', 'abstract': 'خلاصه',
            'content': '', 'status': 'draft',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        article = Article.objects.get(title='تست')
        self.assertEqual(article.created_by, self.admin)

    def test_anonymous_cannot_create_article(self):
        response = self.client.post('/api/accounts/articles/', {
            'title': 'x', 'abstract': 'y',
        }, format='json')
        self.assertIn(response.status_code, (401, 403))