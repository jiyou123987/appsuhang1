# -*- coding: utf-8 -*-
"""
우리집 냉장고 — v5
양문형 냉장고 UI · 세로형 로비 · 단계별 직접 입력
"""

import os
import json
import hashlib
import datetime as dt
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st

st.set_page_config(page_title="우리집 냉장고", page_icon="🧊",
                   layout="centered", initial_sidebar_state="collapsed")

DATA_FILE = "fridge_data.json"
TODAY = dt.datetime.now(ZoneInfo("Asia/Seoul")).date()
WD = ["월", "화", "수", "목", "금", "토", "일"]

# 칸: 좌측문 / 우측문 / 하단서랍  (기타 포함)
ZONES = {
    "dairy":  {"name": "유제품", "emoji": "🥛", "side": "L"},
    "veg":    {"name": "야채",   "emoji": "🥬", "side": "L"},
    "fruit":  {"name": "과일",   "emoji": "🍎", "side": "L"},
    "meat":   {"name": "고기",   "emoji": "🥩", "side": "R"},
    "side":   {"name": "반찬",   "emoji": "🍱", "side": "R"},
    "frozen": {"name": "냉동",   "emoji": "🧊", "side": "R"},
    "etc":    {"name": "기타",   "emoji": "📦", "side": "B"},
}
ZKEYS = list(ZONES.keys())
LZ = [k for k, v in ZONES.items() if v["side"] == "L"]
RZ = [k for k, v in ZONES.items() if v["side"] == "R"]

FOOD_DB = {
    "우유":     ("dairy", 7,  "🥛", "개봉 후엔 문쪽 말고 안쪽 선반에 두세요."),
    "요구르트": ("dairy", 14, "🥤", "뚜껑을 꼭 닫아 냄새 흡수를 막아주세요."),
    "치즈":     ("dairy", 21, "🧀", "랩 대신 종이포일로 싸면 덜 눅눅해져요."),
    "버터":     ("dairy", 60, "🧈", "냄새를 잘 먹어요. 밀폐용기에 따로."),
    "계란":     ("dairy", 21, "🥚", "뾰족한 쪽을 아래로. 씻지 말고 넣기."),
    "두부":     ("side",  5,  "🧈", "물에 잠기게 담가 매일 물을 갈아주세요."),
    "대파":     ("veg",   10, "🌿", "송송 썰어 지퍼백에 얼리면 2개월!"),
    "양파":     ("veg",   30, "🧅", "통째로는 실온 망에. 깐 건 밀폐 냉장."),
    "당근":     ("veg",   21, "🥕", "신문지에 싸서 세워두면 오래가요."),
    "감자":     ("veg",   30, "🥔", "냉장 금지! 어두운 실온에 보관하세요."),
    "애호박":   ("veg",   10, "🥒", "자른 단면에 랩을 밀착시켜 주세요."),
    "양배추":   ("veg",   14, "🥬", "심을 파내고 젖은 키친타월을 끼워두세요."),
    "시금치":   ("veg",   5,  "🥬", "세워서 보관. 눕히면 금방 물러요."),
    "버섯":     ("veg",   7,  "🍄", "씻지 말고 종이봉투에. 물기가 적이에요."),
    "무":       ("veg",   21, "🥗", "잎을 잘라내고 신문지에 싸서 세워두세요."),
    "오이":     ("veg",   7,  "🥒", "랩에 싸서 세워 보관하면 무르지 않아요."),
    "파프리카": ("veg",   12, "🫑", "꼭지째 키친타월에 싸서 보관하세요."),
    "고추":     ("veg",   10, "🌶️", "물기를 완전히 없애고 밀폐용기에."),
    "토마토":   ("fruit", 7,  "🍅", "꼭지를 아래로. 덜 익었으면 실온에."),
    "사과":     ("fruit", 21, "🍎", "에틸렌이 나와요. 다른 채소와 분리!"),
    "바나나":   ("fruit", 5,  "🍌", "냉장 금지. 꼭지를 랩으로 감싸세요."),
    "딸기":     ("fruit", 3,  "🍓", "먹기 직전에 씻기. 한 겹만 펴서."),
    "포도":     ("fruit", 7,  "🍇", "씻지 않은 채로 통풍되는 용기에."),
    "귤":       ("fruit", 14, "🍊", "한 겹씩 펴서 통풍시켜 주세요."),
    "수박":     ("fruit", 5,  "🍉", "자른 면에 랩을 밀착시켜 주세요."),
    "닭고기":   ("meat",  2,  "🍗", "핏물을 닦고 한 끼씩 소분해 냉동하세요."),
    "돼지고기": ("meat",  3,  "🥓", "공기를 빼고 밀착 포장. 3일 넘기면 냉동."),
    "소고기":   ("meat",  3,  "🥩", "키친타월로 핏물 제거 후 랩 밀착 포장."),
    "생선":     ("meat",  2,  "🐟", "내장을 빼고 물기를 닦아 이중 포장."),
    "새우":     ("frozen", 30, "🦐", "해동은 냉장실에서 천천히. 재냉동 금물."),
    "만두":     ("frozen", 90, "🥟", "펼쳐 얼린 뒤 봉지에 모아주세요."),
    "아이스크림": ("frozen", 180, "🍦", "문쪽 말고 가장 안쪽에 두세요."),
    "김치":     ("side",  60, "🥬", "꾹 눌러 국물에 잠기게 해주세요."),
    "햄":       ("side",  14, "🍖", "개봉 후엔 밀폐용기로 옮겨 담으세요."),
    "밥":       ("side",  2,  "🍚", "따뜻할 때 한 공기씩 랩에 싸서 냉동."),
    "식빵":     ("side",  5,  "🍞", "냉장보다 냉동이 나아요. 바로 구우세요."),
    "소스":     ("etc",   90, "🧂", "개봉 후엔 냉장. 뚜껑을 깨끗이 닦으세요."),
    "음료":     ("etc",   30, "🥤", "개봉 후엔 2~3일 안에 드세요."),
}
HALF = {"대파", "양배추", "두부", "애호박", "당근", "양파", "무", "식빵", "수박", "파프리카"}

