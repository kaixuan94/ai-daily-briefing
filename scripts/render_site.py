#!/usr/bin/env python3
"""Render briefs/*.md into static HTML and refresh the archive index.

Usage:
    python3 scripts/render_site.py

Requires the Python package `markdown` (pip install markdown).
The generated HTML is what GitHub Pages serves; rerun this after adding a brief.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

try:
    import markdown
    from markdown.extensions.toc import slugify_unicode
except ImportError:
    sys.exit("Missing dependency. Install it with: pip install markdown")

ROOT = Path(__file__).resolve().parents[1]
BRIEFS = ROOT / "briefs"
ASSETS = "assets/style.css"
SITE = "https://kaixuan94.github.io/ai-daily-briefing"
REPO = "https://github.com/kaixuan94/ai-daily-briefing"

URL_RE = re.compile(r"(?<!\()(https?://[^\s<>）)]+)")
TRAIL = ".,;:，。、；：>"
H1_RE = re.compile(r"^#\s+(.+)$", re.M)
WEEKDAY_RE = re.compile(r"（([^）]+)）")
WINDOW_RE = re.compile(r"香港时间\s*([^）]+)")
CODE_SPLIT = re.compile(r"(`[^`]*`)")


def autolink(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        url = raw.rstrip(TRAIL)
        if not url:
            return raw
        return f"[{url}]({url}){raw[len(url):]}"

    parts = CODE_SPLIT.split(text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            out.append(part)
        else:
            out.append(URL_RE.sub(repl, part))
    return "".join(out)


def render_markdown(text: str) -> str:
    return markdown.markdown(
        autolink(text),
        extensions=["tables", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": slugify_unicode}},
        tab_length=2,
        output_format="html",
    )


def externalize_links(body: str) -> str:
    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if "target=" in tag:
            return tag
        return tag[:-1] + ' target="_blank" rel="noopener noreferrer">'

    return re.sub(r'<a href="https?://[^"]*">', repl, body)


def decorate(body: str) -> str:
    body = externalize_links(body)
    # Keep the Chinese colon with its label so it doesn't wrap onto its own line.
    body = body.replace("</strong>：", "：</strong>")
    body = body.replace("<table>", '<div class="table-scroll"><table>').replace(
        "</table>", "</table></div>"
    )
    body = re.sub(
        r"(<h1[^>]*>.*?</h1>\s*)<ul>",
        r'\1<ul class="meta">',
        body,
        count=1,
        flags=re.S,
    )
    body = re.sub(
        r"(<h2[^>]*>目录</h2>\s*)<ol>",
        r'<nav class="toc" aria-label="目录">\1<ol>',
        body,
        count=1,
    )
    body = re.sub(
        r'(<nav class="toc" aria-label="目录">.*?</ol>)',
        r"\1</nav>",
        body,
        count=1,
        flags=re.S,
    )
    return body


def page(
    title: str,
    description: str,
    canonical: str,
    depth: int,
    main: str,
    og_type: str = "article",
) -> str:
    prefix = "../" * depth
    css = prefix + ASSETS
    home = prefix + "index.html"
    desc = html.escape(description, quote=True)
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#f4efe6" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#161310" media="(prefers-color-scheme: dark)">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="{html.escape(og_type, quote=True)}">
  <meta property="og:url" content="{html.escape(canonical, quote=True)}">
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{css}">
</head>
<body>
  <a class="skip" href="#content">跳到正文</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="{home}">
        <span class="brand-mark" aria-hidden="true">简</span>
        <span>
          <span class="brand-name">凯旋</span>
          <span class="brand-sub">AI圈每日简报</span>
        </span>
      </a>
      <nav class="header-nav" aria-label="站点">
        <a href="{home}">目录</a>
      </nav>
    </div>
  </header>
  <main id="content" class="wrap">
{main}
  </main>
  <footer class="site-footer">
    <p>凯旋 · AI圈每日简报</p>
    <p><a href="{REPO}">GitHub 仓库</a></p>
  </footer>
</body>
</html>
"""


