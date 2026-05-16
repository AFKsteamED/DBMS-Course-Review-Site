import json
from pathlib import Path

from django.db.models import Max
from django.core.management.base import BaseCommand

from reviews.models import Course, Professor, Review


class Command(BaseCommand):
    help = 'Import professors and courses from all_courses.json (bulk_create for speed)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=str(Path(__file__).resolve().parents[3] / 'all_courses.json'),
            help='Path to courses JSON (default: all_courses.json in project root)',
        )
        parser.add_argument(
            '--no-clear',
            action='store_true',
            help='Skip clearing existing Course and Professor rows before importing',
        )

    def handle(self, *args, **options):
        json_path = options['file']
        self.stdout.write(f'Loading {json_path} ...')

        with open(json_path, encoding='utf-8') as f:
            entries = json.load(f)

        self.stdout.write(f'  {len(entries)} entries loaded.')

        if not options['no_clear']:
            r = Review.objects.all().delete()
            c = Course.objects.all().delete()
            p = Professor.objects.all().delete()
            self.stdout.write(
                f'Cleared: {r[0]} reviews, {c[0]} courses, {p[0]} professors'
            )

        # ── Step 1: 收集所有唯一教授名稱 ────────────────────────────────────────
        # professor_name → department（取第一次出現的 department）
        prof_dept: dict[str, str] = {}
        for entry in entries:
            name = entry['professor_name']
            if name not in prof_dept:
                prof_dept[name] = entry['department']

        # 取得已存在的教授（避免重複）
        existing_profs = {p.professor_name: p for p in Professor.objects.all()}
        next_id = (Professor.objects.aggregate(m=Max('professor_id'))['m'] or 0) + 1

        new_profs = [
            Professor(
                professor_id=next_id + i,
                professor_name=name,
                department=dept,
            )
            for i, (name, dept) in enumerate(
                (n, d) for n, d in prof_dept.items() if n not in existing_profs
            )
        ]

        if new_profs:
            Professor.objects.bulk_create(new_profs, batch_size=500)
            self.stdout.write(f'  Professors inserted: {len(new_profs)}')

        # 重新載入完整教授對照表
        prof_cache: dict[str, Professor] = {
            p.professor_name: p for p in Professor.objects.all()
        }

        # ── Step 2: 批次插入課程 ─────────────────────────────────────────────────
        existing_course_ids: set[str] = set(
            Course.objects.values_list('course_id', flat=True)
        )

        new_courses = []
        skipped = 0
        for entry in entries:
            if entry['course_id'] in existing_course_ids:
                skipped += 1
                continue
            prof = prof_cache.get(entry['professor_name'])
            if prof is None:
                skipped += 1
                continue
            new_courses.append(Course(
                course_id=entry['course_id'],
                course_name=entry['course_name'],
                credits=entry['credits'],
                department=entry['department'],
                professor=prof,
            ))
            existing_course_ids.add(entry['course_id'])  # 防止 JSON 內重複

        if new_courses:
            Course.objects.bulk_create(new_courses, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f'Done — 總教授數: {len(prof_cache)}, '
            f'課程新增: {len(new_courses)}, '
            f'略過: {skipped}'
        ))