RECIPES = [
    {"n": "계란찜",        "e": "🍳", "i": ["계란", "대파"],                  "t": "10분"},
    {"n": "파기름 볶음밥",  "e": "🍚", "i": ["대파", "밥", "계란"],            "t": "15분"},
    {"n": "두부김치",      "e": "🥬", "i": ["두부", "김치", "돼지고기"],      "t": "20분"},
    {"n": "된장찌개",      "e": "🍲", "i": ["두부", "애호박", "양파", "감자"], "t": "25분"},
    {"n": "양배추전",      "e": "🥞", "i": ["양배추", "계란"],                "t": "15분"},
    {"n": "닭볶음탕",      "e": "🍗", "i": ["닭고기", "감자", "당근", "양파"], "t": "40분"},
    {"n": "제육볶음",      "e": "🥓", "i": ["돼지고기", "양파", "대파"],      "t": "25분"},
    {"n": "버섯크림파스타", "e": "🍝", "i": ["버섯", "우유", "양파"],          "t": "20분"},
    {"n": "토마토달걀볶음", "e": "🍅", "i": ["토마토", "계란", "대파"],        "t": "10분"},
    {"n": "감자채볶음",    "e": "🥔", "i": ["감자", "양파"],                  "t": "15분"},
    {"n": "시금치나물",    "e": "🥬", "i": ["시금치"],                        "t": "10분"},
    {"n": "프렌치토스트",  "e": "🍞", "i": ["식빵", "계란", "우유"],          "t": "10분"},
    {"n": "새우볶음밥",    "e": "🍤", "i": ["새우", "밥", "계란", "당근"],    "t": "20분"},
    {"n": "소고기무국",    "e": "🍲", "i": ["소고기", "무", "대파"],          "t": "30분"},
    {"n": "치즈라면",      "e": "🍜", "i": ["치즈", "계란", "대파"],          "t": "8분"},
    {"n": "오이무침",      "e": "🥒", "i": ["오이", "양파"],                  "t": "10분"},
    {"n": "파프리카볶음",  "e": "🫑", "i": ["파프리카", "양파", "돼지고기"],  "t": "15분"},
]

ALLERGY = {
    "유제품": ["우유", "요구르트", "치즈", "버터"],
    "계란": ["계란"], "갑각류": ["새우", "게"], "생선": ["생선", "고등어", "연어"],
    "돼지": ["돼지고기", "햄"], "소": ["소고기"],
    "밀": ["식빵", "만두", "라면", "파스타"], "콩": ["두부", "된장"],
}

