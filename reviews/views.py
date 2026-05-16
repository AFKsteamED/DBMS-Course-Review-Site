from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, F, Max, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LoginForm, RegisterForm, ReviewForm
from .models import Course, Professor, Review, Student


def home(request):
    top_courses_qs = (
        Course.objects
        .annotate(avg_overall=Avg('review__overall_score'))
        .filter(avg_overall__isnull=False)       # 只取有評價的課程
        .select_related('professor')
        .order_by('-avg_overall')
    )
    if settings.DEBUG:
        print('\n[DEBUG] Top5 SQL:', top_courses_qs.query, '\n')
    top_courses = top_courses_qs[:5]
    latest_reviews = (
        Review.objects
        .select_related('student', 'course')
        .order_by('-review_date')[:5]
    )
    return render(request, 'reviews/home.html', {
        'top_courses': top_courses,
        'latest_reviews': latest_reviews,
        'course_count': Course.objects.count(),
        'professor_count': Professor.objects.count(),
        'review_count': Review.objects.count(),
    })


SORT_FIELDS = {
    'overall':   F('avg_overall').desc(nulls_last=True),
    'sweetness': F('avg_sweetness').desc(nulls_last=True),
    'easiness':  F('avg_easiness').desc(nulls_last=True),
    'value':     F('avg_value').desc(nulls_last=True),
}


def course_list(request):
    query    = request.GET.get('q', '').strip()
    dept     = request.GET.get('dept', '')
    semester = request.GET.get('semester', '')
    sort     = request.GET.get('sort', '')

    courses = Course.objects.select_related('professor').annotate(
        avg_overall=Avg('review__overall_score'),
        avg_sweetness=Avg('review__sweetness_score'),
        avg_easiness=Avg('review__easiness_score'),
        avg_value=Avg('review__value_score'),
    )

    if query:
        courses = courses.filter(
            Q(course_name__icontains=query) |
            Q(professor__professor_name__icontains=query)
        )
    if dept:
        courses = courses.filter(department=dept)
    if semester == '114上':
        courses = courses.filter(course_id__startswith='11410')
    elif semester == '114下':
        courses = courses.filter(course_id__startswith='11420')

    if sort in SORT_FIELDS:
        courses = courses.order_by(SORT_FIELDS[sort], 'course_name')
    else:
        # 預設：有評價的課程依課名排序，無評價的排在後面
        courses = courses.order_by(
            F('avg_overall').desc(nulls_last=True), 'course_name'
        )

    departments = (
        Course.objects
        .values_list('department', flat=True)
        .distinct()
        .order_by('department')
    )

    return render(request, 'reviews/course_list.html', {
        'courses': courses,
        'query': query,
        'dept': dept,
        'semester': semester,
        'sort': sort,
        'departments': departments,
    })


def course_detail(request, course_id):
    course = get_object_or_404(Course.objects.select_related('professor'), pk=course_id)
    stats = Review.objects.filter(course=course).aggregate(
        avg_sweetness=Avg('sweetness_score'),
        avg_easiness=Avg('easiness_score'),
        avg_value=Avg('value_score'),
        avg_overall=Avg('overall_score'),
    )
    reviews = (
        Review.objects
        .filter(course=course)
        .select_related('student')
        .order_by('-review_date')
    )
    return render(request, 'reviews/course_detail.html', {
        'course': course,
        'stats': stats,
        'reviews': reviews,
    })


@login_required
def add_review(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    student_id = int(request.user.username)
    student = get_object_or_404(Student, pk=student_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            max_id = Review.objects.aggregate(max_id=Max('review_id'))['max_id'] or 0
            Review.objects.create(
                review_id=max_id + 1,
                student=student,
                course=course,
                sweetness_score=int(form.cleaned_data['sweetness_score']),
                easiness_score=int(form.cleaned_data['easiness_score']),
                value_score=int(form.cleaned_data['value_score']),
                overall_score=int(form.cleaned_data['overall_score']),
                comment_text=form.cleaned_data['comment_text'] or None,
                review_date=timezone.now().date(),
            )
            return redirect('course_detail', course_id=course_id)
    else:
        form = ReviewForm()

    return render(request, 'reviews/add_review.html', {
        'form': form,
        'course': course,
        'student': student,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data['student_id']
            user = User.objects.create_user(
                username=str(student_id),
                password=form.cleaned_data['password'],
            )
            Student.objects.create(
                student_id=student_id,
                student_name=form.cleaned_data['student_name'],
                major=form.cleaned_data['major'] or None,
                year_level=int(form.cleaned_data['year_level']),
            )
            login(request, user)
            messages.success(request, f'歡迎加入！學號 {student_id} 註冊成功。')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'reviews/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        next_url = request.POST.get('next', next_url)
        form = LoginForm(request.POST)
        if form.is_valid():
            student_id = str(form.cleaned_data['student_id'])
            password = form.cleaned_data['password']
            user = authenticate(request, username=student_id, password=password)
            if user is not None:
                login(request, user)
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('home')
            form.add_error(None, '學號或密碼錯誤，請再試一次。')
    else:
        form = LoginForm()
    return render(request, 'reviews/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    student_id = int(request.user.username)
    student = get_object_or_404(Student, pk=student_id)
    reviews = (
        Review.objects
        .filter(student=student)
        .select_related('course')
        .order_by('-review_date')
    )
    return render(request, 'reviews/profile.html', {
        'student': student,
        'reviews': reviews,
    })


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review.objects.select_related('course', 'student'), pk=review_id)
    student_id = int(request.user.username)
    if review.student.student_id != student_id:
        return HttpResponseForbidden('你沒有權限修改此評價。')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review.sweetness_score = int(form.cleaned_data['sweetness_score'])
            review.easiness_score = int(form.cleaned_data['easiness_score'])
            review.value_score = int(form.cleaned_data['value_score'])
            review.overall_score = int(form.cleaned_data['overall_score'])
            review.comment_text = form.cleaned_data['comment_text'] or None
            review.save()
            messages.success(request, '評價已成功更新。')
            return redirect('profile')
    else:
        form = ReviewForm(initial={
            'sweetness_score': review.sweetness_score,
            'easiness_score': review.easiness_score,
            'value_score': review.value_score,
            'overall_score': review.overall_score,
            'comment_text': review.comment_text or '',
        })

    return render(request, 'reviews/edit_review.html', {
        'form': form,
        'review': review,
        'course': review.course,
    })


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review.objects.select_related('student'), pk=review_id)
    student_id = int(request.user.username)
    if review.student.student_id != student_id:
        return HttpResponseForbidden('你沒有權限刪除此評價。')

    if request.method == 'POST':
        review.delete()
        messages.success(request, '評價已成功刪除。')
    return redirect('profile')
