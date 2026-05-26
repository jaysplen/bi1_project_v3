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
| W1 | PM baskets analysed | {w1.get('pm_cases', '—')} |
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
    if not shutil.which("soffice"):
        print("  [warn] LibreOffice (`soffice`) not found")
        return False

    body = md_path.read_text(encoding="utf-8")
    html_body = md_lib.markdown(
        body,
        extensions=["tables", "fenced_code", "toc", "nl2br"],
    )
    html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
body {{ font-family: "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11pt;
       line-height: 1.45; margin: 2cm; color: #1a1a1a; }}
h1 {{ font-size: 22pt; color: #1B2A4A; border-bottom: 2px solid #2E5FA1; padding-bottom: 6px; }}
h2 {{ font-size: 16pt; color: #1B2A4A; margin-top: 1.2em; }}
h3 {{ font-size: 13pt; color: #2E5FA1; }}
table {{ border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 10pt; }}
th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }}
th {{ background: #f1f5f9; }}
code {{ background: #f1f5f9; padding: 1px 4px; font-size: 9.5pt; }}
pre {{ background: #f8fafc; padding: 10px; border: 1px solid #e2e8f0; font-size: 9pt; }}
img {{ max-width: 100%; height: auto; }}
</style>
</head><body>
{html_body}
</body></html>"""
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    try:
        subprocess.run(
            [
                "soffice", "--headless",
                "--convert-to", "pdf",
                "--outdir", str(pdf_path.parent),
                str(OUT_HTML),
            ],
            check=True,
            capture_output=True,
            cwd=ROOT,
        )
        produced = pdf_path.parent / (OUT_HTML.stem + ".pdf")
        if produced.is_file() and produced != pdf_path:
            produced.replace(pdf_path)
        return pdf_path.is_file()
    except subprocess.CalledProcessError as exc:
        print(f"  [warn] LibreOffice conversion failed: {exc}")
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