# ══════════════════════════════════════════════════════════════
CSS = """
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp {background:linear-gradient(180deg,#EAF4FF 0%,#F3F8FB 40%,#EEF6F4 100%); background-attachment:fixed;}
.block-container {padding:0.45rem 0.75rem 1.1rem !important; max-width:100% !important;}
html, body, [class*="css"], button, input {font-family:'Pretendard','Apple SD Gothic Neo',-apple-system,'Malgun Gothic',sans-serif !important; -webkit-tap-highlight-color:transparent;}
div[data-testid="stVerticalBlock"] {gap:0.3rem !important;}
div[data-testid="stHorizontalBlock"] {gap:0.4rem !important;}
.stElementContainer:has(.sp) {display:none;}

.hd {display:flex; justify-content:space-between; align-items:flex-end; padding:4px 5px 9px;}
.hd-t {font-size:21px; font-weight:900; color:#1F3D37; letter-spacing:-1px; line-height:1.15;}
.hd-s {font-size:11.5px; font-weight:700; color:#8CA09A; margin-top:2px;}
.hd-n {background:#FF6B5A; color:#fff; font-size:11px; font-weight:850; padding:5px 12px; border-radius:99px; box-shadow:0 5px 12px -5px rgba(255,107,90,.8);}
.hd-o {background:#CFE6DE; color:#2C6B5B; font-size:11px; font-weight:850; padding:5px 12px; border-radius:99px;}

.body {background:linear-gradient(180deg,#5C4A3F,#43362E); border-radius:26px; padding:9px; box-shadow:0 18px 38px -20px rgba(50,35,25,.85);}
.top {background:linear-gradient(180deg,#FBFEFF,#EAF4F2); border-radius:19px 19px 9px 9px; padding:9px 0 8px; text-align:center; border:1px solid rgba(255,255,255,.9);}
.lamp {width:52px; height:5px; border-radius:99px; margin:0 auto 6px; background:linear-gradient(90deg,#FFF3C4,#FFE89A,#FFF3C4); box-shadow:0 0 16px 3px rgba(255,228,150,.9);}
.top-t {font-size:9px; font-weight:850; color:#A9BCB6; letter-spacing:3px;}
.gap {height:8px;}
.dr {background:linear-gradient(180deg,rgba(255,255,255,.97),rgba(238,247,245,.95)); border-radius:14px; padding:7px 6px; border:1px solid rgba(255,255,255,.9);}
.drw {background:linear-gradient(180deg,#F6FBFA,#E7F2EF); border-radius:9px 9px 18px 18px; padding:7px 6px 9px; border:1px solid rgba(255,255,255,.9);}
.hdl-l {position:absolute; right:3px; top:18%; width:5px; height:64%; border-radius:99px; background:linear-gradient(180deg,#D9D2CA,#A89C90);}
.seam {width:5px; align-self:stretch; border-radius:99px; background:linear-gradient(180deg,#6B584B,#4A3B32); margin:0 1px;}

div[data-testid="column"] .stButton > button {width:100%; border:none; border-radius:15px; padding:9px 2px; min-height:66px; font-weight:800; font-size:11.5px; line-height:1.45; color:#2B544B; background:linear-gradient(165deg,#FFFFFF,#F1F9F7); box-shadow:0 4px 10px -6px rgba(45,90,80,.55), inset 0 1px 0 #fff; transition:transform .16s cubic-bezier(.3,1.5,.5,1); white-space:pre-line;}
div[data-testid="column"] .stButton > button:hover {transform:translateY(-2px) scale(1.03); color:#0E7A5E;}
div[data-testid="column"] .stButton > button:active {transform:scale(.95);}
.wide .stButton > button {min-height:52px !important; font-size:12px !important;}

.tabbar .stButton > button {min-height:54px !important; padding:6px 0 2px !important; font-size:20px !important; line-height:1.15 !important; border-radius:16px !important; background:#fff !important; color:#8699A2 !important; box-shadow:0 4px 11px -7px rgba(45,80,90,.6) !important; white-space:pre-line !important; font-weight:800 !important;}
.tabbar .stButton > button:hover {color:#2BB49A !important; transform:translateY(-2px) !important;}

.stButton > button[kind="primary"] {background:linear-gradient(135deg,#3FD4B2,#2BB6D6) !important; color:#fff !important; border:none !important; font-weight:850 !important; border-radius:16px !important; padding:12px !important; font-size:14.5px !important; min-height:0 !important; box-shadow:0 9px 18px -9px rgba(43,182,214,.95) !important;}
.stButton > button[kind="secondary"] {background:#fff !important; color:#64756F !important; border:none !important; border-radius:16px !important; font-weight:800 !important; font-size:14px !important; padding:12px !important; min-height:0 !important; box-shadow:0 4px 11px -7px rgba(45,90,80,.5) !important;}
.stButton > button:focus {box-shadow:none !important; outline:none !important;}

.card {background:#fff; border-radius:18px; padding:12px 15px; margin-bottom:7px; box-shadow:0 6px 15px -11px rgba(45,90,80,.65); font-size:12.5px; color:#2F403B; animation:pop .3s cubic-bezier(.3,1.3,.5,1);}
@keyframes pop {from{opacity:0;transform:translateY(8px);} to{opacity:1;transform:none;}}
.gbg {background:#EDF2F0; border-radius:99px; height:7px; overflow:hidden;}
.gfl {height:7px; border-radius:99px; transition:width .6s ease;}
.bdg {display:inline-block; padding:2px 9px; border-radius:99px; font-size:9.5px; font-weight:850; color:#fff;}
.chr {border-radius:50%; display:flex; align-items:center; justify-content:center; position:relative; box-shadow:0 5px 12px -8px rgba(45,90,80,.8); border:2.5px solid #fff;}
.fc {position:absolute; right:-3px; bottom:-4px;}
.wg {animation:wg 2.4s ease-in-out infinite;}
@keyframes wg {0%,100%{transform:rotate(-4deg);} 50%{transform:rotate(4deg);}}
.chip {display:inline-block; background:#EDF8F4; border-radius:99px; padding:3px 10px; margin:3px 4px 0 0; font-size:11px; font-weight:750; color:#1C7A5B;}
.emp {text-align:center; padding:26px 12px; color:#9AAAA5; font-size:12.5px;}
.stTextInput input, .stNumberInput input, .stDateInput input {border-radius:13px !important; border:1.5px solid #E2ECE8 !important; font-size:13.5px !important;}
div[data-baseweb="select"] > div {border-radius:13px !important;}
.stTabs [data-baseweb="tab"] {border-radius:12px; padding:5px 14px; font-size:13px; font-weight:800;}
.stTabs [aria-selected="true"] {background:linear-gradient(135deg,#3FD4B2,#2BB6D6); color:#fff;}
label {font-size:11.5px !important; font-weight:800 !important; color:#64756F !important;}
@media (min-width:520px){.block-container{max-width:460px !important;}}
</style>
"""
if hasattr(st, "html"):
    st.html(CSS)
else:
    st.markdown(CSS, unsafe_allow_html=True)


def H(h):
    st.markdown(" ".join(str(h).split()), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
def guess(name):
    name = (name or "").strip()
    if name in FOOD_DB:
        return FOOD_DB[name]
    for k, v in FOOD_DB.items():
        if k and (k in name or name in k):
            return v
    return ("etc", 7, "📦", "밀폐용기에 담아 3~5일 안에 드세요.")


def _d(v, fb=None):
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str):
        try:
            return dt.date.fromisoformat(v[:10])
        except Exception:
            return fb
    return fb


