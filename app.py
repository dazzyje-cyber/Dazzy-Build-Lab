# streamlit_app.py
"""
DAZZY JE's BUILD LAB - Single-file Streamlit prototype
Run:
  pip install streamlit pillow qrcode matplotlib numpy
  streamlit run streamlit_app.py

This app is self-contained and will create placeholder assets and a local SQLite DB.
Features:
 - Welcome hero + localStorage handshake (embedded HTML)
 - Home (weapon categories + cards)
 - Weapon detail (attachments, server-side PIL preview layering)
 - Animated-like stat bars (Original, New, Difference)
 - Save builds (SQLite), list builds, rename, delete
 - Share build via encoded URL and QR code
 - Recoil simulator (matplotlib)
 - Compare mode (weapon vs weapon, build vs build)
 - Settings, About, Contact skeletons
"""
import streamlit as st
import json, base64, sqlite3, os, io, time
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import qrcode
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Configuration & Setup
# -----------------------------
st.set_page_config(page_title="DAZZY BUILD LAB", layout="wide", initial_sidebar_state="expanded")

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
FRONTEND = ROOT / "frontend"
DATA = ROOT / "data"
DB_PATH = DATA / "dazzylab.db"

ASSETS.mkdir(parents=True, exist_ok=True)
FRONTEND.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Utility helpers
# -----------------------------
def gen_uid():
    import uuid
    return str(uuid.uuid4())

