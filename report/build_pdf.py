"""Build report/REPORT.pdf from REPORT.md, with the architecture diagram on its own last page.

Needs the `markdown` package (build-time only, not used by the app) and Google Chrome:
    uv pip install markdown
    .venv/bin/python report/build_pdf.py
"""

import subprocess
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 15mm 16mm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10.2pt; line-height: 1.38; color: #111; }
h1 { font-size: 15.5pt; margin: 0 0 4px; }
h2 { font-size: 11.8pt; margin: 12px 0 4px; border-bottom: 1px solid #ccc; padding-bottom: 2px; }
p { margin: 4px 0; text-align: justify; }
ul { margin: 3px 0 3px 18px; padding: 0; } li { margin: 1px 0; }
blockquote { margin: 5px 0 5px 10px; padding: 3px 9px; border-left: 3px solid #1565c0; background: #f4f8fd; }
blockquote p { margin: 2px 0; text-align: left; }
code { font-size: 8.8pt; background: #f2f2f2; padding: 0 2px; border-radius: 2px; }
.diagram { page-break-before: always; text-align: center; }
.diagram img { width: 100%; }
.diagram p { text-align: center; font-size: 9.5pt; color: #444; }
"""


def main() -> None:
    body = markdown.markdown((HERE / "REPORT.md").read_text(encoding="utf-8"), extensions=["extra"])
    diagram = (HERE.parent / "docs" / "architecture.png").as_uri()
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{body}
<div class="diagram"><h2>Architecture diagram</h2><img src="{diagram}">
<p>Feedback arc (blue), exits: approved (green), attempts exhausted (amber), technical error (red, dashed).</p></div>
</body></html>"""
    html_path = HERE / "REPORT.html"
    html_path.write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={HERE / 'REPORT.pdf'}", html_path.as_uri()],
                   check=True, capture_output=True)
    html_path.unlink()


if __name__ == "__main__":
    main()
