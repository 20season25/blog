#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Obsidian 公众号库装配博客内容：拷贝正文 + 剥离 H1 + 注入 front-matter。

用法: python prep_content.py
只新增/覆盖 content/*.md，绝不改动 Obsidian 库。
"""
import os

VAULT = r"D:\Obsidian Vault\公众号"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "content")
os.makedirs(OUT, exist_ok=True)

# slug: (vault 相对路径, 元数据)
POSTS = {
    "anthropic-ipo-807b": (
        r"Anthropic上市推文\Anthropic要上市了-看清807亿美元亏损的真相再谈2万亿估值.md",
        dict(
            title='Anthropic要上市了：看清807亿美元"亏损"的真相，再谈2万亿估值',
            date="2026-10-29", series="算力金融", order=1,
            tags=["AI行业", "资本市场"],
            summary="一家\"净亏807亿\"的公司，凭什么谈2万亿估值——看懂招股书里的会计幻觉，和1500家大客户背后的早期市场。",
        ),
    ),
    "anthropic-9000b-real-debt": (
        r"Anthropic上市推文\Anthropic招股书再读-807亿亏损是幻觉-9000亿承诺才是真债.md",
        dict(
            title="Anthropic招股书再读：807亿亏损是幻觉，9000亿承诺才是真债",
            date="2026-11-02", series="算力金融", order=2,
            tags=["AI行业", "资本市场"],
            summary="真正吓人的数字写在报表之外：近9000亿美元算力承诺，付款期排到2045年，而还款来源写的是\"AI自己变强\"。",
        ),
    ),
    "qwen-on-iphone": (
        r"苹果智能×千问推文\千问上了iPhone-等了两年的Apple智能进中国-赢家为什么是它.md",
        dict(
            title="千问上了iPhone：等了两年的Apple智能进中国，赢家为什么是它",
            date="2026-11-03", series="深度解读", order=None,
            tags=["AI行业", "渠道"],
            summary="复盘两年谈判桌：传闻主角从百度换成阿里，模型座次翻了几轮，iPhone上那个位置从没换过人。模型决定入场券，渠道决定胜负。",
        ),
    ),
    "black-october-ai-keys": (
        r"黑色十月安全速写\黑色十月-小偷不偷数据了-改偷AI钥匙.md",
        dict(
            title="黑色十月：小偷不偷数据了，改偷AI钥匙",
            date="2026-11-04", series="安全速写", order=1,
            tags=["AI安全"],
            summary="九个平台连环失窃、假官方扩展上架11小时、模型48小时自主攻破6个浏览器版本——附普通人的五条自保清单。",
        ),
    ),
    "ai-search-answer-leaves-link-dies": (
        r"AI搜索围墙推文\一天蒸发5000亿-当AI搜索决定答案留下链接消失.md",
        dict(
            title='一天蒸发5000亿：当AI搜索决定"答案留下，链接消失"',
            date="2026-11-05", series="深度解读", order=None,
            tags=["AI搜索", "创作者经济"],
            summary="谷歌史上最惨一天、Reddit每周流失百万访问开始砌墙——\"内容免费、广告买单\"的旧契约，正在被AI搜索重新议价。",
        ),
    ),
    "ai-weekly-001": (
        r"2026-11-06 AI周报1-钱和墙.md",
        dict(
            title="AI周报 #1：这周，AI圈聊的全是\"钱\"和\"墙\"",
            date="2026-11-06", series="AI周报", order=1,
            tags=["周报"],
            summary="创刊号：亏损是幻觉承诺是真债、3万亿集体承诺、5000亿蒸发、内容结算与自保清单——这周该更新的六个认知。",
        ),
    ),
    "nvidia-as-guarantor": (
        r"英伟达担保人推文\英伟达开始干银行的活-AI万亿承诺背后的担保人.md",
        dict(
            title="英伟达开始干银行的活：AI万亿承诺背后的担保人",
            date="2026-11-09", series="算力金融", order=3,
            tags=["AI行业", "资本市场"],
            summary="卖芯片的公司开始替买芯片的人按手印借钱——担保、信用循环，和朗讯、北电的历史回声。",
        ),
    ),
}


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return "[" + ", ".join(v) + "]"
    return str(v)


for slug, (rel, meta) in POSTS.items():
    src = os.path.join(VAULT, rel)
    body = open(src, encoding="utf-8-sig").read().replace("\r\n", "\n").strip()
    lines = body.split("\n")
    if lines and lines[0].startswith("# "):  # 剥离 H1，标题由 front-matter 提供
        lines = lines[1:]
    body = "\n".join(lines).strip()
    fm = "\n".join(
        f"{k}: {fmt(meta[k])}" for k in ("title", "date", "series", "order", "tags", "summary")
    )
    dst = os.path.join(OUT, slug + ".md")
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"---\nslug: {slug}\n{fm}\n---\n\n{body}\n")
    print(f"{slug}.md  <- {rel}  ({len(body)} chars)")