def ensure_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS builds(
                    id TEXT PRIMARY KEY, name TEXT, user_id TEXT, created_at TEXT, build_json TEXT
                )""")
    conn.commit()
    return conn

DB = ensure_db()

def b64encode_json(obj):
    s = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(s.encode()).decode()

def b64decode_json(payload):
    try:
        return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except Exception:
        return None

# Simple placeholder image generator
def make_placeholder(filename, w=900, h=360, bg=(10,14,20), accent=(255,106,0), text=None):
    path = ASSETS / filename
    if path.exists():
        return str(path)
    img = Image.new("RGB", (w,h), bg)
    draw = ImageDraw.Draw(img)
    try:
        # try common font
        font = ImageFont.truetype("DejaVuSans.ttf", size=40)
    except Exception:
        font = ImageFont.load_default()
    txt = text if text else filename
    draw.text((24,24), txt, fill=accent, font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return str(path)

# Create a set of placeholder images
make_placeholder("hero_bg.jpg", w=1400, h=420, text="DAZZY BUILD LAB")
make_placeholder("weapons/viper_ar.png", w=800, h=360, text="Viper AR Base")
make_placeholder("weapons/shadow_smg.png", w=800, h=360, text="Shadow SMG Base")
make_placeholder("attachments/suppressor.png", w=300, h=150, text="Suppressor")
make_placeholder("attachments/red_dot.png", w=300, h=150, text="Red Dot")
make_placeholder("attachments/light_stock.png", w=300, h=150, text="Light Stock")
make_placeholder("avatar.png", w=300, h=300, text="DAZZY AVATAR")

# -----------------------------
# Data: weapons and attachments (sample)
# -----------------------------
WEAPONS = [
    {
        "id": "viper_ar",
        "name": "Viper AR",
        "class": "Assault Rifle",
        "difficulty": "Medium",
        "meta": "A",
        "description": "Reliable and accurate at medium ranges. Versatile all-rounder.",
        "base_stats": {
            "damage": 32, "range": 60, "accuracy": 72, "recoil": 55,
            "mobility": 62, "ads": 68, "reload": 54, "mag": 30, "fire_rate": 680
        },
        "image": str(ASSETS / "weapons" / "viper_ar.png"),
        "recommended_playstyle": "Mid-range engagements, burst control."
    },
    {
        "id": "shadow_smg",
        "name": "Shadow SMG",
        "class": "SMG",
        "difficulty": "Easy",
        "meta": "B",
        "description": "Fast handling and high mobility, best for close quarters.",
        "base_stats": {
            "damage": 22, "range": 28, "accuracy": 58, "recoil": 48,
            "mobility": 82, "ads": 78, "reload": 58, "mag": 40, "fire_rate": 900
        },
        "image": str(ASSETS / "weapons" / "shadow_smg.png"),
        "recommended_playstyle": "Aggressive close-range skirmishes."
    }
]

ATTACHMENTS = [
    {
        "id": "suppressor",
        "name": "Suppressor",
        "image": str(ASSETS / "attachments" / "suppressor.png"),
        "description": "Reduces sound signature and muzzle flash.",
        "deltas": {"damage": 0, "range": -4, "accuracy": -2, "recoil": -6, "mobility": -2, "ads": -3, "reload": 0, "mag": 0, "fire_rate": 0},
        "advantages": ["Stealthier", "Less visible on killcam"],
        "disadvantages": ["Minor range penalty"]
    },
    {
        "id": "red_dot",
        "name": "Red Dot Sight",
        "image": str(ASSETS / "attachments" / "red_dot.png"),
        "description": "Clear sight picture for mid-range.",
        "deltas": {"damage": 0, "range": +2, "accuracy": +8, "recoil": 0, "mobility": -2, "ads": -6, "reload": 0, "mag": 0, "fire_rate": 0},
        "advantages": ["Accuracy boost"],
        "disadvantages": ["Slight ADS penalty"]
    },
    {
        "id": "light_stock",
        "name": "Light Stock",
        "image": str(ASSETS / "attachments" / "light_stock.png"),
        "description": "Boosts mobility and ADS speed.",
        "deltas": {"damage": 0, "range": 0, "accuracy": -3, "recoil": -6, "mobility": +8, "ads": +10, "reload": 0, "mag": 0, "fire_rate": 0},
        "advantages": ["Mobility/ADS speed"],
        "disadvantages": ["Slight accuracy loss"]
    }
]

WEAPONS_MAP = {w["id"]: w for w in WEAPONS}
ATTACH_MAP = {a["id"]: a for a in ATTACHMENTS}

# -----------------------------
# Styling: injected CSS (dark + orange + neon blue + glass)
# -----------------------------
THEME_CSS = """
<style>
:root{
  --bg:#071022;
  --panel: rgba(255,255,255,0.03);
  --glass-border: rgba(255,255,255,0.05);
  --accent: #ff6a00;
  --neon: #0ae5ff;
  --muted: #9fb0c8;
  --glass-blur: 8px;
}
body { background: var(--bg); color: #e6eef8; }
.topbar { display:flex; align-items:center; justify-content:space-between; padding:12px 18px; border-radius:12px; margin-bottom:12px; }
.hero { position:relative; padding:18px; margin-bottom:12px; border-radius:14px; }
.hero .logo { font-size:30px; font-weight:800; letter-spacing:2px; }
.hero .subtitle { color:var(--muted); margin-top:6px; }
.glass { background: var(--panel); border-radius:12px; padding:12px; border:1px solid var(--glass-border); backdrop-filter: blur(var(--glass-blur)); transition: transform .18s ease, box-shadow .18s ease; }
.weapon-grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(260px,1fr)); gap:14px; }
.weapon-card { display:block; padding:12px; border-radius:12px; text-decoration:none; color:inherit; }
.weapon-card:hover { transform: translateY(-6px); box-shadow: 0 18px 50px rgba(0,0,0,0.6); border:1px solid rgba(10,180,255,0.06); }
.weapon-img { width:100%; height:160px; object-fit:cover; border-radius:8px; }
.category-pill { padding:8px 14px; border-radius:999px; margin-right:8px; display:inline-block; margin-bottom:8px; cursor:pointer; background:linear-gradient(90deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02)); }
.attachment-card { display:flex; gap:12px; align-items:center; padding:8px; border-radius:10px; margin-bottom:8px; }
.attach-img { width:140px; height:70px; object-fit:contain; }
.preview { border-radius:12px; overflow:hidden; }
.stat-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.stat-name { width:110px; font-weight:700; font-size:13px; }
.bars { flex:1; height:16px; background:rgba(255,255,255,0.03); border-radius:8px; position:relative; overflow:hidden; }
.bar { height:100%; position:absolute; left:0; top:0; transition: width 420ms cubic-bezier(.2,.8,.2,1); }
.bar.orig { background:rgba(255,255,255,0.08); z-index:1; }
.bar.new.up { background:linear-gradient(90deg,#00f5a0,#00d2ff); z-index:2; opacity:0.95;}
.bar.new.down { background:linear-gradient(90deg,#ff6a00,#ff9a1a); z-index:2; opacity:0.95;}
.stat-diff { width:64px; text-align:right; font-weight:800; }
.small-muted { color:var(--muted); font-size:13px; }
.cta { background:linear-gradient(90deg,var(--accent),#ff9a1a); color:#07101a; padding:8px 12px; border-radius:10px; font-weight:800; text-decoration:none; }
.kv { display:flex; gap:8px; align-items:center; margin-bottom:6px; }
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)

# -----------------------------
# Local storage handshake HTML
# -----------------------------
LOCAL_STORAGE_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    body{font-family:Inter,system-ui,Roboto,sans-serif;background:#071022;color:#e6eef8;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
    .card{background:rgba(255,255,255,0.03);padding:22px;border-radius:12px;width:420px;box-shadow:0 12px 40px rgba(0,0,0,0.6)}
    h2{margin:0 0 8px 0}
    input{width:100%;padding:12px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:#e6eef8}
    button{margin-top:12px;width:100%;padding:12px;border-radius:10px;border:none;background:linear-gradient(90deg,#ff6a00,#ff9a1a);color:#07101a;font-weight:700;cursor:pointer}
    .sub{font-size:13px;color:#9fb0c8;margin-top:8px}
  </style>
</head>
<body>
  <div class="card">
    <h2>Welcome to DAZZY BUILD LAB</h2>
    <div class="sub">Enter a display name. A unique ID will be generated to keep you distinct.</div>
    <input id="display" placeholder="What should we call you?" autofocus />
    <button id="saveBtn">Save & Enter</button>
    <div style="height:8px"></div>
    <div class="sub">This stores a small profile in your browser only (localStorage).</div>
  </div>
<script>
(function(){
  const input = document.getElementById('display');
  const btn = document.getElementById('saveBtn');
  function genUID(){ return 'xxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,function(c){var r=Math.random()*16|0,v=c=='x'?r:(r&0x3|0x8);return v.toString(16);});}
  btn.onclick = function(){
    const name = input.value.trim() || 'Player';
    const now = new Date().toISOString();
    const existing = localStorage.getItem('dazzylab_user');
    let user = null;
    if (existing) {
      try { user = JSON.parse(existing); } catch(e) { user = null; }
    }
    if (!user) {
      user = { uid: genUID(), display_name: name, first_visit: now, last_visit: now, visit_count: 1, favourite_gun: null, saved_builds: [], recently_viewed: [], theme: 'dark' };
    } else {
      user.display_name = name;
      user.last_visit = now;
      user.visit_count = (user.visit_count||0)+1;
    }
    localStorage.setItem('dazzylab_user', JSON.stringify(user));
    const payload = btoa(unescape(encodeURIComponent(JSON.stringify(user))));
    const url = location.origin + location.pathname + '?dazzy_user=' + payload;
    location.href = url;
  };
})();
</script>
</body>
</html>
"""

# -----------------------------
# Session + User helpers
# -----------------------------
def get_user_from_query():
    params = st.experimental_get_query_params()
    if "dazzy_user" in params:
        payload = params["dazzy_user"][0]
        try:
            return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
        except Exception:
            return None
    return None

def register_user(payload):
    st.session_state["user"] = payload
    # add server-side meta
    st.session_state["user"].setdefault("server_first_seen", datetime.utcnow().isoformat())
    st.session_state["user"]["server_last_seen"] = datetime.utcnow().isoformat()

# -----------------------------
# Stats & Build logic
# -----------------------------
def compute_stats(base, selected_ids):
    modified = base.copy()
    for sid in selected_ids:
        att = ATTACH_MAP.get(sid)
        if not att:
            continue
        for k,v in att["deltas"].items():
            modified[k] = modified.get(k, 0) + v
    diffs = {k: modified.get(k,0) - base.get(k,0) for k in modified}
    return modified, diffs

def render_stat_html(base, modified, diffs):
    order = ["damage","range","accuracy","recoil","mobility","ads","reload","mag","fire_rate"]
    html = "<div class='glass' style='padding:12px'>"
    for k in order:
        b = base.get(k,0)
        m = modified.get(k,0)
        d = diffs.get(k,0)
        maxv = max(1, b, m)
        w_orig = int((b/maxv)*100)
        w_new = int((m/maxv)*100)
        color_class = "up" if d>0 else ("down" if d<0 else "same")
        sign = f"+{d}" if d>0 else str(d)
        html += f"""
        <div class="stat-row">
          <div class="stat-name">{k.upper()}</div>
          <div class="bars">
            <div class="bar orig" style="width:{w_orig}%;"></div>
            <div class="bar new {color_class}" style="width:{w_new}%;"></div>
          </div>
          <div class="stat-diff {'small-muted' if d==0 else ('up' if d>0 else 'down')}">{sign}</div>
        </div>
        """
    html += "</div>"
    return html

# -----------------------------
# Preview compositing (server-side)
# -----------------------------
def composite_preview(base_path, selected_ids, size=(900,400)):
    try:
        base = Image.open(base_path).convert("RGBA")
    except Exception:
        # fallback placeholder
        base = Image.new("RGBA", size, (10,14,20,255))
    base = base.resize(size, Image.LANCZOS)
    canvas = Image.new("RGBA", size, (0,0,0,0))
    canvas.paste(base, (0,0), base)

    # simple composition: attachments center-overlay with scaling and slight offsets
    w,h = size
    for i, aid in enumerate(selected_ids):
        att = ATTACH_MAP.get(aid)
        if not att:
            continue
        try:
            aimg = Image.open(att["image"]).convert("RGBA")
        except Exception:
            continue
        # scale attachment relative to base width (attachments should be smaller)
        scale = 0.42
        aw = int(w * scale)
        aspect = aimg.height / max(1, aimg.width)
        ah = int(aw * aspect)
        aimg = aimg.resize((aw, ah), Image.LANCZOS)
        # position: stagger vertically
        x = int((w - aw) / 2 + (i-0.5)*20)
        y = int(h*0.15 + i*12)
        canvas.paste(aimg, (x,y), aimg)

    # flatten to RGB
    out = Image.alpha_composite(Image.new("RGBA", size, (0,0,0,255)), canvas).convert("RGB")
    return out

# -----------------------------
# Save / Load builds
# -----------------------------
def save_build_to_db(build_obj, user_uid):
    cur = DB.cursor()
    bid = gen_uid()
    cur.execute("INSERT INTO builds(id,name,user_id,created_at,build_json) VALUES (?,?,?,?,?)",
                (bid, build_obj.get("name","build"), user_uid, datetime.utcnow().isoformat(), json.dumps(build_obj)))
    DB.commit()
    return bid

def list_builds_for_user(user_uid):
    cur = DB.cursor()
    cur.execute("SELECT id,name,created_at,build_json FROM builds WHERE user_id=? ORDER BY created_at DESC", (user_uid,))
    rows = cur.fetchall()
    builds = []
    for r in rows:
        bid,name,created_at,build_json = r
        try:
            build = json.loads(build_json)
        except:
            build = {}
        builds.append({"id":bid,"name":name,"created_at":created_at,"build":build})
    return builds

def delete_build(bid):
    cur = DB.cursor()
    cur.execute("DELETE FROM builds WHERE id=?", (bid,))
    DB.commit()

def rename_build(bid, new_name):
    cur = DB.cursor()
    cur.execute("UPDATE builds SET name=? WHERE id=?", (new_name, bid))
    DB.commit()

# -----------------------------
# Recoil simulator (simple)
# -----------------------------
def generate_recoil_trace(seed=0, length=120, variance=1.0):
    rng = np.random.default_rng(seed)
    x = np.cumsum(rng.normal(loc=0.5, scale=0.6*variance, size=length))
    y = np.cumsum(rng.normal(loc=0.0, scale=0.2*variance, size=length))
    return x, y

def plot_recoil_trace(ax, x, y, color="#ff6a00", alpha=0.9):
    ax.plot(x, y, color=color, linewidth=2, alpha=alpha)
    ax.scatter([x[0]],[y[0]], color=color, s=40)
    ax.set_xlabel("Horizontal")
    ax.set_ylabel("Vertical")
    ax.set_title("Recoil Trace")
    ax.invert_yaxis()
    ax.grid(False)

# -----------------------------
# Pages
# -----------------------------
def page_welcome():
    st.markdown("""
    <div class="hero glass" style="display:flex;gap:18px;align-items:center;">
      <div style="flex:1">
        <div class="logo">DAZZY <span style="color:var(--accent)">BUILD LAB</span></div>
        <div class="subtitle small-muted">Blood Strike Gun Modification</div>
        <div style="height:12px"></div>
        <div class="small-muted">Premium companion for weapon builds and optimization.</div>
        <div style="height:16px"></div>
        <button onclick="document.location='/__enter__'" class="cta">ENTER BUILD LAB</button>
      </div>
      <div style="flex:1">
        <img src="assets/hero_bg.jpg" style="width:100%; border-radius:12px; opacity:0.95"/>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # show a Streamlit button to open embedded localstorage HTML (because onclick above isn't interactive)
    if st.button("ENTER BUILD LAB (Click here if the cinematic button above did not work)"):
        st.components.v1.html(LOCAL_STORAGE_HTML, height=480, scrolling=False)

def page_home():
    st.markdown("<div class='topbar glass'><div style='display:flex;gap:12px;align-items:center'><strong>DAZZY BUILD LAB</strong></div><div class='kv small-muted'>Welcome back, <strong>{}</strong></div></div>".format(st.session_state["user"].get("display_name","Player")), unsafe_allow_html=True)
    # search
    q = st.text_input("Search weapons or builds", value="", max_chars=120, key="searchbox")
    # categories
    cols = st.columns((1,1,1,2))
    categories = ["Assault Rifles","SMGs","Shotguns","Snipers","LMGs","Marksman Rifles","Pistols"]
    with cols[0]:
        for i,cat in enumerate(categories[:3]):
            st.markdown(f"<div class='category-pill glass'>{cat}</div>", unsafe_allow_html=True)
    with cols[1]:
        for cat in categories[3:6]:
            st.markdown(f"<div class='category-pill glass'>{cat}</div>", unsafe_allow_html=True)
    with cols[2]:
        for cat in categories[6:]:
            st.markdown(f"<div class='category-pill glass'>{cat}</div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown("<div class='glass' style='padding:12px'><h4>Creator Picks</h4><div class='small-muted'>Featured build of the week & daily tips will show here.</div></div>", unsafe_allow_html=True)

    st.markdown("<h3 style='margin-top:12px'>Weapons</h3>", unsafe_allow_html=True)
    # filter weapons
    filtered_weapons = WEAPONS
    if q:
        qlow = q.lower()
        filtered_weapons = [w for w in WEAPONS if qlow in w["name"].lower() or qlow in w["class"].lower() or qlow in w["description"].lower()]

    # grid
    gird_html = "<div class='weapon-grid'>"
    for w in filtered_weapons:
        gird_html += f"""
        <a class="weapon-card glass" href="?weapon={w['id']}">
          <img class="weapon-img" src="{w['image']}" />
          <div style="padding-top:8px"><strong>{w['name']}</strong></div>
          <div class="small-muted">{w['class']} • Difficulty: {w['difficulty']} • Meta: {w['meta']}</div>
          <div class="small-muted" style="margin-top:6px">{w['description']}</div>
        </a>
        """
    gird_html += "</div>"
    st.markdown(gird_html, unsafe_allow_html=True)

    # quick saved builds preview
    st.markdown("<h3>Saved Builds</h3>", unsafe_allow_
