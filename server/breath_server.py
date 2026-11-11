#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""呼吸 记录服务。

只监听 127.0.0.1:8089，外部必须经 nginx Basic 认证 + 限流。
数据：/var/www/home/breath/entries.json
照片：/var/www/home/breath/photos/YYYY-MM-DD.jpg

接口：
    GET  /           记录表单
    POST /api        JSON {text, weather?}        写一条文字记录
    POST /api-photo?date=YYYY-MM-DD  二进制图片    写当天照片（可单独传，也可后传）
"""
import json
import os
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = "/var/www/home/breath"
DATA = os.path.join(BASE, "entries.json")
PHOTOS = os.path.join(BASE, "photos")
GUEST = "/var/www/home/guestbook/entries.json"
PORT = 8089
MAX_BYTES = 15 * 1024 * 1024
ALLOWED = {b"\xff\xd8\xff": ".jpg", b"\x89PNG\r\n\x1a\n": ".png", b"RIFF": ".webp"}

FORM = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>呼吸 · 今日记录</title>
<style>
body{margin:0;background:#131312;color:#e6e4df;font:15px/1.9 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.box{max-width:34rem;margin:0 auto;padding:2.2rem 1.2rem 4rem}
h1{font-size:1.2rem;font-weight:600;margin:0 0 .2rem}
p.sub{color:#8f8d85;font-size:.82rem;margin:0 0 1.8rem}
label{display:block;font-size:.8rem;color:#8f8d85;margin:1.1rem 0 .35rem}
input,textarea{width:100%;box-sizing:border-box;background:#1b1b19;border:1px solid #2a2a26;
border-radius:8px;color:#e6e4df;padding:.6rem .7rem;font:inherit;font-size:.9rem}
input[type=file]{padding:.5rem}
button{margin-top:1.6rem;width:100%;padding:.8rem;border:0;border-radius:8px;background:#5b7a5b;
color:#fff;font-size:.95rem;font-weight:600;cursor:pointer}
button:disabled{opacity:.5}
#msg{margin-top:1rem;font-size:.85rem;min-height:1.4em}
.ok{color:#8fae8f}.err{color:#e05a4e}
img.prev{max-width:100%;border-radius:8px;margin-top:.8rem;display:none}
a{color:#8fae8f}
</style></head><body><div class="box">
<h1>呼吸 · 今日</h1>
<p class="sub">一张照片，一句话。30 秒。</p>
<form id="f">
  <label>照片（可选，但最好有）</label>
  <input type="file" id="file" accept="image/jpeg,image/png,image/webp">
  <img class="prev" id="prev" alt="">
  <label>今天 · 一句话锚点</label>
  <textarea id="text" rows="3" placeholder="今天最具体的一个瞬间" maxlength="500" required></textarea>
  <label>天气 / 身体（可选）</label>
  <input id="weather" placeholder="比如：晴 / 肩膀是松的" maxlength="60">
  <button type="submit" id="btn">记下</button>
  <div id="msg"></div>
</form>
<p style="margin-top:2.5rem;font-size:.8rem;color:#8f8d85">
忘记记录的那天：随便写一句"今天没写"，也算数。</p>
<p><a href="/breath/">← 看看现在记到哪了</a></p>
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
    im.onload=function(){URL.revokeObjectURL(u);res(im);};
    im.onerror=function(){URL.revokeObjectURL(u);rej(new Error('读图失败'));};
    im.src=u;
  });
}
function compress(im,max,q){
  var s=Math.min(1,max/Math.max(im.naturalWidth,im.naturalHeight));
  var w=Math.round(im.naturalWidth*s),h=Math.round(im.naturalHeight*s);
  var c=document.createElement('canvas');c.width=w;c.height=h;
  var x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,w,h);x.drawImage(im,0,0,w,h);
  return new Promise(function(res){c.toBlob(res,'image/jpeg',q);});
}
function today(){var d=new Date();return d.toISOString().slice(0,10);}
document.getElementById('f').addEventListener('submit',function(e){
  e.preventDefault();
  var msg=document.getElementById('msg'),btn=document.getElementById('btn');
  btn.disabled=true;msg.className='';msg.textContent='记录中…';
  var text=document.getElementById('text').value.trim();
  var weather=document.getElementById('weather').value.trim();
  var file=f.files[0];
  var go=function(){
    return fetch('api',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:text,weather:weather,date:today()})})
      .then(function(r){return r.json();})
      .then(function(d){if(!d.ok)throw new Error(d.error||'失败');return d;});
  };
  var chain;
  if(file){
    chain=loadImg(file).then(function(im){return compress(im,2000,0.8);})
      .then(function(b){
        msg.textContent='上传照片…（'+Math.round(b.size/1024)+'KB）';
        return fetch('api-photo?date='+today(),{method:'POST',
          headers:{'Content-Type':'image/jpeg'},body:b})
          .then(function(r){return r.json();})
          .then(function(d){if(!d.ok)throw new Error(d.error||'照片失败');return d;});
      }).then(go);
  } else { chain=go(); }
  chain.then(function(){
    msg.className='ok';msg.textContent='记下了。今天呼吸过了。';
    document.getElementById('f').reset();prev.style.display='none';
  }).catch(function(err){
    msg.className='err';msg.textContent='失败：'+(err&&err.message?err.message:err);
  }).then(function(){btn.disabled=false;});
});
</script></body></html>"""


def load_data():
    if not os.path.exists(DATA):
        return {"start": None, "entries": []}
    try:
        return json.load(open(DATA, encoding="utf-8"))
    except Exception:
        return {"start": None, "entries": []}


