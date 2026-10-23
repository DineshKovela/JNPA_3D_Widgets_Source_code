"""Assemble the single-page app: shell + CDN libraries + inlined modules -> web/index.html"""
import os
here = os.path.dirname(os.path.abspath(__file__))
web = os.path.join(here, "web")
shell = open(os.path.join(web, "shell.html")).read()
cdn = [
    "https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js",
    "https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js",
    "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js",
]
mods = ["core", "demand", "macro", "meso", "micro", "analysis", "realtime", "scene", "vehicles3d", "anim3d", "app"]
ENGINE = {"core", "demand", "macro", "meso", "micro"}   # modules copied into Web Workers
out = shell + "\n" + "\n".join(f'<script src="{u}"></script>' for u in cdn) + "\n"
for m in mods:
    tag = '<script data-engine="1">' if m in ENGINE else "<script>"
    out += f"{tag}\n/* ---- {m}.js ---- */\n" + open(os.path.join(web, "src", m + ".js")).read() + "\n</script>\n"
open(os.path.join(web, "index.html"), "w").write(out)
print("index.html", len(out) // 1024, "KB")

# standalone build: all data embedded, no network requests for data
import base64, io
from PIL import Image
d = os.path.join(web, "data")
emb = ""
for name in ["network", "buildings", "quality", "terrain"]:
    txt = open(os.path.join(d, name + ".json")).read().replace("</", "<\\/")
    emb += f'<script type="application/json" id="d-{name}">{txt}</script>\n'
im = Image.open(os.path.join(d, "ortho.jpg"))
buf = io.BytesIO(); im.save(buf, "JPEG", quality=80, optimize=True)
emb += '<script type="text/plain" id="d-ortho">data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode() + "</script>\n"
i = out.index("<script src=")
full = out[:i] + emb + out[i:]
open(os.path.join(web, "standalone.html"), "w").write(full)
print("standalone.html", len(full) // 1024, "KB")

# full HTML documents for opening from disk / self-hosting (the artifact viewer adds this skeleton itself)
SKEL = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'
for src, dst in [("index.html", "index.html"), ("standalone.html", "../TrafficTwin.html")]:
    body = open(os.path.join(web, src)).read()
    if not body.startswith("<!doctype"):
        open(os.path.join(web, dst), "w").write(SKEL + body + "</body></html>")
print("TrafficTwin.html + index.html written as full documents")
