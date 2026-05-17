from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Student(models.Model):
    student_id = models.IntegerField(primary_key=True)
    student_name = models.CharField(max_length=50)
    major = models.CharField(max_length=50, null=True, blank=True)
    year_level = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'Student'

    def __str__(self):
        return self.student_name


class Professor(models.Model):
    professor_id = models.IntegerField(primary_key=True)
    professor_name = models.CharField(max_length=50)
    department = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'Professor'

    def __str__(self):
        return self.professor_name


class Course(models.Model):
    course_id = models.CharField(max_length=30, primary_key=True)
    course_name = models.CharField(max_length=100)
    credits = models.IntegerField()
    department = models.CharField(max_length=50, null=True, blank=True)
    professor = models.ForeignKey(
        Professor,
        on_delete=models.RESTRICT,
        db_column='professor_id',
    )

    class Meta:
        db_table = 'Course'

    def __str__(self):
        return self.course_name



SCORE_VALIDATORS = [MinValueValidator(Decimal('0.5')), MaxValueValidator(Decimal('5.0'))]


class Review(models.Model):
    review_id = models.IntegerField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.RESTRICT,
        db_column='student_id',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.RESTRICT,
        db_column='course_id',
    )
    sweetness_score = models.DecimalField(max_digits=2, decimal_places=1, validators=SCORE_VALIDATORS)
    easiness_score = models.DecimalField(max_digits=2, decimal_places=1, validators=SCORE_VALIDATORS)
    value_score = models.DecimalField(max_digits=2, decimal_places=1, validators=SCORE_VALIDATORS)
    overall_score = models.DecimalField(max_digits=2, decimal_places=1, validators=SCORE_VALIDATORS)
    comment_text = models.CharField(max_length=500, null=True, blank=True)
    review_date = models.DateField()

    class Meta:
        db_table = 'Review'

    def __str__(self):
        return f'Review {self.review_id} by {self.student} on {self.course}'
