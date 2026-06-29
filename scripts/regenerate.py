#!/usr/bin/env python3
"""Regenerate PDFs from every HTML card in reference-cards/ using Playwright Chromium.

Each reference-cards/<name>.html is rendered to reference-cards/<name>.pdf.

Usage:
    pip install -r requirements.txt
    python -m playwright install chromium
    python scripts/regenerate.py
"""
import pathlib
import sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
CARDS = ROOT / "reference-cards"


def main() -> int:
    htmls = sorted(CARDS.glob("*.html"))
    if not htmls:
        print(f"no HTML cards found in {CARDS}", file=sys.stderr)
        return 1
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for html in htmls:
            pdf = html.with_suffix(".pdf")
            page.goto(html.as_uri())
            page.wait_for_timeout(700)  # let embedded fonts settle
            page.pdf(
                path=str(pdf),
                format="Letter",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            print(f"wrote {pdf.relative_to(ROOT)}")
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
