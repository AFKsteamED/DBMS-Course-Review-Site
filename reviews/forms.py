from django import forms
from django.contrib.auth.models import User

# 0.5, 1.0, 1.5, ..., 5.0
SCORE_CHOICES = [(f'{i / 2:.1f}', f'{i / 2:.1f}') for i in range(1, 11)]


class ReviewForm(forms.Form):
    sweetness_score = forms.ChoiceField(
        label='甜度（課程輕鬆程度）',
        choices=SCORE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    easiness_score = forms.ChoiceField(
        label='涼度（作業/考試難度）',
        choices=SCORE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    value_score = forms.ChoiceField(
        label='含金量（學習收穫）',
        choices=SCORE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    comment_text = forms.CharField(
        label='評論內容',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '請分享您對這門課的心得（選填）',
        }),
    )


class RegisterForm(forms.Form):
    student_id = forms.IntegerField(
        label='學號',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '請輸入學號'}),
    )
    student_name = forms.CharField(
        label='姓名',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入姓名'}),
    )
    major = forms.CharField(
        label='科系',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入科系（選填）'}),
    )
    year_level = forms.ChoiceField(
        label='年級',
        choices=[(1, '一年級'), (2, '二年級'), (3, '三年級'), (4, '四年級')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    password = forms.CharField(
        label='密碼',
        min_length=6,
        max_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '6~8 位字元'}),
    )
    confirm_password = forms.CharField(
        label='確認密碼',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '再輸入一次密碼'}),
    )

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id']
        if User.objects.filter(username=str(student_id)).exists():
            raise forms.ValidationError('此學號已經註冊過，請直接登入。')
        return student_id

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', '兩次密碼輸入不一致。')
        return cleaned_data


class LoginForm(forms.Form):
    student_id = forms.IntegerField(
        label='學號',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '請輸入學號'}),
    )
    password = forms.CharField(
        label='密碼',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '請輸入密碼'}),
    )
