"""
Parse 6 NTHU CTM PDF course schedules and output courses.json.
Usage: python parse_courses.py
"""
import json
import re
import sys

import pdfplumber

PDF_FILES = [
    (r'D:\桌面\NTHU\DBMS_coursefiles\CTM_課程表總錄\ECON-1_課程表總錄.pdf', '114-1'),
    (r'D:\桌面\NTHU\DBMS_coursefiles\CTM_課程表總錄\IPMT-1_課程表總錄.pdf', '114-1'),
    (r'D:\桌面\NTHU\DBMS_coursefiles\CTM_課程表總錄\QF-1_課程表總錄.pdf',   '114-1'),
    (r'D:\桌面\NTHU\DBMS_coursefiles\CTM_課程表總錄\ECON-2_課程表總錄.pdf', '114-2'),
    (r'C:\Users\Kuo chen shu\Downloads\IPMT-2_課程表總錄.pdf',              '114-2'),
    (r'C:\Users\Kuo chen shu\Downloads\QF-2_課程表總錄.pdf',                '114-2'),
]

DEPT_MAP = {
    'ECON': '經濟系',
    'QF':   '計財系',
    'IPMT': '科管院學士班',
    'TM':   '科管院學士班',
    'ISS':  '科管院學士班',
    'IMBA': '科管院學士班',
    'LST':  '科管院學士班',
    'CTM':  '科管院學士班',
}

COURSE_ID_RE = re.compile(r'^\d{5}[A-Z]')
PREFIX_RE    = re.compile(r'^\d{5}([A-Z]+)')

# Any character in the broad CJK ranges (Unified, Ext-A/B, Radicals, Kangxi…)
# Using \u ranges so the source file stays ASCII-safe.
_CJK_PAT = (
    r'⺀-⿕'   # CJK Radicals Supplement + Kangxi Radicals
    r'㐀-鿿'   # CJK Extension A + CJK Unified Ideographs
    r'豈-﫿'   # CJK Compatibility Ideographs
)
HAS_CJK_RE      = re.compile(f'[{_CJK_PAT}]')          # any CJK in string
LEADING_CJK_RE  = re.compile(f'^([{_CJK_PAT}]+)')       # CJK anchored at start


def normalize_course_id(raw: str) -> str:
    """'11410QF 100201' → '11410QF100201'"""
    return re.sub(r'\s+', '', raw)


def get_department(course_id: str) -> str | None:
    m = PREFIX_RE.match(course_id)
    if not m:
        return None
    return DEPT_MAP.get(m.group(1))


def extract_course_name(text: str) -> str | None:
    """
    Collect the course name from a multi-line cell.

    Strategy: iterate lines; any line that contains at least one CJK character
    is part of the name (handles 'ESG與社會創', 'MySQL實務應' etc.).
    Stop as soon as we hit a line with NO CJK after we've already collected
    something (that line is the start of the English translation).
    """
    if not text:
        return None
    parts: list[str] = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if HAS_CJK_RE.search(line):
            parts.append(line)
        elif parts:
            # Hit a pure-ASCII line after collecting CJK lines → stop
            break
        # If no CJK collected yet and this line is ASCII, keep looking
        # (handles cells where the first line is blank or an index number)
    return ''.join(parts) if parts else None


def extract_professor_name(text: str) -> str | None:
    """
    Return the first Chinese name from the teacher cell.
    The format is: '余朝恩\\nYU,\\nCHAO-\\nEN' or '張三\\n李四\\n...'
    We take only the leading CJK characters of the first CJK-containing line.
    """
    if not text:
        return None
    for line in text.split('\n'):
        line = line.strip()
        m = LEADING_CJK_RE.match(line)
        if m:
            return m.group(1)
    return None


def parse_pdf(pdf_path: str, semester: str) -> list[dict]:
    courses = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or not row[0]:
                        continue
                    raw_id = row[0].strip()
                    if not COURSE_ID_RE.match(raw_id):
                        continue

                    course_id  = normalize_course_id(raw_id)
                    department = get_department(course_id)
                    if department is None:
                        continue

                    course_name = extract_course_name(row[1] or '')
                    if not course_name:
                        continue

                    try:
                        credits = int((row[2] or '').strip())
                    except ValueError:
                        continue

                    professor_name = extract_professor_name(row[5] or '') or '未知'

                    courses.append({
                        'course_id':      course_id,
                        'course_name':    course_name,
                        'credits':        credits,
                        'professor_name': professor_name,
                        'department':     department,
                        'semester':       semester,
                    })
    return courses


def main():
    all_courses: dict[str, dict] = {}
    for pdf_path, semester in PDF_FILES:
        print(f'Parsing [{semester}] {pdf_path} ...', flush=True)
        try:
            courses = parse_pdf(pdf_path, semester)
            new = 0
            for c in courses:
                if c['course_id'] not in all_courses:
                    all_courses[c['course_id']] = c
                    new += 1
            print(f'  -> {len(courses)} rows parsed, {new} new unique courses')
        except FileNotFoundError:
            print(f'  [SKIP] File not found')
        except Exception as e:
            print(f'  [ERROR] {e}')

    result = list(all_courses.values())
    print(f'\nTotal unique courses: {len(result)}')

    output_path = r'd:\桌面\NTHU\DBMS_coursefiles\course_review_system\courses.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'Saved -> {output_path}')

    print('\nFirst 5 entries:')
    for c in result[:5]:
        print(f"  {c['course_id']}  {c['course_name']}  {c['credits']}cr"
              f"  {c['professor_name']}  {c['department']}  {c['semester']}")


if __name__ == '__main__':
    if sys.stdout.encoding.lower() in ('cp950', 'cp936', 'mbcs'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
