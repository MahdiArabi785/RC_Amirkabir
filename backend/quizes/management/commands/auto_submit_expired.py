# quizes/management/commands/auto_submit_expired.py
"""
بستن تلاش‌های منقضی‌شده.

اجرا:
    python manage.py auto_submit_expired
    python manage.py auto_submit_expired --dry-run

توصیه production: cron هر ۱-۲ دقیقه:
    * * * * * cd /path/to/project && \\
        .venv/bin/python manage.py auto_submit_expired
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from quizes.models import QuizAttempt
from quizes.services import auto_submit_expired


class Command(BaseCommand):
    help = 'بستن تلاش‌های آزمون که deadline آن‌ها گذشته است.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='فقط تعداد را نشان بده، چیزی را نبند.',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        qs = QuizAttempt.objects.filter(
            status=QuizAttempt.Status.IN_PROGRESS,
            deadline_at__lte=now,
        )
        count = qs.count()

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(
                f'[dry-run] {count} attempt(s) past deadline would be closed.'
            ))
            return

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired attempts.'))
            return

        closed = auto_submit_expired()
        self.stdout.write(self.style.SUCCESS(
            f'Closed {closed}/{count} expired attempt(s).'
        ))