def save_data(d):
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA)


def load_guest():
    if not os.path.exists(GUEST):
        return []
    try:
        return json.load(open(GUEST, encoding="utf-8"))
    except Exception:
        return []


def save_guest(items):
    os.makedirs(os.path.dirname(GUEST), exist_ok=True)
    tmp = GUEST + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, GUEST)


def length_check(handler, limit):
    try:
        n = int(handler.headers.get("Content-Length", "0"))
    except ValueError:
        n = 0
    if n <= 0 or n > limit:
        handler._send(400, json.dumps({"ok": False, "error": "空请求或超大"}))
        return False
    return True


class H(BaseHTTPRequestHandler):
    server_version = "breath-post/1.0"

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path.startswith("/api-guest-list"):
            items = load_guest()
            self._send(200, json.dumps(sorted(items, key=lambda x: -x.get("id", 0))[-60:],
                                       ensure_ascii=False))
            return
        if self.path.startswith("/api"):
            self._send(405, json.dumps({"ok": False, "error": "use POST"}))
            return
        self._send(200, FORM, "text/html; charset=utf-8")

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if u.path.startswith("/api-guest-delete"):
            if length_check(self, 4096) is False:
                return
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            try:
                body = json.loads(raw.decode("utf-8"))
            except Exception:
                self._send(400, json.dumps({"ok": False, "error": "bad json"}))
                return
            gid = body.get("id")
            items = load_guest()
            kept = [x for x in items if x.get("id") != gid]
            save_guest(kept)
            self._send(200, json.dumps({"ok": True, "removed": len(items) - len(kept)}))
            return

        if u.path.startswith("/api-guest-add"):
            if length_check(self, 4096) is False:
                return
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            try:
                body = json.loads(raw.decode("utf-8"))
            except Exception:
                self._send(400, json.dumps({"ok": False, "error": "bad json"}))
                return
            if body.get("website"):                    # 蜜罐：假装成功
                self._send(200, json.dumps({"ok": True}))
                return
            text = (body.get("text") or "").strip()[:200]
            if not text:
                self._send(400, json.dumps({"ok": False, "error": "写点什么都好，但得写"}))
                return
            items = load_guest()
            if len(items) >= 500:
                self._send(429, json.dumps({"ok": False, "error": "留言簿已满，等管理员清理"}))
                return
            gid = (max((x.get("id", 0) for x in items), default=0)) + 1
            items.append({
                "id": gid,
                "name": (body.get("name") or "").strip()[:30] or "路人",
                "text": text,
                "ts": time.strftime("%Y-%m-%d %H:%M"),
            })
            save_guest(items)
            self._send(200, json.dumps({"ok": True, "id": gid}, ensure_ascii=False))
            return

        if u.path.startswith("/api-photo"):
            q = urllib.parse.parse_qs(u.query)
            date = (q.get("date", [""])[0] or "").strip()
            if not date or not date.count("-") == 2:
                self._send(400, json.dumps({"ok": False, "error": "date?"}))
                return
            if length <= 0 or length > MAX_BYTES:
                self._send(400, json.dumps({"ok": False, "error": "照片为空或太大"}))
                return
            body = self.rfile.read(length)
            ext = ".jpg"
            for magic, e in ALLOWED.items():
                if body.startswith(magic):
                    ext = e
                    break
            if not ext:
                self._send(415, json.dumps({"ok": False, "error": "只支持 JPG/PNG/WebP"}))
                return
            os.makedirs(PHOTOS, exist_ok=True)
            fn = date + ext
            with open(os.path.join(PHOTOS, fn), "wb") as f:
                f.write(body)
            os.chmod(os.path.join(PHOTOS, fn), 0o644)
            d = load_data()
            for e in d["entries"]:
                if e["date"] == date:
                    e["photo"] = fn
            save_data(d)
            self._send(200, json.dumps({"ok": True, "photo": fn}))
            return

        if u.path.startswith("/api"):
            if length <= 0 or length > 65536:
                self._send(400, json.dumps({"ok": False, "error": "空请求"}))
                return
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw.decode("utf-8"))
            except Exception:
                self._send(400, json.dumps({"ok": False, "error": "bad json"}))
                return
            text = (body.get("text") or "").strip()[:500]
            if not text:
                self._send(400, json.dumps({"ok": False, "error": "至少写一句话"}))
                return
            weather = (body.get("weather") or "").strip()[:60]
            date = (body.get("date") or time.strftime("%Y-%m-%d"))[:10]

            d = load_data()
            replaced = False
            for e in d["entries"]:
                if e["date"] == date:
                    e["text"] = text
                    if weather:
                        e["weather"] = weather
                    replaced = True
            if not replaced:
                d["entries"].append({
                    "date": date, "text": text,
                    "weather": weather or None,
                    "photo": body.get("photo"),
                })
            if not d.get("start"):
                d["start"] = min([e["date"] for e in d["entries"]] + [date])
            save_data(d)
            self._send(200, json.dumps({"ok": True, "date": date, "replaced": replaced}))
            return

        self._send(404, json.dumps({"ok": False, "error": "not found"}))

    def log_message(self, fmt, *args):
        print("[%s] %s" % (time.strftime("%H:%M:%S"), fmt % args), flush=True)


if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    if not os.path.exists(DATA):
        save_data({"start": None, "entries": []})
    print(f"breath service on 127.0.0.1:{PORT}, data={DATA}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