def sanitize(raw):
    out = []
    for it in (raw if isinstance(raw, list) else []):
        if not isinstance(it, dict):
            continue
        nm = str(it.get("name") or "").strip()
        if not nm:
            continue
        g = guess(nm)
        buy = _d(it.get("buy"), TODAY)
        try:
            tot = int(it.get("total_days"))
        except (TypeError, ValueError):
            tot = int(g[1])
        tot = max(1, min(tot, 3650))
        out.append({
            "id": str(it.get("id") or hashlib.md5(f"{nm}{len(out)}{dt.datetime.now()}".encode()).hexdigest()[:8]),
            "name": nm, "zone": it.get("zone") if it.get("zone") in ZONES else g[0],
            "emoji": str(it.get("emoji") or g[2]), "qty": str(it.get("qty") or "1개"),
            "memo": str(it.get("memo") or ""), "buy": buy.isoformat(),
            "expire": _d(it.get("expire"), buy + dt.timedelta(days=tot)).isoformat(),
            "total_days": tot})
    return out


def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    return {}


def save():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"items": st.session_state.foods, "shopping": st.session_state.shop,
                       "allergies": st.session_state.allg, "seen": st.session_state.seen},
                      f, ensure_ascii=False, indent=1)
    except Exception:
        pass


if "foods" not in st.session_state:
    d0 = load()
    st.session_state.foods = sanitize(d0.get("items"))
    sp = d0.get("shopping")
    st.session_state.shop = [str(x) for x in sp] if isinstance(sp, list) else []
    al = d0.get("allergies")
    st.session_state.allg = [x for x in al if x in ALLERGY] if isinstance(al, list) else []
    st.session_state.seen = bool(d0.get("seen", True))
    st.session_state.scr = "home"
    st.session_state.zone = "veg"
    st.session_state.sel = None
    st.session_state.draft = None
    st.session_state.edit = False


def go(s, **kw):
    st.session_state.scr = s
    for k, v in kw.items():
        st.session_state[k] = v
    st.rerun()


def left(item):
    try:
        e = _d(item.get("expire"))
        return (e - TODAY).days if e else 7
    except Exception:
        return 7


def life(item):
    try:
        tot = max(int(item.get("total_days") or 7), 1)
    except Exception:
        tot = 7
    L = left(item)
    r = max(0.0, min(1.0, L / tot))
    if L < 0:
        return .04, "#A9B2AF", "만료", "💀"
    if L <= 1:
        return max(r, .09), "#F0495A", "위급", "😵"
    if L <= 3:
        return max(r, .24), "#FF8A3D", "임박", "😰"
    if L <= 7:
        return max(r, .45), "#F2C94C", "주의", "🙂"
    return r, "#3CC98A", "신선", "😄"


TINT = {"#3CC98A": "#E2F8EE", "#F2C94C": "#FFF8DD", "#FF8A3D": "#FFEEE1",
        "#F0495A": "#FFE5E8", "#A9B2AF": "#EFF2F1"}


def chr_html(it, s=48):
    _, c, _, f = life(it)
    w = "wg" if left(it) > 3 else ""
    return (f"<div class='chr {w}' style='width:{s}px;height:{s}px;background:{TINT.get(c,'#EEF2F1')};"
            f"border-color:{c};font-size:{int(s*.5)}px;'>{it.get('emoji','📦')}"
            f"<span class='fc' style='font-size:{int(s*.33)}px'>{f}</span></div>")


def gauge(it):
    r, c, lb, _ = life(it)
    L = left(it)
    t = f"D-{L}" if L > 0 else ("오늘까지" if L == 0 else f"{-L}일 지남")
    return (f"<div style='display:flex;justify-content:space-between;font-size:10.5px;"
            f"color:#7C8A85;font-weight:800;margin:4px 0 3px;'><span>{t}</span>"
            f"<span class='bdg' style='background:{c}'>{lb}</span></div>"
            f"<div class='gbg'><div class='gfl' style='width:{r*100:.0f}%;background:{c}'></div></div>")


def allergic(n):
    return None


def add(name, zone, days, emoji, qty, memo, buy):
    buy = _d(buy, TODAY)
    d = max(1, int(days))
    st.session_state.foods.append({
        "id": hashlib.md5(f"{name}{dt.datetime.now()}".encode()).hexdigest()[:8],
        "name": name, "zone": zone if zone in ZONES else "etc", "emoji": emoji or "📦",
        "qty": qty or "1개", "memo": memo or "", "buy": buy.isoformat(),
        "expire": (buy + dt.timedelta(days=d)).isoformat(), "total_days": d})
    save()


def head(t, s=""):
    H(f"<div class='hd'><div><div class='hd-t'>{t}</div><div class='hd-s'>{s}</div></div></div>")


def navbar(to="home"):
    """왼쪽 뒤로 · 오른쪽 넣기"""
    a, b = st.columns(2, gap="small")
    with a:
        if st.button("‹  뒤로", use_container_width=True, key=f"bk{st.session_state.scr}"):
            go(to)
    with b:
        if st.button("＋  넣기", use_container_width=True, type="primary",
                     key=f"ad{st.session_state.scr}"):
            go("add")


