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
# (本地目录, 服务器目录, 路由前缀)
JOBS = [
    (os.path.join(HERE, "docs"), "/var/www/blog/aiblog", "/technews/"),
    (os.path.join(HERE, "gallery"), "/var/www/photos", "/photos/"),
]
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


for local_root, remote_root, route in JOBS:
    if not os.path.isdir(local_root):
        print(f"skip {local_root} (不存在)")
        continue
    n = 0
    for base, _, files in os.walk(local_root):
        rel = os.path.relpath(base, local_root).replace("\\", "/")
        rdir = remote_root if rel == "." else posixpath.join(remote_root, rel)
        mkdirs(rdir)
        for fn in files:
            sftp.put(os.path.join(base, fn), posixpath.join(rdir, fn))
            n += 1
    print(f"完成：{n} 个文件 → {remote_root}  ({route})")

sftp.close()
cli.close()
