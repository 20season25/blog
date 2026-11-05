#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/ 同步到腾讯云服务器 /var/www/blog/aiblog/（纯增量，不触碰其他路径）。

复用 leancoach 的 SSH 工具与密钥：
    python sync_server.py
"""
import importlib.util
import os
import posixpath

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "docs")
REMOTE_ROOT = "/var/www/blog/aiblog"          # 只允许写这个前缀下的文件
SSHTOOL = r"D:\CODE\leancoach\deploy\server-sshtool.py"

spec = importlib.util.spec_from_file_location("sshtool", SSHTOOL)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

cli = s.connect()
sftp = cli.open_sftp()


def mkdirs(remote):
    cur = ""
    for part in remote.strip("/").split("/"):
        cur += "/" + part
        try:
            sftp.stat(cur)
        except FileNotFoundError:
            sftp.mkdir(cur)
            print("mkdir", cur)


n = 0
for base, _, files in os.walk(DOCS):
    rel = os.path.relpath(base, DOCS).replace("\\", "/")
    rdir = REMOTE_ROOT if rel == "." else posixpath.join(REMOTE_ROOT, rel)
    mkdirs(rdir)
    for fn in files:
        lp = os.path.join(base, fn)
        rp = posixpath.join(rdir, fn)
        sftp.put(lp, rp)
        n += 1
        print("put ", rp)

sftp.close()
cli.close()
print(f"\n完成：{n} 个文件 → {REMOTE_ROOT}")
