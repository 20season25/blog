#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冬冬相册上传服务。

只监听 127.0.0.1，外部访问必须经 nginx + HTTP Basic 认证 + 限流。
零依赖（仅标准库）。

目录约定：
    /var/www/photos/dongdong/photos.json   照片元数据
    /var/www/photos/dongdong/{id}.jpg      照片本体

接口：
    GET  /        上传页
    POST /api?title=&desc=&loc=   请求体为图片原始字节
"""
import json
import os
import re
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = "/var/www/photos/dongdong"
META = os.path.join(BASE, "photos.json")
PORT = 8088
MAX_BYTES = 15 * 1024 * 1024   # 单张 15MB
MAX_FILES = 600                # 总量上限，防无限上传
ALLOWED = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
    b"RIFF": ".webp",
}

FORM = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>上传照片</title>
<style>
body{margin:0;background:#141412;color:#e8e6e1;font:15px/1.9 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.box{max-width:34rem;margin:0 auto;padding:2.2rem 1.2rem 4rem}
h1{font-size:1.3rem;font-weight:600;margin:0 0 .3rem}
p.sub{color:#8f8d85;font-size:.85rem;margin:0 0 1.8rem}
label{display:block;font-size:.82rem;color:#9a988f;margin:1.1rem 0 .35rem}
input,textarea{width:100%;box-sizing:border-box;background:#1c1c19;border:1px solid #2c2b27;
border-radius:8px;color:#e8e6e1;padding:.6rem .7rem;font:inherit;font-size:.9rem}
input[type=file]{padding:.5rem}
button{margin-top:1.8rem;width:100%;padding:.8rem;border:0;border-radius:8px;background:#e05a4e;
color:#fff;font-size:.95rem;font-weight:600;cursor:pointer}
button:disabled{opacity:.5}
#msg{margin-top:1rem;font-size:.85rem;min-height:1.4em}
.ok{color:#6fbf8f}.err{color:#e05a4e}
img.prev{max-width:100%;border-radius:8px;margin-top:.8rem;display:none}
</style></head><body><div class="box">
<h1>上传照片</h1>
<p class="sub">冬冬的镜头 · 上传后立即出现在展墙上</p>
<form id="f">
  <label>照片（JPG / PNG / WebP，单张不超过 15MB）</label>
  <input type="file" id="file" accept="image/jpeg,image/png,image/webp" required>
  <img class="prev" id="prev" alt="">
  <label>标题</label>
  <input id="title" placeholder="比如：赶海的傍晚" maxlength="60">
  <label>一句话说明</label>
  <textarea id="desc" rows="3" placeholder="这张照片背后的故事" maxlength="300"></textarea>
  <label>地点</label>
  <input id="loc" placeholder="比如：深圳·西涌" maxlength="60">
  <button type="submit" id="btn">上传</button>
  <div id="msg"></div>
</form>
</div>
<script>
var f=document.getElementById('file'),prev=document.getElementById('prev');
f.addEventListener('change',function(){
  var file=f.files[0]; if(!file)return;
  prev.src=URL.createObjectURL(file); prev.style.display='block';
});
function loadImg(file){
  return new Promise(function(res,rej){
    var u=URL.createObjectURL(file), im=new Image();
    im.onload=function(){ URL.revokeObjectURL(u); res(im); };
    im.onerror=function(e){ URL.revokeObjectURL(u); rej(e); };
    im.src=u;
  });
}
function compress(im,max,q){
  var s=Math.min(1,max/Math.max(im.naturalWidth,im.naturalHeight));
  var w=Math.round(im.naturalWidth*s), h=Math.round(im.naturalHeight*s);
  var c=document.createElement('canvas'); c.width=w; c.height=h;
  var x=c.getContext('2d');
  x.fillStyle='#fff'; x.fillRect(0,0,w,h);
  x.drawImage(im,0,0,w,h);
  return new Promise(function(res){ c.toBlob(res,'image/jpeg',q); });
}
document.getElementById('f').addEventListener('submit',function(e){
  e.preventDefault();
  var file=f.files[0], msg=document.getElementById('msg'), btn=document.getElementById('btn');
  if(!file){ msg.className='err'; msg.textContent='请选择一张照片'; return; }
  btn.disabled=true; msg.className=''; msg.textContent='处理中…';
  loadImg(file).then(function(im){
    return Promise.all([compress(im,2000,0.82), compress(im,720,0.72)]);
  }).then(function(b){
    var full=b[0], thumb=b[1];
    msg.textContent='上传中…（'+Math.round(full.size/1024)+'KB）';
    var q=new URLSearchParams({
      title:document.getElementById('title').value,
      desc:document.getElementById('desc').value,
      loc:document.getElementById('loc').value
    });
    return fetch('api?'+q.toString(),{method:'POST',headers:{'Content-Type':'image/jpeg'},body:full})
      .then(function(r){ return r.json(); })
      .then(function(d){
        if(!d.ok) throw new Error(d.error||'上传失败');
        return fetch('api?kind=thumb&id='+d.id,{method:'POST',headers:{'Content-Type':'image/jpeg'},body:thumb})
          .then(function(){ return d; });
      });
  }).then(function(d){
    msg.className='ok'; msg.textContent='上传成功（第 '+d.id+' 张），刷新作品集即可看到';
    document.getElementById('f').reset(); prev.style.display='none';
  }).catch(function(err){
    msg.className='err'; msg.textContent='失败：'+(err&&err.message?err.message:err);
  }).then(function(){ btn.disabled=false; });
});
</script></body></html>"""


