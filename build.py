#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「认知增量」静态博客生成器（零依赖，仅标准库）。

用法:  python build.py            # content/*.md → docs/
约定:  content/*.md 使用 front-matter（slug/title/date/series/order/tags/summary）；
       正文子集：#/##/### 标题、段落、**加粗**、`代码`、[链接](url)、
       > 引用、- / 1. 列表、--- 分隔线。
部署:  docs/ 整目录即站点（GitHub Pages: main 分支 /docs；服务器: /var/www/blog/aiblog/）。
"""
import datetime
import html
import json
import os
import re
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "docs")
GALLERY = os.path.join(ROOT, "gallery")   # 独立站点：摄影相册，部署到 /photos/

# ── 站点配置（改名/改签名只动这里）──────────────────────────────
SITE = {
    "name": "认知增量",
    "tagline": "不复述新闻，只更新认知。",
    "author": "Season",
    "description": "AI 行业的深度解读与认知更新：钱、墙、人与安全。与微信公众号同步更新。",
    "url": "https://softslow.cloud/technews",
}
# ────────────────────────────────────────────────────────────────

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
           "viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='18' "
           "fill='%23111'/%3E%3Ctext x='50' y='72' font-size='62' text-anchor='middle' "
           "fill='%23fff' font-family='serif'%3E%E7%9F%A5%3C/text%3E%3C/svg%3E")

CSS = """
:root{--bg:#faf9f6;--ink:#1a1a18;--sub:#6b6a66;--line:#e4e1da;--card:#ffffff;
--accent:#b32d2d;--accent-ink:#8f1f1f;--kicker:#8f1f1f;--code-bg:#f0eee8;--quote-bg:#f4f2ec}
@media (prefers-color-scheme:dark){:root{--bg:#141412;--ink:#e8e6e1;--sub:#9a988f;
--line:#2c2b27;--card:#1c1c19;--accent:#e05a4e;--accent-ink:#e8837a;--kicker:#e8837a;
--code-bg:#23231f;--quote-bg:#1f1e1a}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.95 "Source Han Serif SC","Noto Serif SC","Songti SC",STSong,SimSun,Georgia,serif}
a{color:inherit}
.wrap{max-width:46rem;margin:0 auto;padding:0 1.25rem}
header.site{border-bottom:1px solid var(--line);background:var(--card)}
.site-in{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;
gap:.4rem;padding:1.4rem 1.25rem 1.1rem}
.brand{font-size:1.45rem;font-weight:700;letter-spacing:.06em;text-decoration:none}
.brand .dot{color:var(--accent)}
.tagline{color:var(--sub);font-size:.9rem;letter-spacing:.05em}
nav.top{font-family:system-ui,sans-serif;font-size:.88rem}
nav.top a{color:var(--sub);text-decoration:none;margin-left:1.1rem}
nav.top a:hover{color:var(--accent)}
.about{margin:1.6rem 0 0;padding:1.15rem 1.3rem;background:var(--card);
border:1px solid var(--line);border-radius:10px;font-size:.95rem}
.about b{letter-spacing:.03em}
.about .cols{color:var(--sub);margin-top:.45rem}
.about .cols span{margin-right:1.1em;white-space:nowrap}
.about .cols i{font-style:normal;color:var(--accent);font-family:system-ui,sans-serif;
font-size:.78rem;border:1px solid var(--line);border-radius:4px;padding:.05em .45em;margin-right:.35em}
.list{margin:1.4rem 0 3rem}
a.card{display:block;text-decoration:none;padding:1.35rem .2rem 1.45rem;
border-bottom:1px solid var(--line)}
a.card:hover h2{color:var(--accent-ink)}
.meta{font-family:system-ui,sans-serif;font-size:.8rem;color:var(--sub);
display:flex;align-items:center;gap:.7em;margin-bottom:.45rem;letter-spacing:.04em}
.badge{color:var(--kicker);border:1px solid var(--line);border-radius:4px;
padding:.05em .5em;background:var(--quote-bg);white-space:nowrap}
a.card h2{margin:.1rem 0 .4rem;font-size:1.32rem;line-height:1.5;transition:color .15s}
.sum{color:var(--sub);font-size:.95rem;margin:0}
.more{font-family:system-ui,sans-serif;font-size:.82rem;color:var(--accent);
margin-top:.55rem;letter-spacing:.08em}
footer.site{border-top:1px solid var(--line);color:var(--sub);
font-family:system-ui,sans-serif;font-size:.8rem;line-height:1.9;padding:1.3rem 0 2.4rem}
footer.site a{color:var(--sub)}
article{padding:2.2rem 0 1rem}
.kicker{font-family:system-ui,sans-serif;font-size:.8rem;letter-spacing:.12em;
color:var(--kicker);margin-bottom:.6rem}
h1.title{font-size:1.78rem;line-height:1.55;margin:0 0 .7rem;font-weight:700}
p.lede{font-size:1.06rem;color:var(--sub)}
.byline{font-family:system-ui,sans-serif;font-size:.82rem;color:var(--sub);
padding:.75rem 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);
margin-bottom:1.9rem;letter-spacing:.04em}
.body h2{font-size:1.3rem;line-height:1.5;margin:2.5em 0 1em;padding-left:.6em;
border-left:4px solid var(--accent)}
.body h3{font-size:1.1rem;margin:2em 0 .8em}
.body p{margin:0 0 1.35em;text-align:justify}
.body ul,.body ol{margin:0 0 1.35em;padding-left:1.6em}
.body li{margin-bottom:.5em}
.body blockquote{margin:1.6em 0;padding:.9em 1.2em;background:var(--quote-bg);
border-left:4px solid var(--accent);border-radius:0 8px 8px 0;color:var(--sub)}
.body blockquote p{margin:0}
.body hr{border:none;border-top:1px solid var(--line);margin:2.4em 0}
.body code{font-family:ui-monospace,Consolas,monospace;font-size:.85em;
background:var(--code-bg);padding:.15em .45em;border-radius:4px}
.body strong{font-weight:700}
.body img{display:block;max-width:100%;height:auto;border-radius:8px;margin:1.6em auto;
border:1px solid var(--line)}
p.colophon{color:var(--sub);font-size:.86rem;font-family:system-ui,sans-serif;
line-height:1.8;border-top:1px dashed var(--line);padding-top:1.1em;margin-top:2.2em}
.series-nav{display:flex;gap:.8rem;margin:2.6rem 0 0;font-family:system-ui,sans-serif}
.series-nav a{flex:1;text-decoration:none;border:1px solid var(--line);border-radius:10px;
padding:.8rem 1rem;background:var(--card);font-size:.86rem}
.series-nav a:hover{border-color:var(--accent)}
.series-nav .dir{color:var(--sub);font-size:.75rem;display:block;margin-bottom:.25rem}
.series-nav .next{text-align:right}
.backline{margin:2.4rem 0 3.5rem;font-family:system-ui,sans-serif;font-size:.85rem}
.backline a{color:var(--sub);text-decoration:none}
.backline a:hover{color:var(--accent)}
@media (max-width:640px){h1.title{font-size:1.45rem}a.card h2{font-size:1.18rem}}
.share{display:flex;flex-wrap:wrap;align-items:center;gap:.6rem;margin:2.4rem 0 0;
font-family:system-ui,sans-serif;padding:1.1rem 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.share .s-label{font-size:.82rem;color:var(--sub);letter-spacing:.1em}
.share a.s-btn,.share button.s-btn,.share summary.s-btn{font-size:.82rem;color:var(--ink);text-decoration:none;
border:1px solid var(--line);border-radius:6px;padding:.35em .9em;background:var(--card);cursor:pointer;
list-style:none;display:inline-block;font-family:inherit;line-height:inherit}
.share a.s-btn:hover,.share button.s-btn:hover,.share summary.s-btn:hover{border-color:var(--accent);color:var(--accent-ink)}
.share button.s-btn[hidden]{display:none}
.share summary.s-btn::-webkit-details-marker{display:none}
.share details.s-qr{display:inline-block;position:relative}
.share details[open] summary.s-btn{border-color:var(--accent);color:var(--accent-ink)}
.qrbox{position:absolute;z-index:9;top:calc(100% + .7rem);left:0;background:var(--card);
border:1px solid var(--line);border-radius:10px;padding:.9rem .9rem .5rem;box-shadow:0 8px 28px rgba(0,0,0,.18)}
.qrbox svg{display:block;width:136px;height:136px;background:#fff;border-radius:6px}
.qrbox .qr-tip{font-size:.72rem;color:var(--sub);text-align:center;margin-top:.45rem;white-space:nowrap}
.copydone{color:var(--green,#2e7d4f)!important;border-color:var(--green,#2e7d4f)!important}
""".strip()


def parse_fm(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    meta, body = {}, m.group(2).strip() if m else text
    if m:
        for line in m.group(1).split("\n"):
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            v = v.strip()
            if v.startswith("[") :
                meta[k.strip()] = [x.strip().strip('"\'') for x in v[1:-1].split(",") if x.strip()]
            elif v == "":
                meta[k.strip()] = None
            elif v.isdigit():
                meta[k.strip()] = int(v)
            else:
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":  # 成对剥离包裹引号
                    v = v[1:-1]
                meta[k.strip()] = v
    return meta, body


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
               lambda m: '<img src="' + html.escape(m.group(2), quote=True)
                         + '" alt="' + m.group(1) + '" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a href="{html.escape(m.group(2), quote=True)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md_to_html(md):
    out, lines = [], md.split("\n")
    i, lede_next = 0, False
    para_cls = ' class="lede"'
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("### "):
            out.append(f"<h3>{inline(ln[4:])}</h3>")
        elif ln.startswith("## "):
            out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("# "):
            out.append(f"<h2>{inline(ln[2:])}</h2>")
        elif re.fullmatch(r"-{3,}|\*{3,}", ln.strip()):
            out.append("<hr>")
        elif ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            inner = "".join(f"<p>{inline(b)}</p>" for b in buf if b)
            out.append(f"<blockquote>{inner}</blockquote>")
            continue
        elif re.match(r"[-*]\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"[-*]\s+", lines[i]):
                item = inline(re.sub(r"[-*]\s+", "", lines[i], count=1))
                buf.append("<li>" + item + "</li>")
                i += 1
            out.append("<ul>" + "".join(buf) + "</ul>")
            continue
        elif re.match(r"\d+\.\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"\d+\.\s+", lines[i]):
                item = inline(re.sub(r"\d+\.\s+", "", lines[i], count=1))
                buf.append("<li>" + item + "</li>")
                i += 1
            out.append("<ol>" + "".join(buf) + "</ol>")
            continue
        elif ln.strip() == "**导语**":
            lede_next = True
        else:
            if ln.startswith("说明："):
                out.append(f'<p class="colophon">{inline(ln)}</p>')
            else:
                out.append(f"<p{para_cls}>{inline(ln)}</p>")
                para_cls, lede_next = "", False
        i += 1
    return "\n".join(out)


def load_posts():
    posts = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md"):
            continue
        meta, body = parse_fm(open(os.path.join(CONTENT, fn), encoding="utf-8").read())
        meta["body"] = body
        meta["html"] = md_to_html(body)
        posts.append(meta)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def read_time(body):
    return max(1, round(len(re.sub(r"\s", "", body)) / 420))


def esc(s):
    return html.escape(str(s), quote=True)


def page(title, desc, body, rel="", jsonld=""):
    d = f'<meta name="description" content="{esc(desc)}">' if desc else ""
    oga = f'{SITE["url"]}/{rel}' if rel else SITE["url"]
    full = title if SITE["name"] in title else f"{title} · {SITE['name']}"
    prefix = "../" if rel.startswith(("posts/", "drafts/", "photos/")) else ""
    j = f'<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full)}</title>
{d}
<link rel="canonical" href="{esc(oga)}">
<meta property="og:image" content="{esc(SITE["url"])}/assets/cover.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{FAVICON}">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE["name"])}" href="{prefix}rss.xml">
{j}
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def header(prefix="", active="home"):
    return f"""<header class="site"><div class="site-in wrap" style="padding-left:0;padding-right:0">
<a class="brand" href="{prefix}index.html">{SITE["name"]}<span class="dot">.</span></a>
<span class="tagline">{esc(SITE["tagline"])}</span>
<nav class="top"><a href="{prefix}index.html#about">关于</a><a href="{prefix}data/compute-finance.html">数据</a><a href="{prefix}rss.xml">RSS</a></nav>
</div></header>"""


def footer(prefix=""):
    y = datetime.date.today().year
    return f"""<footer class="site"><div class="wrap">
© {y} {esc(SITE["author"])} · {esc(SITE["name"])} · 与微信公众号同步更新<br>
全部内容为个人观点，不构成投资建议 · <a href="{prefix}rss.xml">RSS 订阅</a>
</div></footer>"""


def build_index(posts):
    cards = []
    for p in posts:
        badge = f'<span class="badge">{esc(p["series"])}{" · " + str(p["order"]) if p.get("order") else ""}</span>' if p.get("series") else ""
        cards.append(f"""<a class="card" href="posts/{p['slug']}.html">
<div class="meta">{badge}<span>{p["date"]}</span><span>约 {read_time(p["body"])} 分钟</span></div>
<h2>{esc(p["title"])}</h2>
<p class="sum">{esc(p["summary"])}</p>
<div class="more">阅读全文 →</div>
</a>""")
    about = f"""<section class="about" id="about">
<b>{esc(SITE["name"])}</b> — {esc(SITE["description"])}<br>
这里只做一件事：把每周 AI 圈的噪音，蒸馏成值得留下的判断。
<div class="cols"><span><i>深度</i>带观点的深度解读</span><span><i>速写</i>安全事件复盘</span><span><i>周报</i>每周五 · 六个认知</span></div>
</section>"""
    body = header() + f'<main class="wrap">{about}<section class="list">{"".join(cards)}</section></main>' + footer()
    web = json.dumps({
        "@context": "https://schema.org", "@type": "WebSite",
        "name": SITE["name"], "description": SITE["description"],
        "url": SITE["url"], "author": {"@type": "Person", "name": SITE["author"]},
        "inLanguage": "zh-CN",
    }, ensure_ascii=False)
    return page(SITE["name"] + "｜" + SITE["tagline"], SITE["description"], body, jsonld=web)


def build_post(p, posts, draft=False):
    banner = ""
    if draft:
        banner = ('<div style="font-family:system-ui,sans-serif;font-size:.85rem;'
                  'background:#fff3cd;color:#664d03;border:1px solid #ffe08a;'
                  'border-radius:8px;padding:.6rem 1rem;margin-top:1.2rem">'
                  "🚧 草稿预览（AI 夜间生成，未经人工核实）——确认后才会发布</div>")
    kicker = f'<div class="kicker">{esc(p["series"])}{" · 第 " + str(p["order"]) + " 篇" if p.get("order") else ""}</div>' if p.get("series") else ""
    sibs = sorted([q for q in posts if q.get("series") == p.get("series") and q.get("order")
                   and p.get("order")], key=lambda q: q["order"]) if p.get("series") else []
    prev_n = next_n = ""
    if sibs and p.get("order"):
        idx = next((i for i, q in enumerate(sibs) if q["slug"] == p["slug"]), None)
        if idx is not None:
            if idx > 0:
                q = sibs[idx - 1]
                prev_n = f'<a href="{q["slug"]}.html"><span class="dir">← 系列上一篇</span>{esc(q["title"])}</a>'
            if idx < len(sibs) - 1:
                q = sibs[idx + 1]
                next_n = f'<a class="next" href="{q["slug"]}.html"><span class="dir">系列下一篇 →</span>{esc(q["title"])}</a>'
    series_nav = f'<div class="series-nav">{prev_n}{next_n}</div>' if (prev_n or next_n) else ""
    enc_url = urllib.parse.quote(f'{SITE["url"]}/posts/{p["slug"]}.html', safe="")
    enc_t = urllib.parse.quote(p["title"], safe="")
    share = f"""<div class="share">
<span class="s-label">分享</span>
<button type="button" class="s-btn copybtn" onclick="copyLink(this)">复制链接</button>
<button type="button" class="s-btn sharebtn" onclick="sysShare(this)" hidden>系统分享</button>
<details class="s-qr"><summary class="s-btn">微信扫码</summary>
<div class="qrbox"><div data-qr></div><div class="qr-tip">微信扫一扫，手机上阅读</div></div>
</details>
<a class="s-btn" target="_blank" rel="noopener" href="https://service.weibo.com/share/share.php?url={enc_url}&amp;title={enc_t}">微博</a>
<a class="s-btn" target="_blank" rel="noopener" href="https://x.com/intent/post?url={enc_url}&amp;text={enc_t}">X</a>
</div>
<script src="../assets/qrcode.min.js"></script>
<script>
function copyLink(btn){{
  var t = location.href;
  var done = function(){{ if(btn){{ var o = btn.textContent; btn.textContent = '已复制 ✓';
    btn.classList.add('copydone'); setTimeout(function(){{ btn.textContent = o;
    btn.classList.remove('copydone'); }}, 1600); }} }};
  if (navigator.clipboard) {{ navigator.clipboard.writeText(t).then(done, function(){{ prompt('复制链接：', t); }}); }}
  else {{ prompt('复制链接：', t); }}
}}
function sysShare(btn){{
  if (!navigator.share) return;
  navigator.share({{ title: document.title, url: location.href }}).catch(function(){{}});
}}
document.addEventListener('DOMContentLoaded', function(){{
  var sb = document.querySelector('.share .sharebtn');
  if (sb && navigator.share) sb.hidden = false;   // 仅移动端/支持时显示
}});
document.querySelectorAll('details.s-qr').forEach(function(d){{
  d.addEventListener('toggle', function(){{ var box = d.querySelector('[data-qr]');
    if (d.open && box && !box.dataset.done) {{ box.dataset.done = '1';
      try {{ var q = qrcode(0, 'M'); q.addData(location.href); q.make();
        box.innerHTML = q.createSvgTag({{cellSize: 4, margin: 0}}); }}
      catch(e) {{ box.textContent = '生成失败，请直接复制链接'; }} }} }});
}});
</script>"""
    tags = " · ".join(p.get("tags") or [])
    body = header("../", "post") + f"""<main class="wrap"><article>
{banner}
{kicker}
<h1 class="title">{esc(p["title"])}</h1>
<div class="byline">{p["date"]} · {esc(SITE["author"])} · 约 {read_time(p["body"])} 分钟{(" · " + tags) if tags else ""}</div>
<div class="body">
{p["html"]}
</div>
{share}
{series_nav}
<div class="backline"><a href="../index.html">← 返回目录</a></div>
</article></main>""" + footer("../")
    art = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": p["title"], "description": p["summary"],
        "datePublished": p["date"], "dateModified": p["date"],
        "author": {"@type": "Person", "name": SITE["author"]},
        "publisher": {"@type": "Organization", "name": SITE["name"]},
        "mainEntityOfPage": f'{SITE["url"]}/posts/{p["slug"]}.html',
        "inLanguage": "zh-CN",
    }, ensure_ascii=False)
    return page(p["title"], p["summary"], body, f"posts/{p['slug']}.html", jsonld=art)


def build_rss(posts):
    items = []
    for p in posts:
        items.append(f"""<item>
<title>{esc(p["title"])}</title>
<link>{SITE["url"]}/posts/{p["slug"]}.html</link>
<guid isPermaLink="true">{SITE["url"]}/posts/{p["slug"]}.html</guid>
<pubDate>{datetime.datetime.strptime(p["date"], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>
<description>{esc(p["summary"])}</description>
<content:encoded>{esc("<div>" + SITE["tagline"] + "</div>" + p["html"])}</content:encoded>
</item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
<title>{esc(SITE["name"])}</title>
<link>{SITE["url"]}</link>
<description>{esc(SITE["description"])}</description>
<language>zh-CN</language>
<lastBuildDate>{datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>
{''.join(items)}
</channel>
</rss>"""


PHOTO_CSS = """
.gallery{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:1.6rem 0 2rem}
@media(max-width:640px){.gallery{grid-template-columns:repeat(2,1fr)}}
.gallery figure{margin:0;position:relative;overflow:hidden;border-radius:10px;
background:var(--code-bg);cursor:zoom-in;aspect-ratio:4/3}
.gallery img{width:100%;height:100%;object-fit:cover;display:block;
transition:transform .35s ease,filter .35s ease}
.gallery figure:hover img{transform:scale(1.04)}
.gallery figcaption{position:absolute;left:0;right:0;bottom:0;padding:1.6rem .7rem .6rem;
font-family:system-ui,sans-serif;font-size:.72rem;color:#fff;
background:linear-gradient(transparent,rgba(0,0,0,.72));opacity:0;transition:opacity .25s}
.gallery figure:hover figcaption{opacity:1}
.credit{border:1px solid var(--line);background:var(--card);border-radius:12px;
padding:1.1rem 1.25rem;margin:1.4rem 0;font-size:.92rem;color:var(--sub)}
.credit b{color:var(--ink)}
#lb{position:fixed;inset:0;background:rgba(8,8,7,.94);display:none;z-index:99;
align-items:center;justify-content:center;flex-direction:column;padding:1.5rem}
#lb.on{display:flex}
#lb img{max-width:96vw;max-height:82vh;object-fit:contain;border-radius:6px}
#lb .cap{color:#ddd;font-family:system-ui,sans-serif;font-size:.82rem;margin-top:.9rem;text-align:center}
#lb .cap em{color:#9a988f;font-style:normal;display:block;margin-top:.25rem;font-size:.75rem}
#lb .x{position:absolute;top:1rem;right:1.3rem;color:#ddd;font-size:1.6rem;cursor:pointer;
line-height:1;font-family:system-ui,sans-serif}
#lb .nav{position:absolute;top:50%;transform:translateY(-50%);color:#ddd;font-size:2rem;
cursor:pointer;padding:1rem;user-select:none;font-family:system-ui,sans-serif}
#lb .prev{left:.4rem}#lb .next{right:.4rem}
"""

PHOTO_JS = """
var imgs=[].slice.call(document.querySelectorAll('.gallery figure'));
var lb=document.getElementById('lb'), lbImg=lb.querySelector('img'),
    capT=lb.querySelector('.cap .t'), capD=lb.querySelector('.cap .d'), cur=0;
function show(i){cur=(i+imgs.length)%imgs.length;var f=imgs[cur],im=f.querySelector('img');
  lbImg.src=im.getAttribute('src');lbImg.alt=im.alt;
  capT.textContent=f.dataset.title||'';capD.textContent=f.dataset.desc||'';lb.classList.add('on');}
imgs.forEach(function(f,i){f.addEventListener('click',function(){show(i);});});
lb.querySelector('.x').addEventListener('click',function(){lb.classList.remove('on');});
lb.querySelector('.prev').addEventListener('click',function(e){e.stopPropagation();show(cur-1);});
lb.querySelector('.next').addEventListener('click',function(e){e.stopPropagation();show(cur+1);});
lb.addEventListener('click',function(e){if(e.target===lb)lb.classList.remove('on');});
document.addEventListener('keydown',function(e){
  if(!lb.classList.contains('on'))return;
  if(e.key==='Escape')lb.classList.remove('on');
  if(e.key==='ArrowLeft')show(cur-1);
  if(e.key==='ArrowRight')show(cur+1);});
"""


def build_photos():
    """独立相册页（部署到 /photos/，不隶属于 /technews）。"""
    import json as _json
    src = os.path.join(ROOT, "photos.json")
    if not os.path.exists(src):
        return None
    photos = _json.load(open(src, encoding="utf-8"))
    figs = []
    for idx, p in enumerate(photos):
        fn = os.path.basename(p["url"])
        # 首屏 8 张直接加载（避免部分浏览器对首屏 lazy 图片不触发），其余懒加载
        lazy = "" if idx < 8 else ' loading="lazy"'
        figs.append(
            f'<figure data-title="{esc(p.get("title",""))}" data-desc="{esc(p.get("description",""))}">'
            f'<img src="{esc(fn)}" alt="{esc(p.get("title",""))}"{lazy}>'
            f'<figcaption>{esc(p.get("title",""))} · {esc(p.get("location",""))}</figcaption></figure>'
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>冬冬的镜头 · 摄影</title>
<meta name="description" content="冬冬的摄影作品：深圳的海、雨与山。">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='18' fill='%23111'/%3E%3Ctext x='50' y='72' font-size='58' text-anchor='middle' fill='%23fff' font-family='serif'%3E%E5%BD%B1%3C/text%3E%3C/svg%3E">
<style>{CSS}{PHOTO_CSS}
.gallery{{grid-template-columns:repeat(4,1fr)}}
@media(max-width:900px){{.gallery{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:640px){{.gallery{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<header class="site"><div class="site-in wrap" style="padding-left:0;padding-right:0">
<a class="brand" href="/">Season<span class="dot">.</span></a>
<span class="tagline">摄影</span>
<nav class="top"><a href="/">主页</a><a href="/technews/">科技情报</a><a href="/breath/">呼吸</a></nav>
</div></header>
<main class="wrap"><article>
<div class="kicker">摄影</div>
<h1 class="title">冬冬的镜头</h1>
<p class="lede">我的朋友冬冬是一位摄影师。这是他镜头下的深圳——海、雨、山里的雾，和那些刚好被撞见的瞬间。</p>
<div class="credit">
<b>关于摄影师</b>　冬冬，摄影师。<br>
这里是一个小小的展墙，如果某张照片让你停了一下，欢迎告诉我也告诉他。
</div>
<div class="gallery">
{''.join(figs)}
</div>
<div id="lb"><span class="x">×</span><span class="nav prev">‹</span><span class="nav next">›</span>
<img src="" alt=""><div class="cap"><span class="t"></span><span class="d"></span></div></div>
</article></main>
<footer class="site"><div class="wrap">
© 2026 Season · 摄影作品版权归冬冬所有，请勿转载
</div></footer>
<script>{PHOTO_JS}</script>
</body>
</html>"""


def build_sitemap(posts):
    urls = [f'{SITE["url"]}/'] + [f'{SITE["url"]}/posts/{p["slug"]}.html' for p in posts]
    urls.append(f'{SITE["url"]}/data/compute-finance.html')
    today = datetime.date.today().isoformat()
    items = "\n".join(
        f"<url><loc>{esc(u)}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq></url>"
        for u in urls
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{items}\n</urlset>")


def main():
    posts = load_posts()
    published = [p for p in posts if not p.get("draft")]
    drafts = [p for p in posts if p.get("draft")]
    os.makedirs(os.path.join(OUT, "posts"), exist_ok=True)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_index(published))
    for p in published:
        with open(os.path.join(OUT, "posts", p["slug"] + ".html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(build_post(p, published))
    if drafts:
        os.makedirs(os.path.join(OUT, "drafts"), exist_ok=True)
        for p in drafts:
            with open(os.path.join(OUT, "drafts", p["slug"] + ".html"), "w", encoding="utf-8", newline="\n") as f:
                f.write(build_post(p, published, draft=True))
    with open(os.path.join(OUT, "rss.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_rss(published))
    g = build_photos()
    if g:
        os.makedirs(GALLERY, exist_ok=True)
        with open(os.path.join(GALLERY, "index.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(g)
        print("photos page -> gallery/index.html")
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_sitemap(published))
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: " + SITE["url"] + "/sitemap.xml\n")
    print(f"OK: {len(published)} published, {len(drafts)} drafts -> {OUT}")
    for p in posts:
        tag = "DRAFT " if p.get("draft") else ""
        print(f"  {p['date']}  {tag}{p['slug']}")


if __name__ == "__main__":
    main()