# ══════════════════════════════════════════════════════════════
#  홈 — 양문형 냉장고
# ══════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════
def zone():
    z = st.session_state.zone if st.session_state.zone in ZONES else "veg"
    zi = ZONES[z]
    F = sorted([i for i in st.session_state.foods if i.get("zone") == z], key=left)
    head(f"{zi['emoji']} {zi['name']}", f"{len(F)}개")

    if not F:
        H("<div class='card emp'>비어 있어요 🫙</div>")
    for it in F[:6]:
        c1, c2 = st.columns([1, 4.4], gap="small")
        with c1:
            H(f"<div style='padding-top:6px'>{chr_html(it)}</div>")
        with c2:
            H(f"<b style='font-size:14.5px'>{it['name']}</b>"
              f"<span style='font-size:10.5px;color:#9AAAA5;font-weight:700'> {it.get('qty','')}</span>"
              f"{gauge(it)}")
        if st.button("자세히 ›", key=f"d{it['id']}", use_container_width=True):
            go("detail", sel=it["id"], edit=False)
    navbar()




def detail():
    it = next((i for i in st.session_state.foods if i["id"] == st.session_state.sel), None)
    if not it:
        go("home")
    _, c, lb, _ = life(it)
    g = guess(it["name"])
    L = left(it)
    ex = _d(it["expire"], TODAY)
    by = _d(it["buy"], TODAY)
    if L > 1:
        big, msg = f"{L}일 남았어요", "아직 여유 있어요 😄"
    elif L == 1:
        big, msg = "내일까지!", "오늘·내일 중에 드세요 😰"
    elif L == 0:
        big, msg = "오늘까지!", "오늘 안에 꼭 드세요 😵"
    else:
        big, msg = f"{-L}일 지났어요", "상태를 꼭 확인하세요 💀"

    head(f"{it.get('emoji','📦')} {it['name']}", f"{ZONES[it['zone']]['name']} · {lb}")
    c1, c2 = st.columns([1, 3], gap="small")
    with c1:
        H(chr_html(it, 62))
    with c2:
        H(f"<div style='padding-top:9px'>{gauge(it)}</div>")

    H(f"<div class='card' style='text-align:center;padding:15px 12px;"
      f"background:linear-gradient(140deg,{TINT.get(c,'#EEF2F1')},#fff)'>"
      f"<div style='font-size:10.5px;font-weight:850;color:#9AAAA5'>남은 소비기한</div>"
      f"<div style='font-size:28px;font-weight:900;color:{c};letter-spacing:-1.3px;line-height:1.3'>{big}</div>"
      f"<div style='font-size:13px;font-weight:850;color:#44544E'>📅 {ex.year}년 {ex.month}월 {ex.day}일({WD[ex.weekday()]}) 까지</div>"
      f"<div style='font-size:11px;color:#9AAAA5;font-weight:700;margin-top:3px'>{msg}</div></div>")

    H(f"<div class='card' style='line-height:1.8'>"
      f"🗓 <b>등록</b> {by.month}월 {by.day}일 "
      f"<span style='color:#9AAAA5'>({max((TODAY-by).days,0)}일째)</span><br>"
      f"📦 <b>수량</b> {it.get('qty','-')}<br>"
      f"📝 <b>메모</b> {it.get('memo') or '-'}</div>"
      f"<div class='card' style='background:linear-gradient(140deg,#FFFBEC,#FFF5D8)'>"
      f"💡 {g[3]}</div>")

    if allergic(it["name"]):
        st.error(f"🚫 알레르기 주의 — {allergic(it['name'])}")

    a, b = st.columns(2, gap="small")
    with a:
        if st.button("🍽 다 먹음", use_container_width=True):
            st.session_state.foods = [x for x in st.session_state.foods if x["id"] != it["id"]]
            if it["name"] not in st.session_state.shop:
                st.session_state.shop.append(it["name"])
                st.session_state.seen = False
            save()
            go("shop")
    with b:
        if st.button("✏️ 기한 수정", use_container_width=True):
            st.session_state.edit = not st.session_state.edit
            st.rerun()
    if st.session_state.edit:
        nd = st.date_input("새 소비기한", ex)
        if st.button("저장", use_container_width=True, type="primary"):
            it["expire"] = nd.isoformat()
            it["total_days"] = max((nd - by).days, 1)
            st.session_state.edit = False
            save()
            st.rerun()
    navbar("zone")


def recipe():
    F = st.session_state.foods
    have = {i["name"] for i in F}
    urg = {i["name"] for i in F if left(i) <= 3}
    head("오늘 뭐 해먹지", f"급한 재료 {len(urg)}개부터")
    sc = []
    for r in RECIPES:
        if any(allergic(x) for x in r["i"]):
            continue
        hit = [x for x in r["i"] if any(x in h or h in x for h in have)]
        if not hit:
            continue
        ms = [x for x in r["i"] if x not in hit]
        u = sum(1 for x in hit if x in urg)
        sc.append((u * 10 + len(hit) - len(ms) * 2, r, hit, ms, u))
    sc.sort(key=lambda x: -x[0])
    if not sc:
        H("<div class='card emp'>재료를 더 넣어주세요 🥲</div>")
    for _, r, hit, ms, u in sc[:4]:
        tag = "<span class='bdg' style='background:#FF8A3D'>임박</span>" if u else ""
        info = (f"<span style='color:#D1620B;font-size:11px;font-weight:800'>＋{', '.join(ms)}</span>"
                if ms else "<span style='color:#1E9E6A;font-size:11px;font-weight:800'>✓ 다 있어요</span>")
        H(f"<div class='card'><span style='font-size:14.5px;font-weight:850'>{r['e']} {r['n']}</span> {tag}"
          f"<span style='float:right;font-size:10.5px;color:#9AAAA5;font-weight:800'>{r['t']}</span>"
          f"<br>{info}</div>")
        if ms and st.button("🛒 담기", key=f"r{r['n']}", use_container_width=True):
            for m in ms:
                if m not in st.session_state.shop:
                    st.session_state.shop.append(m)
            st.session_state.seen = False
            save()
            st.toast("담았어요 🛒")
    navbar()


