<div align="center">

# 🎓 清大課程評價平台
### NTHU Course Review Platform

一個為國立清華大學學生打造的課程評價系統 — 從 **甜度**、**涼度**、**含金量** 三個維度，幫你在選課前看見同學的真實心得。

<br/>

[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)

<sub>國立清華大學 · 科技管理學院學士班27級 · DBMS 課程期末專案 · 2026</sub>

</div>

---

## 一、專案簡介

清大目前缺乏一個結構化的課程評價平台，學生選課時往往只能依賴口耳相傳或社群媒體上零散的資訊。本專案以 DBMS 課程期末作業為契機，結合全端開發技術，打造一個真正可用的課程評價工具，收錄 **114 學年度上下學期全校 5,000+ 門課程**。

> **三維評分哲學**：不同於單一星等，本平台將課程拆解為「甜度（給分）／涼度（負擔）／含金量（收穫）」，讓每個人依自己的選課目標做出判斷。

<br/>

## 二、核心功能

| 功能 | 說明 |
|------|------|
| **熱門課程排名** | 以加權公式 `平均分數 × log(評價數 + 1)` 排序，至少 3 筆評價才入榜，避免少數評價灌水 |
| **多條件篩選** | 關鍵字（課名／教授）、開課系所、學期、排序方式自由組合，後端一次查詢完成 |
| **半星評分系統** | 以 0.5 顆星為單位（0.5–5.0，共 10 級），滑鼠半星互動 + 即時整體分數預覽 |
| **使用者系統** | 以學號為帳號，未登入無法評價、修改／刪除僅限本人（非本人回傳 403） |
| **課程詳細頁** | 三維度平均分數與所有評價一覽 |
| **評價 CRUD** | 新增、修改（預填原資料）、刪除（確認對話框），overall 自動計算 |

<br/>

## 三、技術架構

採用標準的 Django **MVT（Model–View–Template）** 架構：

```
瀏覽器 ──HTTP──▶ Gunicorn ──▶ Django URL Router ──▶ View
                                                      │
                                        Django ORM ◀──┘
                                             │
                                             ▼
                                        PostgreSQL
                                             │
                     HTML Template ◀── 查詢結果 ──┘ ──▶ 回傳瀏覽器渲染
```

| 類別 | 技術 | 用途 |
|------|------|------|
| 後端框架 | **Django 6.0** | 路由、ORM、使用者認證、商業邏輯 |
| 程式語言 | **Python 3.12** | 主要開發語言 |
| 資料庫 | **PostgreSQL 15** | 關聯式資料庫 |
| 前端 | **Bootstrap 5** | RWD 排版與元件 |
| 靜態檔案 | **WhiteNoise** | 雲端環境靜態檔案服務 |
| DB 連線 | **dj-database-url + psycopg** | 解析 `DATABASE_URL` |
| WSGI 伺服器 | **Gunicorn** | 生產環境 Web 伺服器 |
| 資料解析 | **pdfplumber + pandas** | 解析 PDF / Excel 原始課程資料（見 `scripts/`） |

<br/>

## 四、資料庫設計

四張table：

```
┌─────────────┐        ┌──────────────┐
│   Student   │        │  Professor   │
├─────────────┤        ├──────────────┤
│ student_id  │        │ professor_id │
│ student_name│        │ professor_name
│ major       │        │ department   │
│ year_level  │        └──────┬───────┘
└──────┬──────┘               │ 1
       │ 1                     │
       │            N  ┌───────▼──────┐
       │        ┌──────│    Course    │
       │        │      ├──────────────┤
       │        │      │ course_id(PK)│  ← VARCHAR 科號 (如 11410ECON100201)
       │        │      │ course_name  │
       │        │      │ credits      │
       │        │      │ department   │
       │        │      └──────┬───────┘
       │ 1      │ N           │ 1
       │   ┌────▼─────────────▼───┐
       └──▶│        Review         │
           ├──────────────────────┤
           │ review_id (PK)       │
           │ sweetness_score  0.5–5.0
           │ easiness_score   0.5–5.0
           │ value_score      0.5–5.0
           │ overall_score  ← 三項平均，自動計算
           │ comment_text         │
           │ review_date          │
           └──────────────────────┘
```

**設計決策**

- **`course_id` 用 VARCHAR 而非 INT** — 清大科號本身是字串（`11410ECON100201`），直接作為主鍵，省去額外對照。
- **`overall_score` 自動計算** — 系統設為三項平均，不開放手動輸入，確保評分一致。
- **分數用 `DECIMAL(2,1)`** — 支援 0.5 為單位的半星，提供更細緻的粒度。
- **移除 `Enrollment` 表** — 原設計含選課紀錄表，實作中未使用，移除以保持整潔。

<br/>

## 五、專案結構

```
DBMS-Course-Review-Site/
├── course_review/          # Django 專案設定
│   ├── settings.py         # 設定（DB、靜態檔、安全標頭）
│   ├── urls.py             # 根路由
│   └── wsgi.py             # WSGI 進入點
├── reviews/                # 主應用
│   ├── models.py           # Student / Professor / Course / Review
│   ├── views.py            # 首頁、課程列表/詳細、評價 CRUD、登入註冊
│   ├── forms.py            # 表單驗證
│   ├── urls.py             # 應用路由
│   ├── templates/reviews/  # 9 個 HTML 模板（Bootstrap 5）
│   └── management/commands/# 資料匯入與維護指令
│       ├── import_courses.py    # 匯入課程與教授
│       ├── seed_reviews.py      # 產生測試評價
│       └── fix_overall_scores.py# 批次修正歷史 overall_score
├── scripts/                # 一次性原始資料解析（pdfplumber / pandas）
│   ├── parse_courses.py         # 解析 PDF 課表
│   └── parse_excel_courses.py   # 解析 Excel 課表
├── all_courses.json        # 全校課程資料（import_courses 的來源）
├── Procfile                # release: migrate / web: gunicorn
├── requirements.txt        # Python 相依套件
└── manage.py
```

<br/>

## 六、開發歷程中解決的問題

| 問題 | 解決方式 |
|------|----------|
| PDF 課名跨行截斷 | 修正 pdfplumber 跨行文字合併邏輯 |
| `course_id` 型別（INT → 字串科號） | Model 改用 `CharField` |
| Railway 本機無法連 `railway.internal` DB | 改用 `DATABASE_PUBLIC_URL` |
| 課程列表 N+1 查詢 | Django ORM `annotate + Avg` 一次查詢 |
| `overall_score` 歷史資料錯誤 | 撰寫 `fix_overall_scores` 指令批次修正 |
| 篩選器系所寫死 | 改為從資料庫動態載入並依科號前綴排序 |

<br/>

---

<div align="center">

**作者：郭珍妤** · 國立清華大學 · 2026
<br/>

</div>
