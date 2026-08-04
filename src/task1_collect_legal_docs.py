"""
Task 1 — Thu thập văn bản chính sách/quy định dịch vụ đại học.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản chính sách (PDF/DOCX) từ trang công khai của một trường đại học.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, mô tả đúng nội dung.

Gợi ý nguồn (ví dụ trang công khai RMIT Vietnam — rmit.edu.vn):
    - https://www.rmit.edu.vn/study-at-rmit/tuition-fees
    - https://www.rmit.edu.vn/study-at-rmit/scholarships/...
    - https://www.rmit.edu.vn/students/my-studies/fees-and-payments

Gợi ý văn bản (chủ đề dịch vụ đại học):
    - Học phí & phương thức thanh toán (Tuition Fees)
    - Chính sách học bổng (Scholarship eligibility)
    - Quy định ký túc xá / hỗ trợ chỗ ở (Accommodation Services)
    - Hướng dẫn đăng ký học phần qua cổng thông tin sinh viên (Course Registration)

Lưu ý: một số trang trường (vd VinUni, Fulbright) chặn bot crawler mặc định (HTTP 403) —
không phải lỗi của bạn, đó là cấu hình WAF/Cloudflare phía server. Đổi sang trang khác
thay vì cố vượt qua, và chỉ dùng nguồn công khai/được phép chia sẻ.
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")


import requests

# Direct PDF links xac nhan tu trang cong khai RMIT Vietnam (rmit.edu.vn).
DOCS = [
    (
        "https://www.rmit.edu.vn/assets/vn/en/assets-for-production/documents/pdfs/"
        "study-at-rmit/tuition-fees/student-fees-and-charges-guide-06-2026.pdf",
        "tuition-fees-rmit.pdf",
    ),
    (
        "https://www.rmit.edu.vn/content/dam/rmit/vn/en/assets-for-production/documents/pdfs/"
        "study-at-rmit/scholarships/english-pdf/"
        "rmit-university-vietnam-scholarship-terms-and-conditions.pdf",
        "academic-achievement-scholarship-rmit.pdf",
    ),
    (
        "https://www.rmit.edu.vn/assets/vn/en/assets-for-production/documents/pdfs/"
        "academic-calendar/academic-calendar-2026-jun26.pdf",
        "academic-calendar-rmit.pdf",
    ),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RAGLabBot/1.0)"}


def download_file(url: str, filename: str):
    """Tai 1 file ve DATA_DIR, bo qua neu da ton tai."""
    filepath = DATA_DIR / filename
    if filepath.exists() and filepath.stat().st_size > 0:
        print(f"= Da co san: {filepath}")
        return

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    filepath.write_bytes(response.content)
    print(f"OK Da tai: {filepath} ({len(response.content)} bytes)")


def collect_all():
    setup_directory()
    for url, filename in DOCS:
        download_file(url, filename)


if __name__ == "__main__":
    collect_all()