def half():
    head("남은 반쪽", "한 번에 다 못 쓰는 재료")
    tg = [i for i in st.session_state.foods
          if i["name"] in HALF or "반" in (i.get("memo") or "")]
    if not tg:
        H("<div class='card emp'>대파·양배추 같은 재료가 없어요 🌿</div>")
    for t in sorted(tg, key=left)[:4]:
        us = [r for r in RECIPES if any(t["name"] in x or x in t["name"] for x in r["i"])]
        ch = "".join(f"<span class='chip'>{r['e']} {r['n']}</span>" for r in us[:4]) or \
             "<span style='font-size:11px;color:#9AAAA5'>자유롭게 활용해 보세요</span>"
        H(f"<div class='card'><span style='font-size:14px;font-weight:850'>{t.get('emoji','📦')} {t['name']}</span>"
          f"<span style='float:right;font-size:10.5px;color:#9AAAA5;font-weight:800'>D-{left(t)}</span>"
          f"<br>{ch}</div>")
    navbar()


def shop():
    head("장보기", f"{len(st.session_state.shop)}개")
    n = st.text_input("", "", placeholder="＋ 살 것 적고 Enter", label_visibility="collapsed")
    if n and n not in st.session_state.shop:
        st.session_state.shop.append(n)
        save()
        st.rerun()
    if not st.session_state.shop:
        H("<div class='card emp'>비었어요 ✨</div>")
    for s in list(st.session_state.shop)[:9]:
        c1, c2 = st.columns([5, 1.1], gap="small")
        with c1:
            H(f"<div class='card' style='margin-bottom:4px;padding:11px 15px'>🛒 <b>{s}</b></div>")
        if c2.button("✓", key=f"s{s}", use_container_width=True):
            st.session_state.shop.remove(s)
            save()
            st.rerun()
    navbar()


def find():
    head("집에 있나?", "마트에서 바로 확인")
    q = st.text_input("", "", placeholder="🔍 재료 이름", label_visibility="collapsed")
    if q:
        hits = [i for i in st.session_state.foods if q in i["name"] or i["name"] in q]
        if hits:
            for h in hits:
                H(f"<div class='card' style='background:linear-gradient(140deg,#E8FBF1,#D9F6E7)'>"
                  f"<span style='font-size:16px;font-weight:900;color:#1C7A5B'>✅ 있어요</span>"
                  f"<span style='float:right;font-size:11.5px;color:#55665F;font-weight:700;padding-top:4px'>"
                  f"{ZONES[h['zone']]['name']} · D-{left(h)}</span></div>")
        else:
            H(f"<div class='card' style='background:linear-gradient(140deg,#FFEFE6,#FFE3D2)'>"
              f"<span style='font-size:16px;font-weight:900;color:#C2410C'>❌ 없어요</span></div>")
            if st.button("🛒 장보기에 담기", use_container_width=True, type="primary"):
                st.session_state.shop.append(q)
                st.session_state.seen = False
                save()
                go("shop")
    navbar()


def setting():
    scene_css()
    head("팁", "재료별 보관법")
    names=list(dict.fromkeys(i["name"] for i in st.session_state.foods))[:5]
    if not names:
        names=["대파","계란","두부","감자"]
    for n in names:
        g=guess(n)
        H(f"<div class='card'><b>{g[2]} {escape(n)}</b><br><span style='font-size:12px'>{g[3]}</span></div>")
    navbar()


