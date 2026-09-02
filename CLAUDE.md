# 課程評價系統

## 技術棧
- Django 6.0 + Python 3.12
- PostgreSQL 15
- Bootstrap 5（前端）
- WhiteNoise（靜態檔案）、Gunicorn（WSGI）

## 資料庫
- 名稱：course_review_db
- 4 張資料表：Student, Professor, Course, Review
  （原 Enrollment 表未使用已移除）

## 評分規則
- sweetness_score（甜度）、easiness_score（涼度）、
  value_score（含金量）、overall_score：皆為 0.5~5.0 分（半星）
- overall_score 由三項平均自動計算，不開放手動輸入

## 注意事項
- 使用繁體中文介面
- 所有 template 放在 reviews/templates/reviews/