import random
import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Max

from reviews.models import Course, Review, Student

COMMENTS = [
    '老師上課很認真，推薦！',
    '考試偏難，建議提早準備。',
    '作業不多，但期末考很硬。',
    '很有收穫的一門課。',
    '輕鬆的選修，分數給得不錯。',
    '老師講解清楚，上課不無聊。',
    '報告很多，需要花時間。',
    '適合想輕鬆過的同學。',
    '課程內容豐富，收穫滿滿。',
    '期中考有點難，但老師有劃重點。',
    '點名不嚴，但要認真準備期末。',
    '課程對未來工作很有幫助。',
    '老師人很好，有問題都會解答。',
    '作業量適中，不會壓力太大。',
    '課程節奏稍快，建議提前預習。',
    '小班制，和老師互動機會多。',
    '期末 project 很充實，學到不少實戰技巧。',
    '內容偏理論，建議有基礎再選。',
    '評分標準清楚，努力就有好成績。',
    '上課有點無聊，但考試很好過。',
    '老師給分不手軟，大推！',
    '對找工作幫助很大，值得修。',
    '課程難度偏高，需要多花時間複習。',
    '輕鬆有趣，下課後還會查相關資料。',
    '老師要求嚴格，但學到的東西很扎實。',
    None,  # 留空
    None,
    None,
]

HALF_SCORES = [i * 0.5 for i in range(1, 11)]  # 0.5, 1.0, ..., 5.0

NAMES = [
    '王小明', '李美玲', '陳建宏', '林雅婷', '張志偉',
    '黃淑芬', '吳俊賢', '劉怡君', '蔡文彬', '鄭雪晴',
    '許家豪', '謝宛蓉', '江柏翰', '邱雅惠', '洪志遠',
    '葉美君', '賴俊廷', '何雨晴', '蕭信宏', '顏宜珊',
]
MAJORS = ['經濟系', '計財系', '科管系', '工業工程系', '資訊工程系', '電機系']

START_DATE = date(2024, 9, 1)
END_DATE = date(2025, 6, 30)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days

PASSWORD = 'test1234'
NUM_STUDENTS = 20
SEED_USERNAME_PATTERN = r'^11\d1\d{4}$'
COURSE_RATIO = 0.4   # 40% 課程加入評價


def _rand_sid() -> int:
    """產生格式 11X1XXXX 的 8 位學號。"""
    return int(f'11{random.randint(0, 9)}1{random.randint(0, 9999):04d}')