# v6: one coherent viewport scene; HTML links are real navigation, not
# disconnected opening/closing tags around Streamlit widgets.
def scene_css():
    st.markdown("""<style>
    header,footer,#MainMenu{display:none!important}
    .stApp{background:#dceee6!important}
    .block-container{max-width:520px!important;padding:12px 18px 24px!important}
    .scene{height:calc(100svh - 30px);min-height:550px;max-height:1000px;position:relative;overflow:hidden;border-radius:32px;background:#eaf3df;font-family:system-ui,sans-serif;color:#254b3d;box-sizing:border-box}
    .scene *{box-sizing:border-box} .scene a{text-decoration:none!important;color:inherit}
    .room{position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent 0 39px,#cadfc655 40px 41px),linear-gradient(#edf3d8 0 77%,#d3b994 77% 100%)}
    .room:after{content:'';position:absolute;left:0;right:0;top:77%;height:9px;background:#ad987b}
    .brand{position:absolute;top:6%;width:100%;text-align:center;z-index:3}
    .brand h1{font-size:64px!important;letter-spacing:-5px;line-height:1!important;margin:0!important;color:#255c47;font-weight:950!important;text-shadow:0 4px #fff7}
    .brand p{font-size:14px;font-weight:700;margin:14px 0;color:#6b8065}
    .closed{position:absolute;left:17%;right:17%;top:30%;bottom:14%;border:7px solid #4b7a66;border-radius:32px;background:#a8d6bc;box-shadow:12px 14px 0 #254b3d22}
    .closed:before,.closed:after{content:'';position:absolute;top:0;bottom:0;width:50%;background:linear-gradient(110deg,#d2ebd3,#a7d3b5);border:2px solid #6a9e80;border-radius:24px}
    .closed:after{right:0}.handles{position:absolute;z-index:2;top:40%;left:43%;font-size:34px;color:#527b64;letter-spacing:6px}
    .magnet{position:absolute;z-index:3;top:22%;left:10%;transform:rotate(-9deg);font-size:38px}
    .start{position:absolute;z-index:4;bottom:5%;left:16%;right:16%;padding:17px;text-align:center;border-radius:22px;background:#ffd178;border:3px solid #927342;box-shadow:0 5px 0 #927342;font-size:20px;font-weight:900}
    .gamehead{position:absolute;top:3%;left:7%;right:7%;display:flex;align-items:center;justify-content:space-between;z-index:3;font-size:24px;font-weight:950}
    .counter{font-size:12px;background:#fff8;padding:7px 12px;border-radius:20px}
    .cabinet{position:absolute;top:12%;bottom:17%;left:15%;right:15%;background:#f8ffed;border:7px solid #6d9a80;border-radius:25px;box-shadow:0 12px 0 #315a4133,inset 0 0 25px #9ab6a244;padding:22px 8px 12px;display:flex;flex-direction:column;gap:8px}
    .light{position:absolute;top:7px;width:40px;height:5px;left:calc(50% - 20px);background:#ffdc76;box-shadow:0 0 16px #ffca44;border-radius:20px}
    .doors{position:absolute;top:13%;bottom:18%;width:12%;background:linear-gradient(90deg,#a0ceb0,#e0eed4);border:4px solid #6d9a80;border-radius:15px;z-index:1}
    .dl{left:3%;transform:skewY(-8deg)}.dr{right:3%;transform:skewY(8deg)}
    .pocket{position:absolute;left:10%;right:10%;height:18%;border:2px solid #95b7a0;border-top-width:5px;background:#ffffff66;border-radius:0 0 8px 8px;text-align:center;padding-top:12px;font-size:20px}
    .shelfrow{display:flex;flex:1;min-height:0;gap:7px;border-bottom:7px solid #b0cbbb;border-radius:8px}
    .foodslot{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;border-radius:13px;background:#ffffff66;position:relative;min-width:0}
    .foodslot:hover{background:#fff;transform:translateY(-2px)}
    .foodslot .emoji{font-size:clamp(28px,5svh,46px);line-height:1.3;filter:drop-shadow(0 4px 0 #0001)}
    .foodslot .label{font-size:12px;font-weight:850;white-space:nowrap;margin-top:3px}
    .foodslot .count{position:absolute;right:4px;top:3px;font-size:10px;border-radius:99px;background:#dcebdc;padding:2px 6px}
    .utility{position:absolute;bottom:4%;left:5%;right:5%;display:flex;justify-content:space-between;gap:6px;z-index:4}
    .utility a{display:flex;align-items:center;justify-content:center;width:16%;height:54px;background:#fff9;border:2px solid #d4e0c7;border-radius:17px;font-size:23px;box-shadow:0 4px 0 #adbea3}
    .addfloat{position:absolute;bottom:12%;left:38%;right:38%;background:#ffd178;border:2px solid #ad8545;border-radius:99px;text-align:center;padding:9px;font-weight:900;z-index:4;box-shadow:0 3px 0 #ad8545}
    .curtain{position:absolute;top:12%;bottom:17%;width:35%;background:#b2d9bc;border:5px solid #6d9a80;z-index:8;animation:dooropen 1s ease-in-out forwards;pointer-events:none;border-radius:18px}
    .curtain.l{left:15%;transform-origin:left}.curtain.r{right:15%;transform-origin:right;animation-name:dooropenr}
    @keyframes dooropen{to{transform:perspective(600px) rotateY(-105deg);opacity:0}}
    @keyframes dooropenr{to{transform:perspective(600px) rotateY(105deg);opacity:0}}
    .fadebrand{position:absolute;inset:40% 0 auto;text-align:center;font-size:42px;font-weight:950;z-index:9;animation:fadeaway .65s forwards;pointer-events:none;color:#315c45}
    @keyframes fadeaway{to{opacity:0;transform:translateY(-15px)}}
    div[data-testid='stHorizontalBlock']{flex-wrap:nowrap!important}
    div[data-testid='stColumn']{min-width:0!important}
    .step-title{font-size:29px;font-weight:900;letter-spacing:-1px;margin:32px 0 24px;color:#28513e}
    .step-label{font-size:12px;font-weight:800;color:#799783;margin-top:20px}
    .stButton button[kind='primary'],.stFormSubmitButton button[kind='primary']{background:#418266!important;color:white!important}
    @media(max-width:520px){.block-container{padding:0!important}.scene{border-radius:0;height:100svh;max-height:none}.stMainBlockContainer:has(.step-title){padding:22px!important}}
    @media(prefers-reduced-motion:reduce){.curtain,.fadebrand{animation-duration:.01ms}}
    </style>""",unsafe_allow_html=True)


