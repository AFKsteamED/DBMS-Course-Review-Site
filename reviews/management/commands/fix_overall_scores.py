from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '將所有 Review 的 overall_score 重新計算為三項分數平均值並更新。'

    def handle(self, *args, **options):
        sql = """
            UPDATE "Review"
            SET overall_score = ROUND(
                (sweetness_score + easiness_score + value_score) / 3.0,
                1
            )
            WHERE overall_score IS DISTINCT FROM ROUND(
                (sweetness_score + easiness_score + value_score) / 3.0,
                1
            );
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            updated = cursor.rowcount

        self.stdout.write(
            self.style.SUCCESS(f'完成：更新了 {updated} 筆 overall_score。')
        )
