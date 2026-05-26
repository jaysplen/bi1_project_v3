#!/usr/bin/env python3
"""
Build PROJECT_HANDBOOK.pdf from PROJECT_HANDBOOK.md.

Steps:
  1. Inject live KPIs at <!-- METRICS --> from exports/metrics_summary.json.
  2. Convert markdown -> HTML -> PDF via LibreOffice (soffice headless).

Run from the repository root:

    python3 build_handbook.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_METRICS = ROOT / "exports" / "metrics_summary.json"
SOURCE_MD = ROOT / "PROJECT_HANDBOOK.md"
OUT_MD = ROOT / "PROJECT_HANDBOOK.generated.md"
OUT_HTML = ROOT / "PROJECT_HANDBOOK.generated.html"
OUT_PDF = ROOT / "PROJECT_HANDBOOK.pdf"

METRICS_MARKER = "<!-- METRICS -->"


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        print(f"  [warn] {path} not found")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _metrics_block(base: dict) -> str:
    w1 = base.get("w1", {})
    w2 = base.get("w2", {})
    w3 = base.get("w3", {})
    return f"""
### Live pipeline metrics

*Source: `exports/metrics_summary.json`*

| Work package | Metric | Value |
|--------------|--------|-------|
| W1 | Repairs analyzed | {w1.get('pm_cases', '—')} |
| W1 | Association rules | {w1.get('rules_count', '—')} |
| W1 | Top rule lift | {w1.get('top_lift', 0):.2f} |
| W1 | Pareto SKUs for 80% / 90% coverage | {w1.get('pareto_cov80_parts', '—')} / {w1.get('pareto_cov90_parts', '—')} |
| W2 | Algorithm | {w2.get('method', '—')} |
| W2 | Test R² | {w2.get('r2', 0):.4f} |
| W2 | Test MAE (days) | {w2.get('mae', 0):.4f} |
| W3 | Algorithm | {w3.get('method', '—')} |
| W3 | Operating threshold | {w3.get('threshold', '—')} |
| W3 | Recall (failure) | {w3.get('recall_failure', 0):.1%} |
| W3 | Precision (failure) | {w3.get('precision_failure', 0):.1%} |
| W3 | Accuracy | {w3.get('accuracy', 0):.1%} |
""".strip()


def inject(text: str, marker: str, block: str) -> str:
    if marker in text:
        return text.replace(marker, block, 1)
    return text


def build_pdf(md_path: Path, pdf_path: Path) -> bool:
    try:
        import markdown as md_lib
    except ImportError:
        print("  [warn] `markdown` not installed (pip install markdown)")
        return False
    
    # Check if chromium is available
    chromium_path = "/snap/bin/chromium"
    if not Path(chromium_path).is_file():
        print(f"  [warn] Chromium not found at {chromium_path}")
        return False

    body = md_path.read_text(encoding="utf-8")
    
    # Strip the title heading # from the body if we are rendering it on the cover page
    if body.startswith("# "):
        # Remove first line
        body_lines = body.split("\n")
        body = "\n".join(body_lines[1:])
        
    html_body = md_lib.markdown(
        body,
        extensions=["tables", "fenced_code", "toc", "nl2br"],
    )
    
    cover_page_html = """
<div class="cover-page">
    <div class="cover-header">
        <div class="cover-eyebrow">VacuTech Solutions &middot; Analytical Case Study</div>
        <h1 class="cover-title">Business Intelligence &<br>Data Mining Handbook</h1>
        <h2 class="cover-subtitle">Data-Driven Process Optimization for Operations & CRM</h2>
    </div>
    <div class="cover-footer">
        <div class="cover-meta">
            <h4>B.Sc. Business Intelligence</h4>
            <p>DLMDSEBA02 &mdash; First Semester Module Guide</p>
        </div>
        <div class="cover-meta" style="text-align: right;">
            <h4>Author</h4>
            <p>Lead BI Architect</p>
        </div>
    </div>