def load_meta():
    if not os.path.exists(META):
        return []
    try:
        return json.load(open(META, encoding="utf-8"))
    except Exception:
        return []


def save_meta(items):
    tmp = META + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, META)


def next_id(items, base):
    used = {int(x["id"]) for x in items if str(x.get("id", "")).isdigit()}
    n = max(used) + 1 if used else 1
    while os.path.exists(os.path.join(base, f"{n}.jpg")) or \
          os.path.exists(os.path.join(base, f"{n}.png")):
        n += 1
    return n


class H(BaseHTTPRequestHandler):
    server_version = "photo-upload/1.0"

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api"):
            self._send(405, json.dumps({"ok": False, "error": "use POST"}))
            return
        self._send(200, FORM, "text/html; charset=utf-8")

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if not u.path.startswith("/api"):
            self._send(404, json.dumps({"ok": False, "error": "not found"}))
            return
        q = urllib.parse.parse_qs(u.query)
        title = (q.get("title", [""])[0] or "").strip()[:60]
        desc = (q.get("desc", [""])[0] or "").strip()[:300]
        loc = (q.get("loc", [""])[0] or "").strip()[:60]

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0:
            self._send(400, json.dumps({"ok": False, "error": "空请求"}))
            return
        if length > MAX_BYTES:
            self._send(413, json.dumps({"ok": False, "error": "照片超过 15MB"}))
            return

        items = load_meta()
        if len(items) >= MAX_FILES:
            self._send(429, json.dumps({"ok": False, "error": f"已达 {MAX_FILES} 张上限"}))
            return

        body = self.rfile.read(length)
        ext = None
        for magic, e in ALLOWED.items():
            if body.startswith(magic):
                ext = e
                break
        if not body:
            self._send(400, json.dumps({"ok": False, "error": "没有收到数据"}))
            return
        if not ext:
            self._send(415, json.dumps({"ok": False, "error": "只支持 JPG / PNG / WebP"}))
            return

        # 缩略图（前端 canvas 压缩后二次上传）
        kind = (q.get("kind", [""])[0] or "").strip()
        if kind == "thumb":
            tid = (q.get("id", [""])[0] or "").strip()
            if not tid.isdigit():
                self._send(400, json.dumps({"ok": False, "error": "缺少 id"}))
                return
            tname = f"{tid}_t.jpg"
            with open(os.path.join(BASE, tname), "wb") as f:
                f.write(body)
            os.chmod(os.path.join(BASE, tname), 0o644)
            items = load_meta()
            for it in items:
                if str(it.get("id")) == tid:
                    it["thumb"] = f"/photos/dongdong/{tname}"
            save_meta(items)
            self._send(200, json.dumps({"ok": True, "thumb": tname}))
            return

        pid = next_id(items, BASE)
        fn = f"{pid}{ext}"
        path = os.path.join(BASE, fn)
        with open(path, "wb") as f:
            f.write(body)
        os.chmod(path, 0o644)

        items.append({
            "id": str(pid),
            "url": f"/photos/dongdong/{fn}",
            "thumb": f"/photos/dongdong/{pid}_t.jpg",
            "title": title or "无题",
            "description": desc,
            "date": time.strftime("%Y年%-m月%-d日"),
            "location": loc,
        })
        save_meta(items)
        self._send(200, json.dumps({"ok": True, "id": pid, "file": fn}, ensure_ascii=False))

    def log_message(self, fmt, *args):
        print("[%s] %s" % (time.strftime("%H:%M:%S"), fmt % args), flush=True)


if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    print(f"upload server on 127.0.0.1:{PORT}, base={BASE}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