def parse_brief(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    h1 = H1_RE.search(text)
    title = h1.group(1).strip() if h1 else path.stem
    weekday = ""
    found = WEEKDAY_RE.search(title)
    if found:
        weekday = found.group(1)
    window = ""
    for line in text.splitlines():
        if "时间窗" in line:
            match = WINDOW_RE.search(line)
            window = match.group(1).strip() if match else ""
            break
    categories = re.findall(r"^\d+\.\s+\[(.+?)\]\(#", text, flags=re.M)
    items = len(re.findall(r"^###\s+", text, flags=re.M))
    return {
        "date": path.stem,
        "title": title,
        "weekday": weekday,
        "window": window,
        "categories": categories,
        "items": items,
        "text": text,
        "path": path,
    }


def brief_main(info: dict, body: str, newer: dict | None, older: dict | None) -> str:
    links = []
    if newer:
        links.append(f'<a href="{html.escape(newer["date"])}.html">较新一天</a>')
    if older:
        links.append(f'<a href="{html.escape(older["date"])}.html">较早一天</a>')
    links.append('<a href="../index.html">返回目录</a>')
    links.append(f'<a href="{html.escape(info["date"])}.md">Markdown 原文</a>')
    nav = "\n        ".join(links)
    return f"""    <article class="brief">
{body}
      <p class="brief-end">
        {nav}
      </p>
    </article>"""


def index_main(briefs: list[dict]) -> str:
    if not briefs:
        listing = '    <p class="empty">还没有简报。把 Markdown 放到 <code>briefs/</code> 后重新生成即可。</p>'
    else:
        cards = []
        for info in briefs:
            pills = "".join(f"<li>{html.escape(name)}</li>" for name in info["categories"])
            window = (
                f'<p>香港时间 {html.escape(info["window"])}</p>' if info["window"] else ""
            )
            weekday = (
                f'<span class="weekday">{html.escape(info["weekday"])}</span>'
                if info["weekday"]
                else ""
            )
            cards.append(
                f"""      <li class="card">
        <a class="card-link" href="briefs/{html.escape(info["date"])}.html">
          <time datetime="{html.escape(info["date"])}">{html.escape(info["date"])}</time>{weekday}
          <span class="card-title">AI圈每日简报</span>
          <p class="card-meta">{info["items"]} 条精选 · {len(info["categories"])} 个分类</p>
          {window}
          <ul class="pills">{pills}</ul>
        </a>
        <p class="card-actions">
          <a href="briefs/{html.escape(info["date"])}.html">阅读全文</a>
          <a href="briefs/{html.escape(info["date"])}.md">Markdown 原文</a>
        </p>
      </li>"""
            )
        listing = '    <ol class="archive">\n' + "\n".join(cards) + "\n    </ol>"
    return f"""    <p class="section-label">每日精选</p>
    <h1>AI圈每日简报</h1>
    <p class="lede">凯旋按日整理的 AI 圈阅读页。每期保留全文 HTML，方便在手机和桌面上直接读；Markdown 原文一并归档。</p>
    <h2 class="section-label">已发布</h2>
{listing}"""


def main() -> None:
    paths = sorted(BRIEFS.glob("*.md"), reverse=True)
    briefs = [parse_brief(path) for path in paths]
    by_date = {info["date"]: info for info in briefs}
    dates = [info["date"] for info in briefs]

    for index, info in enumerate(briefs):
        body = decorate(render_markdown(info["text"]))
        # Indent converted markdown so the article source stays readable.
        indented = "\n".join(
            ("      " + line) if line else "" for line in body.splitlines()
        )
        newer = by_date[dates[index - 1]] if index > 0 else None
        older = by_date[dates[index + 1]] if index + 1 < len(dates) else None
        title = f'{info["title"]} — 凯旋'
        description = (
            f'{info["date"]} AI圈每日简报，{len(info["categories"])} 个分类，'
            f'{info["items"]} 条精选。'
        )
        html_page = page(
            title,
            description,
            f'{SITE}/briefs/{info["date"]}.html',
            depth=1,
            main=brief_main(info, indented, newer, older),
        )
        info["path"].with_suffix(".html").write_text(html_page, encoding="utf-8")
        missing = [
            href
            for href in re.findall(r'href="#([^"]+)"', html_page)
            if f'id="{href}"' not in html_page
        ]
        if missing:
            sys.exit(f'{info["date"]}: broken anchors: {missing}')

    index_html = page(
        "凯旋 · AI圈每日简报",
        "凯旋的 AI圈每日简报。按日归档，手机和桌面都可直接阅读。",
        f"{SITE}/",
        depth=0,
        main=index_main(briefs),
        og_type="website",
    )
    (ROOT / "index.html").write_text(index_html, encoding="utf-8")
    print(f"Rendered {len(briefs)} brief(s) and index.html")


if __name__ == "__main__":
    main()
