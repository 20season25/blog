# 认知增量 · 个人博客

「认知增量」的静态博客——与微信公众号同步更新的 AI 深度解读。
**不复述新闻，只更新认知。**

- 线上地址（GitHub Pages）：<https://20season25.github.io/blog/>
- 服务器镜像（腾讯云）：<http://118.25.188.243/aiblog/>
- RSS 全文订阅：<https://20season25.github.io/blog/rss.xml>

## 目录结构

```
aiblog/
├── content/        # 文章 Markdown（front-matter + 正文）
├── build.py        # 生成器：content/ → docs/（零依赖，纯标准库）
├── prep_content.py # 从 Obsidian 库装配文章的一次性脚本（可复用）
├── sync_server.py  # 将 docs/ 同步到腾讯云服务器
└── docs/           # 生成产物 = 站点本体（GitHub Pages 从这里读）
```

## 如何发新文章

1. 在 `content/` 新建 `slug.md`（或改 `prep_content.py` 的 POSTS 表后运行它），格式：

   ```markdown
   ---
   slug: my-new-post
   title: 文章标题
   date: 2026-11-13
   series: 深度解读        # 可选：算力金融 / 深度解读 / 安全速写 / AI周报
   order:                  # 系列内序号，非系列留空
   tags: [AI行业]
   summary: 一句话摘要，显示在目录卡片上
   ---

   正文（Markdown 子集：标题/段落/**加粗**/`代码`/引用/列表/分隔线）…
   ```

2. `python build.py` 重新生成 `docs/`
3. `git add -A && git commit -m "post: 标题" && git push` → GitHub Pages 约 1 分钟后自动更新
4. `python sync_server.py` 同步到腾讯云镜像

## 改站名 / 签名 / 描述

只改 `build.py` 顶部的 `SITE` 字典，重新 build 即可。

## 技术说明

- 生成器只用 Python 标准库（本机 3.8 可跑），无任何 npm/pip 依赖
- 无外部字体/JS，国内访问不受 CDN 影响；深色模式跟随系统
- GitHub Pages 源：`main` 分支 `/docs` 目录
- 服务器部署为**纯增量**：只写 `/var/www/blog/aiblog/`，与既有站点「编程之季」完全隔离，删掉该目录即完成下线
