"""
Task 2 — Crawl bài viết/thông báo về dịch vụ đại học.

Yêu cầu:
    1. Crawl tối thiểu 5 bài viết từ trang công khai của một trường đại học.
    2. Sử dụng Crawl4AI.
    3. Lưu kết quả vào data/landing/news/.
    4. Mỗi bài được lưu thành một file JSON.

Cài đặt:
    pip install crawl4ai
    playwright install chromium
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "landing" / "news"


ARTICLE_URLS = [
    (
        "https://www.rmit.edu.vn/news/all-news/2026/jun/"
        "rmit-achieves-its-best-result-in-20-years-in-"
        "qs-world-university-rankings"
    ),
    (
        "https://www.rmit.edu.vn/news/all-news/2026/jun/"
        "living-safely-with-ai-the-danger-of-automation-bias"
    ),
    (
        "https://www.rmit.edu.vn/news/all-news/2026/jun/"
        "ai-driven-trade-fraud-raises-alarm-for-"
        "vietnamese-exporters"
    ),
    (
        "https://www.rmit.edu.vn/news/all-news/2026/aug/"
        "the-hidden-psychology-behind-older-consumers-"
        "digital-payment-choices"
    ),
    (
        "https://www.rmit.edu.vn/news/all-news/2026/jul/"
        "rmit-student-finds-global-purpose-at-"
        "un-leadership-program"
    ),
]


def setup_directory():
    """Tạo thư mục lưu dữ liệu nếu chưa tồn tại."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def extract_markdown(markdown_result: Any) -> str:
    """
    Chuẩn hóa kết quả Markdown giữa các phiên bản Crawl4AI.

    Một số phiên bản trả về chuỗi, một số phiên bản trả về
    đối tượng MarkdownGenerationResult.
    """
    if isinstance(markdown_result, str):
        return markdown_result.strip()

    raw_markdown = getattr(
        markdown_result,
        "raw_markdown",
        None,
    )

    if isinstance(raw_markdown, str):
        return raw_markdown.strip()

    fit_markdown = getattr(
        markdown_result,
        "fit_markdown",
        None,
    )

    if isinstance(fit_markdown, str):
        return fit_markdown.strip()

    return str(markdown_result or "").strip()


async def crawl_article(url: str, crawler=None) -> dict:
    """
    Crawl một bài viết.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str,
            "content_markdown": str
        }
    """
    from crawl4ai import AsyncWebCrawler

    if crawler is None:
        async with AsyncWebCrawler() as local_crawler:
            result = await local_crawler.arun(url=url)
    else:
        result = await crawler.arun(url=url)

    if not getattr(result, "success", True):
        error_message = getattr(
            result,
            "error_message",
            "Không rõ nguyên nhân",
        )
        raise RuntimeError(
            f"Không crawl được {url}: {error_message}"
        )

    metadata = getattr(result, "metadata", None) or {}

    title = (
        metadata.get("title")
        or metadata.get("og:title")
        or "Unknown"
    )

    content = extract_markdown(
        getattr(result, "markdown", "")
    )

    if not content:
        raise ValueError(
            f"Không lấy được nội dung từ URL: {url}"
        )

    return {
        "url": url,
        "title": str(title).strip(),
        "date_crawled": datetime.now(
            timezone.utc
        ).isoformat(),
        "content_markdown": content,
    }


async def crawl_all():
    """Crawl toàn bộ bài viết và lưu thành JSON."""
    from crawl4ai import AsyncWebCrawler

    setup_directory()

    success_count = 0
    errors = []

    # Dùng chung một trình duyệt Chromium cho tất cả URL.
    async with AsyncWebCrawler() as crawler:
        for index, url in enumerate(ARTICLE_URLS, start=1):
            print(
                f"[{index}/{len(ARTICLE_URLS)}] "
                f"Crawling: {url}"
            )

            try:
                article = await crawl_article(
                    url,
                    crawler=crawler,
                )

                filename = f"article_{index:02d}.json"
                filepath = DATA_DIR / filename

                filepath.write_text(
                    json.dumps(
                        article,
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                success_count += 1
                print(f"  ✓ Saved: {filepath}")

            except Exception as exc:
                errors.append(
                    {
                        "url": url,
                        "error": str(exc),
                    }
                )
                print(f"  ✗ Lỗi: {exc}")

    print("\n" + "=" * 50)
    print(
        f"Đã crawl thành công "
        f"{success_count}/{len(ARTICLE_URLS)} bài viết."
    )

    if errors:
        print(f"Có {len(errors)} bài bị lỗi:")

        for item in errors:
            print(f"- {item['url']}")
            print(f"  {item['error']}")

    if success_count < 5:
        raise RuntimeError(
            "Task 2 yêu cầu crawl thành công tối thiểu 5 bài."
        )

    print(f"✓ Dữ liệu đã được lưu tại: {DATA_DIR}")


def main():
    """Điểm bắt đầu của chương trình."""
    if len(ARTICLE_URLS) < 5:
        raise ValueError(
            "ARTICLE_URLS phải có tối thiểu 5 URL."
        )

    asyncio.run(crawl_all())


if __name__ == "__main__":
    main()