def lobby():
    scene_css()
    H("<div class='scene'><div class='room'></div><div class='brand'><h1>냉큼</h1><p>있는 재료로, 맛있는 오늘.</p></div><div class='closed'><span class='handles'>┃┃</span></div><a class='start' href='?view=home&amp;enter=1' target='_self'>냉장고 열기 →</a></div>")


def home():
    scene_css()
    F=st.session_state.foods
    def slot(z):
        zi=ZONES[z]; n=sum(i['zone']==z for i in F)
        return f"<a class='foodslot' href='?view=zone&amp;zone={z}' target='_self'><span class='count'>{n}</span><span class='emoji'>{zi['emoji']}</span><span class='label'>{zi['name']}</span></a>"
    rows=''.join("<div class='shelfrow'>"+slot(a)+slot(b)+"</div>" for a,b in [('dairy','meat'),('side','frozen'),('veg','fruit')])
    rows+="<div class='shelfrow'>"+slot('etc')+"</div>"
    tools=''.join(f"<a href='?view={v}' target='_self' aria-label='{t}' title='{t}'>{e}</a>" for v,e,t in [('recipe','🍳','레시피'),('half','🥢','남은 반쪽'),('find','🔍','재고 검색'),('shop','📝','장보기'),('set','💡','팁'),('lobby','🏠','로비')])
    anim="<div class='curtain l'></div><div class='curtain r'></div><div class='fadebrand'>냉큼</div>" if st.query_params.get('enter')=='1' else ''
    H(f"<div class='scene'><div class='room'></div><div class='gamehead'><span>냉큼</span><span class='counter'>재료 {len(F)}</span></div><div class='doors dl'></div><div class='doors dr'></div><div class='cabinet'><div class='light'></div>{rows}</div><a class='addfloat' href='?view=add' target='_self'>＋ 넣기</a><div class='utility'>{tools}</div>{anim}</div>")


old_go=go
def go(s,**kw):
    st.query_params.clear()
    old_go(s,**kw)


def addscr():
    scene_css()
    if 'wizard' not in st.session_state:
        st.session_state.wizard={'step':0,'name':'','zone':st.session_state.zone,'qty':'1개','buy':TODAY,'expire':None,'memo':''}
    w=st.session_state.wizard
    step=w['step']
    titles=['무엇을 넣을까요?','어느 칸에 둘까요?','얼마나 남았나요?','언제까지인가요?','이대로 넣을까요?']
    H(f"<div class='step-label'>재료 넣기 · {step+1} / 5</div><div class='step-title'>{titles[step]}</div>")
    st.progress((step+1)/5)
    valid=True
    if step==0:
        examples={'dairy':'우유, 치즈','meat':'닭고기, 소고기','veg':'대파, 당근','fruit':'사과, 딸기','side':'김치, 두부','frozen':'만두, 새우','etc':'소스, 음료'}
        w['name']=st.text_input('재료 이름',value=w['name'],key='wizname',placeholder='예: '+examples.get(w['zone'],'소스, 음료'))
        valid=bool(w['name'].strip())
    elif step==1:
        w['zone']=st.selectbox('보관 칸',ZKEYS,index=ZKEYS.index(w['zone']) if w['zone'] in ZKEYS else 6,format_func=lambda k:ZONES[k]['emoji']+' '+ZONES[k]['name'])
    elif step==2:
        w['qty']=st.text_input('남은 양',w['qty'],placeholder='예: 반 개, 200g')
    elif step==3:
        w['expire']=st.date_input('소비기한',w['expire'] or TODAY)
        st.caption('제품에 표시된 소비기한을 확인해주세요.')
    else:
        H(f"<div class='card'><h2>{escape(w['name'])}</h2>{ZONES[w['zone']]['emoji']} {ZONES[w['zone']]['name']} · {escape(w['qty'])}<br>📅 {w['expire'].isoformat()}까지</div>")
    st.write('')
    a,b=st.columns(2)
    with a:
        if st.button('‹ 뒤로',use_container_width=True):
            if step==0:
                del st.session_state.wizard
                go('home')
            else:
                w['step']-=1;st.rerun()
    with b:
        if st.button('넣기 ✓' if step==4 else '다음 →',type='primary',use_container_width=True,disabled=not valid):
            if step<4:
                w['step']+=1;st.rerun()
            else:
                g=guess(w['name'])
                w['buy']=TODAY
                add(w['name'].strip(),w['zone'],max((w['expire']-w['buy']).days,1),g[2],w['qty'],'',w['buy'])
                st.session_state.foods[-1]['expire']=w['expire'].isoformat()
                save();del st.session_state.wizard
                st.session_state.pop('wizname',None)
                go('home')

# Query links persist across reloads, while regular widgets use session routing.
qview=st.query_params.get('view')
if qview in {'home','zone','add','recipe','half','find','shop','set','lobby'}:
    st.session_state.scr=qview
    if qview=='zone' and st.query_params.get('zone') in ZONES:
        st.session_state.zone=st.query_params['zone']
if 'has_started' not in st.session_state:
    st.session_state.has_started=True
    if not qview: st.session_state.scr='lobby'
SCR = {'lobby':lobby,'home':home,'zone':zone,'add':addscr,'detail':detail,
       'recipe':recipe,'half':half,'shop':shop,'find':find,'set':setting}
SCR.get(st.session_state.get('scr','lobby'),lobby)()