</div>
"""

    html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

@page {{
    size: A4;
    margin: 2.5cm 2cm;
}}

@page :first {{
    margin: 0;
}}

body {{
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1e293b;
    background: #ffffff;
    margin: 0;
    padding: 0;
}}

/* Cover page styling */
.cover-page {{
    page-break-after: always;
    height: 297mm; /* Exact A4 height to prevent print bleed overflow */
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 6cm 3cm 3cm 3cm;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #f8fafc;
}}

.cover-header {{
    border-left: 4px solid #3b82f6;
    padding-left: 24px;
}}

.cover-eyebrow {{
    font-size: 11pt;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #94a3b8;
    font-weight: 600;
    margin-bottom: 12px;
}}

.cover-page h1.cover-title {{
    font-size: 30pt;
    line-height: 1.2;
    font-weight: 700;
    color: #ffffff;
    border-bottom: none;
    padding-bottom: 0;
    margin: 0 0 16px 0;
}}

.cover-page h2.cover-subtitle {{
    font-size: 14pt;
    font-weight: 400;
    color: #cbd5e1;
    border-bottom: none;
    padding-bottom: 0;
    margin: 0;
    page-break-before: auto;
}}

.cover-footer {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-top: 1px solid #334155;
    padding-top: 24px;
    font-size: 9.5pt;
    color: #94a3b8;
}}

.cover-meta h4 {{
    margin: 0 0 4px 0;
    color: #f8fafc;
    font-weight: 600;
}}

.cover-meta p {{
    margin: 0;
}}

/* Main body wrapper to apply standard print margins */
.content-wrapper {{
    padding: 0;
}}

/* Headings */
h1 {{
    font-size: 22pt;
    font-weight: 700;
    color: #0f172a;
    margin-top: 0;
    margin-bottom: 20px;
    border-bottom: 2px solid #cbd5e1;
    padding-bottom: 8px;
}}

h2 {{
    page-break-before: always;
    font-size: 16pt;
    font-weight: 700;
    color: #0f172a;
    margin-top: 1.5em;
    margin-bottom: 14px;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 6px;
}}

h3 {{
    font-size: 12pt;
    font-weight: 600;
    color: #2563eb;
    margin-top: 1.2em;
    margin-bottom: 8px;
}}

p {{
    margin-top: 0;
    margin-bottom: 1em;
}}

/* Tables */
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1.5em 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}}

th, td {{
    border-bottom: 1px solid #e2e8f0;
    padding: 8px 10px;
    text-align: left;
}}

th {{
    background: #f8fafc;
    font-weight: 600;
    color: #0f172a;
    border-top: 1px solid #e2e8f0;
    border-bottom: 2px solid #cbd5e1;
}}

/* Code */
code {{
    background: #f1f5f9;
    padding: 2px 5px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9pt;
    color: #0f172a;
}}

pre {{
    background: #0f172a;
    color: #f8fafc;
    padding: 14px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9pt;
    overflow-x: auto;
    line-height: 1.45;
    margin: 1.5em 0;
    page-break-inside: avoid;
}}

pre code {{
    background: transparent;
    padding: 0;
    color: inherit;
    font-size: inherit;
}}

/* Blockquotes (Alerts) */
blockquote {{
    background: #f0f9ff;
    border-left: 4px solid #0284c7;
    color: #0369a1;
    padding: 12px 16px;
    margin: 1.5em 0;
    border-radius: 0 6px 6px 0;
}}

blockquote p {{
    margin: 0;
}}

/* Lists */
ul, ol {{
    margin-top: 0;
    margin-bottom: 1em;
    padding-left: 20px;
}}

li {{
    margin-bottom: 4px;
}}

/* Visual Assets (Centering images, adding clean dropshadows) */
img {{
    display: block;
    max-width: 80%;
    max-height: 8.5cm;
    margin: 1.5em auto;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    border: 1px solid #e2e8f0;
    page-break-inside: avoid;
}}
</style>
</head><body>
{cover_page_html}
<div class="content-wrapper">
{html_body}
</div>
</body></html>"""
    
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    try:
        subprocess.run(
            [
                chromium_path, "--headless",
                "--disable-gpu",
                "--print-to-pdf=" + str(pdf_path),
                "--no-sandbox",
                str(OUT_HTML),
            ],
            check=True,
            capture_output=True,
            cwd=ROOT,
        )
        return pdf_path.is_file()
    except subprocess.CalledProcessError as exc:
        print(f"  [warn] Chromium PDF generation failed: {exc.stderr.decode(errors='ignore')}")
        return False


def main() -> int:
    if not SOURCE_MD.is_file():
        print(f"ERROR: missing {SOURCE_MD}", file=sys.stderr)
        return 1

    text = SOURCE_MD.read_text(encoding="utf-8")
    base = _load_json(BASE_METRICS)

    if base is None:
        print(
            "ERROR: run `python3 bi_pipeline.py` first to create metrics_summary.json.",
            file=sys.stderr,
        )
        return 1

    text = inject(text, METRICS_MARKER, _metrics_block(base))
    OUT_MD.write_text(text, encoding="utf-8")
    print(f"  Wrote {OUT_MD.name}")

    if build_pdf(OUT_MD, OUT_PDF):
        print(f"  PDF: {OUT_PDF.name}")
        return 0

    print(
        "ERROR: PDF build failed. Install `markdown` and LibreOffice (`soffice`).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
