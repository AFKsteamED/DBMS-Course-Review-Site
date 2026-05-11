import json
from pathlib import Path

from django.db.models import Max
from django.core.management.base import BaseCommand

from reviews.models import Course, Professor, Review


class Command(BaseCommand):
    help = 'Import professors and courses from courses.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=str(Path(__file__).resolve().parents[3] / 'courses.json'),
            help='Path to courses.json (default: project root)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing Course and Professor rows before importing',
        )

    def handle(self, *args, **options):
        json_path = options['file']
        self.stdout.write(f'Loading {json_path} ...')

        with open(json_path, encoding='utf-8') as f:
            entries = json.load(f)

        if options['clear']:
            r = Review.objects.all().delete()
            c = Course.objects.all().delete()
            p = Professor.objects.all().delete()
            self.stdout.write(
                f'Cleared: {r[0]} reviews, {c[0]} courses, {p[0]} professors'
            )

        next_prof_id = (Professor.objects.aggregate(m=Max('professor_id'))['m'] or 0) + 1

        prof_cache: dict[str, Professor] = {}
        for prof in Professor.objects.all():
            prof_cache[prof.professor_name] = prof

        courses_created = 0
        courses_skipped = 0

        for entry in entries:
            prof_name = entry['professor_name']

            if prof_name not in prof_cache:
                prof = Professor.objects.create(
                    professor_id=next_prof_id,
                    professor_name=prof_name,
                    department=entry['department'],
                )
                next_prof_id += 1
                prof_cache[prof_name] = prof
            professor = prof_cache[prof_name]

            if Course.objects.filter(course_id=entry['course_id']).exists():
                courses_skipped += 1
                continue

            Course.objects.create(
                course_id=entry['course_id'],
                course_name=entry['course_name'],
                credits=entry['credits'],
                department=entry['department'],
                professor=professor,
            )
            courses_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done — professors: {len(prof_cache)}, '
            f'courses created: {courses_created}, '
            f'skipped: {courses_skipped}'
        ))
