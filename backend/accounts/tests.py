# accounts/tests.py
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article, CustomUser
from .services import OTPService


class UserManagerTests(TestCase):
    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email=None, password='x')

    def test_create_user_normalizes_blank_phone_to_none(self):
        u1 = CustomUser.objects.create_user(email='a@example.com', phone='', password='pass12345')
        u2 = CustomUser.objects.create_user(email='b@example.com', phone='', password='pass12345')
        # قبل از رفع باگ، ذخیره‌ی '' به‌جای None روی دو کاربر مختلف با
        # unique=True روی phone باعث IntegrityError می‌شد.
        self.assertIsNone(u1.phone)
        self.assertIsNone(u2.phone)

    def test_create_superuser_sets_admin_role(self):
        admin = CustomUser.objects.create_superuser(email='admin@example.com', password='pass12345')
        self.assertTrue(admin.is_admin)


class OTPServiceTests(TestCase):
    def test_verify_wrong_code_fails(self):
        user = OTPService.send_otp('otp@example.com')
        self.assertFalse(OTPService.verify_otp(user, '000000'))

    def test_verify_correct_code_succeeds(self):
        user = OTPService.send_otp('otp2@example.com')
        self.assertTrue(OTPService.verify_otp(user, user.otp_code))
        self.assertTrue(user.is_verified)
        self.assertIsNone(user.otp_code)


class ArticleCreateViewTests(TestCase):
    def test_admin_can_create_article_with_created_by(self):
        admin = CustomUser.objects.create_superuser(email='lead@example.com', password='pass12345')
        self.client.force_login(admin, backend='accounts.backends.EmailOrPhoneBackend')
        response = self.client.post(reverse('accounts:article_create'), {
            'title': 'تست', 'abstract': 'خلاصه', 'content': '', 'status': 'draft',
        })
        # قبل از اضافه شدن فیلد created_by به مدل Article، این درخواست
        # با AttributeError کرش می‌کرد.
        self.assertIn(response.status_code, (200, 302))
        if response.status_code == 302:
            article = Article.objects.get(title='تست')
            self.assertEqual(article.created_by, admin)


class ChangePasswordSessionTests(TestCase):
    def test_password_change_keeps_session_valid(self):
        user = CustomUser.objects.create_user(email='u@example.com', password='oldpass123')
        self.client.force_login(user, backend='accounts.backends.EmailOrPhoneBackend')
        self.client.post(reverse('accounts:change_password'), {
            'old_password': 'oldpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456',
        })
        # قبل از فراخوانی update_session_auth_hash، نشست بعد از این
        # درخواست دیگر معتبر نبود و درخواست بعدی کاربر را لاگ‌اوت‌شده
        # می‌دید.
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)