class Command(BaseCommand):
    help = '建立測試學生帳號與隨機評價資料'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='執行前先刪除上次 seed 產生的資料',
        )
        parser.add_argument(
            '--add',
            type=int,
            default=0,
            metavar='N',
            help='使用現有 seed 學生新增 N 筆額外評價（分布全校各系所）',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_seed_data()

        if options['add'] > 0:
            students = self._get_existing_seed_students()
            if not students:
                self._out('[!] 找不到 seed 學生，請先執行完整 seed 或加上 --clear 重建')
                return
            self._add_extra_reviews(options['add'], students)
        else:
            students = self._create_students()
            review_count, courses_with, courses_without = self._create_reviews(students)
            self._print_summary(students, review_count, courses_with, courses_without)

    # ------------------------------------------------------------------ #

    def _out(self, msg: str = ''):
        """寫入 UTF-8，避免 Windows cp950 無法編碼的問題。"""
        encoded = (msg + '\n').encode('utf-8', errors='replace')
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()

    def _get_existing_seed_students(self) -> list[Student]:
        test_ids = [
            int(u) for u in
            User.objects.filter(username__regex=SEED_USERNAME_PATTERN)
            .values_list('username', flat=True)
        ]
        students = list(Student.objects.filter(pk__in=test_ids))
        self._out(f'找到 {len(students)} 位現有 seed 學生')
        return students

    def _add_extra_reviews(self, n: int, students: list[Student]):
        # 按系所分組，確保分布均勻
        all_courses = list(Course.objects.all())
        dept_courses: dict[str, list] = defaultdict(list)
        for c in all_courses:
            dept_courses[c.department or '其他'].append(c)
        departments = list(dept_courses.keys())

        next_id = (Review.objects.aggregate(m=Max('review_id'))['m'] or 0) + 1
        to_create = []
        dept_counter: dict[str, int] = defaultdict(int)

        for i in range(n):
            dept   = random.choice(departments)
            course = random.choice(dept_courses[dept])
            student = random.choice(students)

            s = random.choice(HALF_SCORES)
            e = random.choice(HALF_SCORES)
            v = random.choice(HALF_SCORES)
            overall = float(
                ((Decimal(str(s)) + Decimal(str(e)) + Decimal(str(v))) / 3)
                .quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            )
            rand_days = random.randint(0, DATE_RANGE_DAYS)

            to_create.append(Review(
                review_id=next_id + i,
                student=student,
                course=course,
                sweetness_score=s,
                easiness_score=e,
                value_score=v,
                overall_score=overall,
                comment_text=random.choice(COMMENTS),
                review_date=START_DATE + timedelta(days=rand_days),
            ))
            dept_counter[dept] += 1

        Review.objects.bulk_create(to_create)
        self._out(f'新增 {n} 筆評價完成，涵蓋 {len(dept_counter)} 個系所')
        self._out(f'資料庫評價總筆數：{Review.objects.count()}')

        # 分數分布統計
        scores = [r.sweetness_score for r in to_create]
        avg = sum(scores) / len(scores)
        self._out(f'甜度平均分（抽樣）：{avg:.2f}（均勻分布於 0.5–5.0）')

    def _clear_seed_data(self):
        test_users = User.objects.filter(username__regex=SEED_USERNAME_PATTERN)
        test_ids = [int(u) for u in test_users.values_list('username', flat=True)]
        deleted_reviews, _ = Review.objects.filter(student_id__in=test_ids).delete()
        deleted_students, _ = Student.objects.filter(pk__in=test_ids).delete()
        deleted_users, _ = test_users.delete()
        self._out(
            f'[清除] {deleted_users} 位帳號、{deleted_students} 位學生、'
            f'{deleted_reviews} 筆評價已刪除'
        )

    def _create_students(self) -> list[Student]:
        students = []
        names = NAMES[:]
        random.shuffle(names)

        for i in range(NUM_STUDENTS):
            for _ in range(100):
                sid = _rand_sid()
                if (not User.objects.filter(username=str(sid)).exists()
                        and not Student.objects.filter(pk=sid).exists()):
                    break
            else:
                self._out('  [!] 無法產生不重複學號，跳過。')
                continue

            User.objects.create_user(username=str(sid), password=PASSWORD)
            student = Student.objects.create(
                student_id=sid,
                student_name=names[i],
                major=random.choice(MAJORS),
                year_level=random.randint(1, 4),
            )
            students.append(student)
            self._out(
                f'  建立帳號：{sid}  {names[i]}  '
                f'{student.major}  {student.year_level} 年級'
            )

        self._out(f'\n共建立 {len(students)} 位學生帳號（密碼：{PASSWORD}）')
        return students

    def _create_reviews(
        self, students: list[Student]
    ) -> tuple[int, list[Course], list[Course]]:
        all_courses = list(Course.objects.select_related('professor').all())
        random.shuffle(all_courses)

        n_with = round(len(all_courses) * COURSE_RATIO)
        courses_with = all_courses[:n_with]
        courses_without = all_courses[n_with:]

        next_id = (Review.objects.aggregate(m=Max('review_id'))['m'] or 0) + 1
        review_count = 0
        reviews_to_create = []

        for course in courses_with:
            for _ in range(random.randint(1, 5)):
                rand_days = random.randint(0, DATE_RANGE_DAYS)
                reviews_to_create.append(Review(
                    review_id=next_id,
                    student=random.choice(students),
                    course=course,
                    sweetness_score=random.randint(1, 5),
                    easiness_score=random.randint(1, 5),
                    value_score=random.randint(1, 5),
                    overall_score=random.randint(1, 5),
                    comment_text=random.choice(COMMENTS),
                    review_date=START_DATE + timedelta(days=rand_days),
                ))
                next_id += 1
                review_count += 1

        Review.objects.bulk_create(reviews_to_create)
        self._out(f'共建立 {review_count} 筆評價')
        return review_count, courses_with, courses_without

    def _print_summary(
        self,
        students: list[Student],
        review_count: int,
        courses_with: list[Course],
        courses_without: list[Course],
    ):
        w = len(courses_with)
        wo = len(courses_without)

        self._out()
        self._out('=' * 62)
        self._out(f'  學生帳號：{len(students)} 位　密碼統一：{PASSWORD}')
        self._out(f'  評價總筆數：{review_count} 筆')
        self._out(f'  有評價課程：{w} 門（{COURSE_RATIO*100:.0f}%）')
        self._out(f'  無評價課程：{wo} 門')
        self._out(f'  課程總數：{w + wo} 門')
        self._out('=' * 62)

        self._out('\n【有評價課程（前 20 筆範例）】')
        for c in sorted(courses_with, key=lambda x: x.course_id)[:20]:
            cnt = Review.objects.filter(course=c).count()
            self._out(f'  [v] {c.course_id:<18} {c.course_name[:20]:<20} ({cnt} 筆)')

        self._out('\nSeed 完成！')
