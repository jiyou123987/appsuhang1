# -*- coding: utf-8 -*-
"""
우리집 냉장고 (My Family Fridge) — v2
Streamlit 단일 파일 · 모바일 세로형 · 한 화면 = 한 기능
"""

import os
import json
import base64
import hashlib
import datetime as dt

import streamlit as st

st.set_page_config(page_title="우리집 냉장고", page_icon="🧊",
                   layout="centered", initial_sidebar_state="collapsed")

DATA_FILE = "fridge_data.json"
TODAY = dt.date.today()

ZONES = {
    "veg":    {"name": "야채칸",   "emoji": "🥬", "c1": "#D7F2DF", "c2": "#B2E5C4"},
    "meat":   {"name": "고기칸",   "emoji": "🥩", "c1": "#FFE0E2", "c2": "#FFC2C7"},
    "dairy":  {"name": "유제품칸", "emoji": "🥛", "c1": "#E2EEFF", "c2": "#C4DCFF"},
    "fruit":  {"name": "과일칸",   "emoji": "🍎", "c1": "#FFEBD6", "c2": "#FFD4AE"},
    "side":   {"name": "반찬칸",   "emoji": "🍱", "c1": "#FFF6D1", "c2": "#FFE89B"},
    "frozen": {"name": "냉동칸",   "emoji": "🧊", "c1": "#E0F4FA", "c2": "#BEE8F4"},
}
ZKEYS = list(ZONES.keys())

FOOD_DB = {
    "우유":     ("dairy", 7,  "🥛", "개봉 후엔 도어칸 말고 안쪽 선반에. 문쪽은 온도가 들쭉날쭉해요."),
    "요구르트": ("dairy", 14, "🥤", "뚜껑을 꼭 닫아 냄새 흡수를 막아주세요."),
    "치즈":     ("dairy", 21, "🧀", "랩 대신 종이포일로 싸면 덜 눅눅해져요."),
    "버터":     ("dairy", 60, "🧈", "냄새를 잘 먹어요. 밀폐용기에 따로 보관하세요."),
    "계란":     ("dairy", 21, "🥚", "뾰족한 쪽을 아래로 두면 더 오래가요. 씻지 말고 넣기."),
    "두부":     ("side",  5,  "🧊", "남으면 물에 잠기게 담가 매일 물을 갈아주세요."),
    "대파":     ("veg",   10, "🌿", "송송 썰어 지퍼백에 얼리면 2개월! 흰 부분은 따로."),
    "양파":     ("veg",   30, "🧅", "통째로는 실온 망에. 깐 건 밀폐해서 냉장."),
    "당근":     ("veg",   21, "🥕", "신문지에 싸서 세워두면 수분이 덜 빠져요."),
    "감자":     ("veg",   30, "🥔", "냉장은 금지! 사과 한 알과 함께 어두운 실온에."),
    "애호박":   ("veg",   10, "🥒", "자른 단면에 랩을 밀착시켜 주세요."),
    "양배추":   ("veg",   14, "🥬", "심을 파내고 젖은 키친타월을 끼워두면 오래가요."),
    "시금치":   ("veg",   5,  "🥬", "세워서 보관. 눕히면 금방 물러요."),
    "버섯":     ("veg",   7,  "🍄", "씻지 말고 종이봉투에. 물기가 최대의 적이에요."),
    "무":       ("veg",   21, "🥗", "잎을 잘라내고 신문지에 싸서 세워두세요."),
    "토마토":   ("fruit", 7,  "🍅", "꼭지를 아래로. 덜 익었으면 실온에 두세요."),
    "사과":     ("fruit", 21, "🍎", "에틸렌이 나와요. 다른 채소와 꼭 분리!"),
    "바나나":   ("fruit", 5,  "🍌", "냉장 금지. 꼭지를 랩으로 감싸면 며칠 더 버텨요."),
    "딸기":     ("fruit", 3,  "🍓", "먹기 직전에 씻기. 키친타월 깔고 한 겹만."),
    "포도":     ("fruit", 7,  "🍇", "씻지 않은 채로 통풍되는 용기에."),
    "닭고기":   ("meat",  2,  "🍗", "핏물을 닦고 한 끼씩 소분해 냉동하면 안전해요."),
    "돼지고기": ("meat",  3,  "🥓", "공기를 빼고 밀착 포장. 3일 넘기면 냉동으로."),
    "소고기":   ("meat",  3,  "🥩", "키친타월로 핏물 제거 후 랩 밀착 포장."),
    "생선":     ("meat",  2,  "🐟", "내장을 빼고 물기를 닦아 랩+지퍼백 이중으로."),
    "새우":     ("frozen",30, "🦐", "해동은 냉장실에서 천천히. 재냉동은 금물."),
    "만두":     ("frozen",90, "🥟", "서로 붙지 않게 펼쳐 얼린 뒤 봉지에 모아주세요."),
    "김치":     ("side",  60, "🥬", "공기 접촉이 산패의 원인. 꾹 눌러 국물에 잠기게."),
    "햄":       ("side",  14, "🍖", "개봉 후엔 밀폐용기로 옮겨 담아주세요."),
    "밥":       ("side",  2,  "🍚", "따뜻할 때 한 공기씩 랩에 싸서 냉동하면 갓 지은 맛."),
    "식빵":     ("side",  5,  "🍞", "냉장은 오히려 노화를 촉진해요. 냉동 후 바로 구우세요."),
}
HALF_FOODS = {"대파", "양배추", "두부", "애호박", "당근", "양파", "무", "식빵"}

RECIPES = [
    {"name": "계란찜",        "emoji": "🍳", "ing": ["계란", "대파"],                  "time": "10분"},
    {"name": "파기름 볶음밥",  "emoji": "🍚", "ing": ["대파", "밥", "계란"],            "time": "15분"},
    {"name": "두부김치",      "emoji": "🥬", "ing": ["두부", "김치", "돼지고기"],      "time": "20분"},
    {"name": "된장찌개",      "emoji": "🍲", "ing": ["두부", "애호박", "양파", "감자"], "time": "25분"},
    {"name": "양배추전",      "emoji": "🥞", "ing": ["양배추", "계란"],                "time": "15분"},
    {"name": "닭볶음탕",      "emoji": "🍗", "ing": ["닭고기", "감자", "당근", "양파"], "time": "40분"},
    {"name": "제육볶음",      "emoji": "🥓", "ing": ["돼지고기", "양파", "대파"],      "time": "25분"},
    {"name": "버섯크림파스타", "emoji": "🍝", "ing": ["버섯", "우유", "양파"],          "time": "20분"},
    {"name": "토마토달걀볶음", "emoji": "🍅", "ing": ["토마토", "계란", "대파"],        "time": "10분"},
    {"name": "감자채볶음",    "emoji": "🥔", "ing": ["감자", "양파"],                  "time": "15분"},
    {"name": "시금치나물",    "emoji": "🥬", "ing": ["시금치"],                        "time": "10분"},
    {"name": "프렌치토스트",  "emoji": "🍞", "ing": ["식빵", "계란", "우유"],          "time": "10분"},
    {"name": "새우볶음밥",    "emoji": "🍤", "ing": ["새우", "밥", "계란", "당근"],    "time": "20분"},
    {"name": "소고기무국",    "emoji": "🍲", "ing": ["소고기", "무", "대파"],          "time": "30분"},
    {"name": "치즈라면",      "emoji": "🍜", "ing": ["치즈", "계란", "대파"],          "time": "8분"},
]

ALLERGY_MAP = {
    "우유/유제품": ["우유", "요구르트", "치즈", "버터"],
    "계란":        ["계란"],
    "갑각류":      ["새우", "게", "랍스터"],
    "생선":        ["생선", "고등어", "연어"],
    "돼지고기":    ["돼지고기", "햄", "베이컨"],
    "소고기":      ["소고기"],
    "밀/글루텐":   ["식빵", "만두", "라면", "파스타"],
    "콩":          ["두부", "된장"],
}

# ──────────────────────────────────────────────────────────────
# 디자인
# ──────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" rel="stylesheet">
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp {
  background:
    radial-gradient(1000px 420px at 12% -8%, #FFF2D9 0%, transparent 58%),
    radial-gradient(900px 480px at 92% 6%, #DDF4FF 0%, transparent 60%),
    linear-gradient(180deg,#FDFBF6 0%, #F2F7F5 100%);
  background-attachment: fixed;
}
.block-container{ padding:0.55rem 0.7rem 0.5rem !important; max-width:430px !important; }
@media (max-width:480px){ .block-container{max-width:100% !important; padding:0.4rem 0.55rem !important;} }
html, body, [class*="css"], button, input, textarea {
  font-family:'Pretendard','Apple SD Gothic Neo',-apple-system,sans-serif !important;
  -webkit-tap-highlight-color: transparent;
}
h1,h2,h3{letter-spacing:-0.6px;}

/* ── 상단바 ── */
.topbar{
  position:relative; overflow:hidden;
  background:linear-gradient(135deg,#8FE3C8 0%,#6FD3D8 55%,#7FC4F0 100%);
  border-radius:24px; padding:13px 17px; margin-bottom:11px;
  box-shadow:0 8px 22px -8px rgba(79,187,180,.65);
}
.topbar:after{
  content:''; position:absolute; right:-24px; top:-34px;
  width:118px; height:118px; border-radius:50%; background:rgba(255,255,255,.17);
}
.tb-t{color:#fff; font-weight:800; font-size:18.5px; letter-spacing:-0.7px;
      text-shadow:0 1px 3px rgba(0,80,70,.18);}
.tb-s{color:rgba(255,255,255,.93); font-weight:600; font-size:11.5px; margin-top:2px;}

/* ── 냉장고 몸체 ── */
.fridge{
  background:linear-gradient(170deg,#FFFFFF 0%,#F2F8F6 100%);
  border:1.5px solid rgba(255,255,255,.9);
  border-radius:30px; padding:13px 10px 9px;
  box-shadow:0 14px 34px -16px rgba(60,110,100,.4), inset 0 1px 0 #fff;
}
.handle{
  width:42px; height:5px; border-radius:99px; margin:0 auto 10px;
  background:linear-gradient(90deg,#D6E5E0,#BFD6CF);
}

/* ── 칸 버튼 ── */
div[data-testid="column"] .stButton > button{
  width:100%; border:none; border-radius:22px;
  padding:13px 4px 11px; min-height:86px;
  font-weight:800; font-size:13px; line-height:1.45; color:#245247;
  background:linear-gradient(160deg,#FFFFFF 0%,#F4FAF8 100%);
  box-shadow:0 5px 14px -6px rgba(60,110,100,.35), inset 0 0 0 1.5px rgba(255,255,255,.9);
  transition:transform .16s cubic-bezier(.3,1.4,.5,1), box-shadow .16s;
  white-space:pre-line;
}
div[data-testid="column"] .stButton > button:hover{
  transform:translateY(-3px) scale(1.02);
  box-shadow:0 10px 22px -8px rgba(60,110,100,.45);
}
div[data-testid="column"] .stButton > button:active{ transform:scale(.97); }

/* ── 사이드 아이콘 ── */
.sideicon .stButton > button{
  min-height:46px !important; padding:0 !important; font-size:19px !important;
  border-radius:17px !important; font-weight:600 !important;
  background:linear-gradient(160deg,#FFFDF5,#FFF6DF) !important;
  box-shadow:0 4px 11px -5px rgba(190,150,60,.5), inset 0 0 0 1.5px rgba(255,255,255,.95) !important;
  color:#6b5a28 !important;
}
.sideicon .stButton > button:hover{ transform:translateY(-2px) scale(1.05); }

/* ── 주요 버튼 ── */
.stButton > button[kind="primary"]{
  background:linear-gradient(135deg,#59D2B0,#45C0CC) !important;
  color:#fff !important; border:none !important; font-weight:800 !important;
  border-radius:18px !important; padding:11px !important; font-size:14px !important;
  box-shadow:0 7px 18px -7px rgba(69,192,204,.85) !important;
}
.stButton > button[kind="secondary"]{
  background:rgba(255,255,255,.88) !important; color:#5b6b66 !important;
  border:none !important; border-radius:16px !important; font-weight:700 !important;
  font-size:13px !important; box-shadow:0 3px 10px -5px rgba(60,110,100,.4) !important;
}
.stButton > button:focus{ box-shadow:none !important; outline:none !important; }

/* ── 카드 ── */
.card{
  background:rgba(255,255,255,.93); border-radius:20px; padding:12px 14px; margin-bottom:8px;
  box-shadow:0 6px 18px -10px rgba(60,110,100,.45), inset 0 0 0 1.2px rgba(255,255,255,.9);
  font-size:13px; color:#33433e; animation:pop .3s cubic-bezier(.3,1.3,.5,1);
}
@keyframes pop{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}

/* ── 게이지 ── */
.gbg{background:#EDF2F0; border-radius:99px; height:8px; overflow:hidden;
     box-shadow:inset 0 1px 2px rgba(0,0,0,.07);}
.gfl{height:8px; border-radius:99px; transition:width .5s ease;}
.badge{display:inline-block; padding:2px 9px; border-radius:99px;
       font-size:10px; font-weight:800; color:#fff; letter-spacing:-.2px;}

/* ── 캐릭터 ── */
.chr{border-radius:50%; display:flex; align-items:center; justify-content:center;
     position:relative; box-shadow:0 5px 13px -5px rgba(60,110,100,.55);
     border:2.5px solid #fff;}
.chr .face{position:absolute; right:-2px; bottom:-3px;}
.wiggle{animation:wig 1.9s ease-in-out infinite;}
@keyframes wig{0%,100%{transform:rotate(-4deg)}50%{transform:rotate(4deg)}}

.hint{font-size:11px; color:#92a09b; text-align:center; margin-top:7px; font-weight:600;}
.empty{text-align:center; padding:26px 12px; color:#8a9793; font-size:13px;}
.stTextInput input, .stNumberInput input, .stDateInput input{
  border-radius:14px !important; border:1.5px solid #E3EDE9 !important;
  background:#fff !important; font-size:13.5px !important;
}
div[data-baseweb="select"] > div{border-radius:14px !important; border-color:#E3EDE9 !important;}
.stTabs [data-baseweb="tab-list"]{gap:6px;}
.stTabs [data-baseweb="tab"]{
  border-radius:14px; padding:6px 14px; font-size:13px; font-weight:700;
  background:rgba(255,255,255,.75);
}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#59D2B0,#45C0CC); color:#fff;}
label{font-size:12px !important; font-weight:700 !important; color:#5b6b66 !important;}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 데이터 — 모든 로드 값을 검증·보정 (TypeError 원인 제거)
# ──────────────────────────────────────────────────────────────
def _d(v, fb=None):
    """어떤 값이든 안전하게 date 로 변환"""
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str):
        try:
            return dt.date.fromisoformat(v[:10])
        except Exception:
            return fb
    return fb


def sanitize(raw):
    """저장본/구버전 데이터를 현재 스키마로 보정. 못 고치면 버림."""
    out = []
    for it in (raw if isinstance(raw, list) else []):
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        g = FOOD_DB.get(name) or guess_food(name)
        buy = _d(it.get("buy"), TODAY)
        total = it.get("total_days")
        try:
            total = int(total)
        except (TypeError, ValueError):
            total = int(g[1])
        total = max(1, min(total, 3650))
        exp = _d(it.get("expire"), buy + dt.timedelta(days=total))
        zone = it.get("zone") if it.get("zone") in ZONES else g[0]
        out.append({
            "id": str(it.get("id") or hashlib.md5(
                f"{name}{len(out)}{dt.datetime.now()}".encode()).hexdigest()[:8]),
            "name": name, "zone": zone, "emoji": str(it.get("emoji") or g[2]),
            "qty": str(it.get("qty") or "1개"), "memo": str(it.get("memo") or ""),
            "buy": buy.isoformat(), "expire": exp.isoformat(), "total_days": total,
        })
    return out


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    return {}


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"items": st.session_state.items,
                       "shopping": st.session_state.shopping,
                       "allergies": st.session_state.allergies,
                       "seen_shopping": st.session_state.seen_shopping},
                      f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def guess_food(name):
    name = (name or "").strip()
    if name in FOOD_DB:
        return FOOD_DB[name]
    for k, v in FOOD_DB.items():
        if k and (k in name or name in k):
            return v
    return ("side", 7, "🍽️", "밀폐용기에 담아 냉장 보관하고 3~5일 안에 드세요.")


if "items" not in st.session_state:
    d = load_data()
    st.session_state.items = sanitize(d.get("items"))
    sp = d.get("shopping")
    st.session_state.shopping = [str(x) for x in sp] if isinstance(sp, list) else []
    al = d.get("allergies")
    st.session_state.allergies = [x for x in al if x in ALLERGY_MAP] if isinstance(al, list) else []
    st.session_state.seen_shopping = bool(d.get("seen_shopping", True))
    st.session_state.screen = "home"
    st.session_state.zone = "veg"
    st.session_state.sel = None
    st.session_state.draft = None
    st.session_state.imgcache = {}
    st.session_state.edit = False


def go(screen, **kw):
    st.session_state.screen = screen
    for k, v in kw.items():
        st.session_state[k] = v
    st.rerun()


# ──────────────────────────────────────────────────────────────
# 계산 유틸 — 전부 방어적
# ──────────────────────────────────────────────────────────────
def days_left(item):
    try:
        e = _d(item.get("expire"))
        if e is None:
            return 7
        return (e - TODAY).days
    except Exception:
        return 7


def life_info(item):
    try:
        total = max(int(item.get("total_days") or 7), 1)
    except Exception:
        total = 7
    left = days_left(item)
    ratio = max(0.0, min(1.0, left / total))
    if left < 0:
        return 0.04, "#A9B2AF", "만료", "💀"
    if left <= 1:
        return max(ratio, .09), "#F0495A", "위급", "😵"
    if left <= 3:
        return max(ratio, .24), "#FF8A3D", "임박", "😰"
    if left <= 7:
        return max(ratio, .45), "#F2C94C", "주의", "🙂"
    return ratio, "#3CC98A", "신선", "😄"


TINT = {"#3CC98A": "#E2F8EE", "#F2C94C": "#FFF8DD", "#FF8A3D": "#FFEEE1",
        "#F0495A": "#FFE5E8", "#A9B2AF": "#EFF2F1"}


def char_html(item, size=48):
    _, color, _, face = life_info(item)
    url = st.session_state.imgcache.get(item.get("name"))
    wig = "wiggle" if days_left(item) > 3 else ""
    if url:
        return (f"<img class='{wig}' src='{url}' style='width:{size}px;height:{size}px;"
                f"border-radius:50%;object-fit:cover;border:2.5px solid {color};'>")
    return (f"<div class='chr {wig}' style='width:{size}px;height:{size}px;"
            f"background:{TINT.get(color,'#EEF2F1')};border-color:{color};"
            f"font-size:{int(size*.5)}px;'>{item.get('emoji','🍽️')}"
            f"<span class='face' style='font-size:{int(size*.33)}px'>{face}</span></div>")


def gauge_html(item):
    ratio, color, label, _ = life_info(item)
    left = days_left(item)
    txt = f"D-{left}" if left > 0 else ("오늘까지!" if left == 0 else f"{-left}일 지남")
    return (f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"font-size:11px;color:#7c8a85;font-weight:700;margin:4px 0 3px;'>"
            f"<span>{txt}</span><span class='badge' style='background:{color}'>{label}</span></div>"
            f"<div class='gbg'><div class='gfl' style='width:{ratio*100:.0f}%;"
            f"background:linear-gradient(90deg,{color},{color}cc)'></div></div>")


def blocked_by_allergy(name):
    name = name or ""
    for a in st.session_state.allergies:
        for bad in ALLERGY_MAP.get(a, []):
            if bad in name or name in bad:
                return a
    return None


def ai_key():
    try:
        k = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        k = ""
    return k or os.environ.get("OPENAI_API_KEY", "")


def ai_recognize(image_bytes):
    key = ai_key()
    if not key:
        return None
    try:
        from openai import OpenAI
        c = OpenAI(api_key=key)
        b64 = base64.b64encode(image_bytes).decode()
        r = c.chat.completions.create(
            model="gpt-4o-mini", max_tokens=120,
            messages=[{"role": "user", "content": [
                {"type": "text", "text":
                 "사진 속 식재료를 식별해 JSON만 출력. "
                 '{"name":"한국어 재료명","zone":"veg|meat|dairy|fruit|side|frozen",'
                 '"days":숫자,"emoji":"이모지1개"}'},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}])
        t = r.choices[0].message.content.strip()
        o = json.loads(t[t.find("{"): t.rfind("}") + 1])
        return {"name": str(o.get("name", "")),
                "zone": o.get("zone") if o.get("zone") in ZONES else "side",
                "days": int(o.get("days", 7)), "emoji": str(o.get("emoji", "🍽️"))}
    except Exception:
        return None


def ai_character(name):
    key = ai_key()
    if not key or not name or name in st.session_state.imgcache:
        return
    try:
        from openai import OpenAI
        c = OpenAI(api_key=key)
        r = c.images.generate(
            model="gpt-image-1", size="1024x1024",
            prompt=(f"귀엽고 동글동글한 '{name}' 캐릭터 마스코트, 연한 민트색 배경, "
                    "심플한 플랫 일러스트, 큰 눈과 웃는 얼굴, 글자 없음, 정중앙 배치"))
        st.session_state.imgcache[name] = "data:image/png;base64," + r.data[0].b64_json
    except Exception:
        pass


def add_item(name, zone, total_days, emoji, qty, memo, buy):
    buy = _d(buy, TODAY)
    total = max(1, int(total_days))
    st.session_state.items.append({
        "id": hashlib.md5(f"{name}{dt.datetime.now()}".encode()).hexdigest()[:8],
        "name": name, "zone": zone if zone in ZONES else "side", "emoji": emoji or "🍽️",
        "qty": qty or "1개", "memo": memo or "", "buy": buy.isoformat(),
        "expire": (buy + dt.timedelta(days=total)).isoformat(), "total_days": total})
    save_data()


def topbar(title, sub=""):
    st.markdown(f"<div class='topbar'><div class='tb-t'>{title}</div>"
                f"<div class='tb-s'>{sub}</div></div>", unsafe_allow_html=True)


def back(to="home"):
    if st.button("‹  뒤로", use_container_width=True, key=f"bk_{st.session_state.screen}"):
        go(to)


# ──────────────────────────────────────────────────────────────
# 홈
# ──────────────────────────────────────────────────────────────
def screen_home():
    items = st.session_state.items
    urg = [i for i in items if days_left(i) <= 3]
    sub = f"재료 {len(items)}개" + (f" · 서두를 재료 {len(urg)}개 ⚠️" if urg else " · 모두 신선해요 ✨")
    topbar("우리집 냉장고 🧊", sub)

    side, main = st.columns([1, 4.5], gap="small")
    with side:
        st.markdown("<div class='sideicon'>", unsafe_allow_html=True)
        if st.button("🍳", key="s1", help="임박 재료 우선 레시피", use_container_width=True):
            go("recipe")
        if st.button("🥢", key="s2", help="남은 반쪽 소비 레시피", use_container_width=True):
            go("half")
        mk = "❗" if (st.session_state.shopping and not st.session_state.seen_shopping) else "📝"
        if st.button(mk, key="s3", help="장보기 메모", use_container_width=True):
            st.session_state.seen_shopping = True
            save_data()
            go("shop")
        if st.button("🔍", key="s4", help="집에 이거 있나? 확인", use_container_width=True):
            go("find")
        if st.button("🚫", key="s5", help="알레르기 설정", use_container_width=True):
            go("allergy")
        if st.button("💡", key="s6", help="보관법 팁", use_container_width=True):
            go("tips")
        st.markdown("</div>", unsafe_allow_html=True)

    with main:
        st.markdown("<div class='fridge'><div class='handle'></div>", unsafe_allow_html=True)
        for row in range(3):
            cols = st.columns(2, gap="small")
            for j in range(2):
                z = ZKEYS[row * 2 + j]
                zi = ZONES[z]
                n = sum(1 for i in items if i.get("zone") == z)
                w = sum(1 for i in items if i.get("zone") == z and days_left(i) <= 3)
                tail = f"{n}개" + (f"  ❗{w}" if w else "")
                with cols[j]:
                    if st.button(f"{zi['emoji']}\n{zi['name']}\n{tail}",
                                 key=f"z{z}", use_container_width=True):
                        go("zone", zone=z)
        st.markdown("</div>", unsafe_allow_html=True)
        st.write("")
        if st.button("＋  재료 넣기", use_container_width=True, type="primary", key="addm"):
            go("add", zone="veg")

    st.markdown("<div class='hint'>칸을 눌러 재료 보기 · 왼쪽은 기능 버튼</div>",
                unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 칸 상세
# ──────────────────────────────────────────────────────────────
def screen_zone():
    z = st.session_state.zone if st.session_state.zone in ZONES else "veg"
    zi = ZONES[z]
    items = sorted([i for i in st.session_state.items if i.get("zone") == z], key=days_left)
    topbar(f"{zi['emoji']} {zi['name']}", f"{len(items)}개 보관 중 · 급한 것부터 보여드려요")

    if not items:
        st.markdown("<div class='card empty'>텅 비었어요 🫙<br>"
                    "<span style='font-size:11.5px'>아래에서 재료를 넣어보세요</span></div>",
                    unsafe_allow_html=True)
    for it in items[:5]:
        c1, c2 = st.columns([1, 4.3], gap="small")
        with c1:
            st.markdown(f"<div style='padding-top:7px'>{char_html(it)}</div>",
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f"<b style='font-size:14px'>{it['name']}</b>"
                        f"<span style='font-size:11px;color:#94a19c;font-weight:600'> "
                        f"{it.get('qty','')}</span>{gauge_html(it)}", unsafe_allow_html=True)
        if st.button("상세 보기 ›", key=f"d{it['id']}", use_container_width=True):
            go("detail", sel=it["id"], edit=False)
    if len(items) > 5:
        st.markdown(f"<div class='hint'>외 {len(items)-5}개 더 있어요</div>",
                    unsafe_allow_html=True)

    a, b = st.columns(2, gap="small")
    with a:
        if st.button("＋ 넣기", use_container_width=True, type="primary", key="addz"):
            go("add", zone=z)
    with b:
        back()


# ──────────────────────────────────────────────────────────────
# 재료 넣기
# ──────────────────────────────────────────────────────────────
def screen_add():
    topbar("재료 넣기 ＋", "사진을 올리면 자동으로 채워져요")
    tab1, tab2 = st.tabs(["📷 사진으로", "✍️ 직접"])

    with tab1:
        up = st.file_uploader("사진", type=["jpg", "jpeg", "png"],
                              label_visibility="collapsed", key="up")
        if up and st.button("🔎 자동 인식", use_container_width=True, type="primary"):
            with st.spinner("사진을 보는 중…"):
                r = ai_recognize(up.getvalue())
            if r and r.get("name"):
                st.session_state.draft = r
                st.success(f"‘{r['name']}’ 같아요! 아래에서 고칠 수 있어요")
            else:
                st.info("자동 인식이 안 됐어요. 아래에 직접 적어주세요"
                        if ai_key() else "사진 인식은 OPENAI_API_KEY가 있을 때 작동해요")

    with tab2:
        pick = st.selectbox("빠른 선택", ["직접 입력"] + list(FOOD_DB.keys()),
                            label_visibility="collapsed")
        if pick != "직접 입력":
            z, d, e, _ = FOOD_DB[pick]
            st.session_state.draft = {"name": pick, "zone": z, "days": d, "emoji": e}

    df = st.session_state.draft or {"name": "", "zone": st.session_state.zone,
                                    "days": 7, "emoji": "🍽️"}
    with st.form("fadd"):
        name = st.text_input("이름", df.get("name", ""), placeholder="예) 대파")
        c1, c2 = st.columns(2)
        zi = ZKEYS.index(df["zone"]) if df.get("zone") in ZONES else 0
        zone = c1.selectbox("칸", ZKEYS, index=zi,
                            format_func=lambda k: f"{ZONES[k]['emoji']} {ZONES[k]['name']}")
        qty = c2.text_input("수량", "1개")
        c3, c4 = st.columns(2)
        buy = c3.date_input("구입일", TODAY)
        days = c4.number_input("소비기한(일)", 1, 1000, int(df.get("days", 7) or 7))
        memo = st.text_input("메모", "", placeholder="개봉함 / 반만 씀")
        ok = st.form_submit_button("냉장고에 넣기 🧊", use_container_width=True, type="primary")

    if ok:
        if not name.strip():
            st.error("이름을 적어주세요")
        else:
            nm = name.strip()
            g = guess_food(nm)
            add_item(nm, zone, days, df.get("emoji") or g[2], qty, memo, buy)
            if ai_key():
                with st.spinner("캐릭터를 그리는 중…"):
                    ai_character(nm)
            st.session_state.draft = None
            bad = blocked_by_allergy(nm)
            if bad:
                st.warning(f"⚠️ 가족 알레르기 ‘{bad}’ 관련 재료예요")
            st.success(f"💡 {g[3]}")
            go("zone", zone=zone)
    back()


# ──────────────────────────────────────────────────────────────
# 재료 상세
# ──────────────────────────────────────────────────────────────
def screen_detail():
    it = next((i for i in st.session_state.items if i["id"] == st.session_state.sel), None)
    if not it:
        go("home")
    _, color, label, _ = life_info(it)
    g = guess_food(it["name"])
    left = days_left(it)
    exp = _d(it["expire"], TODAY)
    buy = _d(it["buy"], TODAY)
    WD = ["월", "화", "수", "목", "금", "토", "일"]
    exp_txt = f"{exp.year}년 {exp.month}월 {exp.day}일({WD[exp.weekday()]})"
    buy_txt = f"{buy.year}년 {buy.month}월 {buy.day}일"
    passed = max((TODAY - buy).days, 0)

    if left > 1:
        big, msg = f"{left}일 남았어요", "아직 여유 있어요 😄"
    elif left == 1:
        big, msg = "내일까지!", "오늘·내일 중에 드세요 😰"
    elif left == 0:
        big, msg = "오늘까지!", "오늘 안에 꼭 드세요 😵"
    else:
        big, msg = f"{-left}일 지났어요", "상태를 꼭 확인하세요 💀"

    topbar(f"{it.get('emoji','🍽️')} {it['name']}", f"{ZONES[it['zone']]['name']} · {label}")

    c1, c2 = st.columns([1, 3], gap="small")
    with c1:
        st.markdown(char_html(it, 64), unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='padding-top:10px'>{gauge_html(it)}</div>",
                    unsafe_allow_html=True)

    st.markdown(
        f"<div class='card' style='text-align:center;padding:14px 12px;"
        f"background:linear-gradient(135deg,{TINT.get(color,'#EEF2F1')},#FFFFFF)'>"
        f"<div style='font-size:11px;font-weight:800;color:#8a9793;letter-spacing:.5px'>"
        f"남은 소비기한</div>"
        f"<div style='font-size:27px;font-weight:900;color:{color};letter-spacing:-1.2px;"
        f"line-height:1.3;margin:1px 0 2px'>{big}</div>"
        f"<div style='font-size:13px;font-weight:800;color:#44544e'>📅 {exp_txt} 까지</div>"
        f"<div style='font-size:11.5px;color:#8a9793;font-weight:600;margin-top:3px'>{msg}</div>"
        f"</div>"
        f"<div class='card' style='line-height:1.75'>"
        f"🗓 <b>구입</b> {buy_txt} <span style='color:#94a19c'>({passed}일째 보관 중)</span><br>"
        f"⏰ <b>소비기한</b> {it['expire']} <span style='color:#94a19c'>(총 {it['total_days']}일)</span><br>"
        f"📦 <b>수량</b> {it.get('qty','-')}<br>"
        f"📝 <b>메모</b> {it.get('memo') or '-'}</div>"
        f"<div class='card' style='background:linear-gradient(135deg,#FFFBEC,#FFF5D8)'>"
        f"💡 <b>보관 팁</b><br><span style='font-size:12.5px'>{g[3]}</span></div>",
        unsafe_allow_html=True)

    bad = blocked_by_allergy(it["name"])
    if bad:
        st.error(f"🚫 알레르기 주의 — {bad}")

    a, b = st.columns(2, gap="small")
    with a:
        if st.button("🍽 다 먹었어요", use_container_width=True):
            st.session_state.items = [x for x in st.session_state.items if x["id"] != it["id"]]
            if it["name"] not in st.session_state.shopping:
                st.session_state.shopping.append(it["name"])
                st.session_state.seen_shopping = False
            save_data()
            go("shop")
    with b:
        if st.button("✏️ 기한 수정", use_container_width=True):
            st.session_state.edit = not st.session_state.edit
            st.rerun()

    if st.session_state.edit:
        nd = st.date_input("새 소비기한", _d(it["expire"], TODAY))
        if st.button("저장", use_container_width=True, type="primary"):
            bd = _d(it["buy"], TODAY)
            it["expire"] = nd.isoformat()
            it["total_days"] = max((nd - bd).days, 1)
            st.session_state.edit = False
            save_data()
            st.rerun()
    back("zone")


# ──────────────────────────────────────────────────────────────
# 레시피
# ──────────────────────────────────────────────────────────────
def screen_recipe():
    items = st.session_state.items
    have = {i["name"] for i in items}
    urg = {i["name"] for i in items if days_left(i) <= 3}
    topbar("오늘 뭐 해먹지 🍳", f"서두를 재료 {len(urg)}개를 먼저 써요")

    sc = []
    for r in RECIPES:
        if any(blocked_by_allergy(x) for x in r["ing"]):
            continue
        hit = [x for x in r["ing"] if any(x in h or h in x for h in have)]
        if not hit:
            continue
        miss = [x for x in r["ing"] if x not in hit]
        u = sum(1 for x in hit if x in urg)
        sc.append((u * 10 + len(hit) - len(miss) * 2, r, hit, miss, u))
    sc.sort(key=lambda x: -x[0])

    if not sc:
        st.markdown("<div class='card empty'>재료를 조금 더 넣어주세요 🥲</div>",
                    unsafe_allow_html=True)
    for _, r, hit, miss, u in sc[:4]:
        tag = "<span class='badge' style='background:#FF8A3D'>임박 소비</span>" if u else ""
        info = (f"<br><span style='color:#D1620B;font-size:11.5px;font-weight:700'>"
                f"＋ 필요: {', '.join(miss)}</span>" if miss else
                "<br><span style='color:#1E9E6A;font-size:11.5px;font-weight:700'>"
                "✓ 재료가 다 있어요!</span>")
        st.markdown(
            f"<div class='card'><span style='font-size:15px;font-weight:800'>"
            f"{r['emoji']} {r['name']}</span> {tag}"
            f"<span style='float:right;font-size:11px;color:#94a19c;font-weight:700'>{r['time']}</span>"
            f"<br><span style='font-size:11.5px;color:#66756f'>사용: {', '.join(hit)}</span>{info}</div>",
            unsafe_allow_html=True)
        if miss and st.button("🛒 부족한 재료 담기", key=f"r{r['name']}", use_container_width=True):
            for m in miss:
                if m not in st.session_state.shopping:
                    st.session_state.shopping.append(m)
            st.session_state.seen_shopping = False
            save_data()
            st.toast("장보기 메모에 담았어요 🛒")
    back()


def screen_half():
    topbar("남은 반쪽 구하기 🥢", "한 번에 다 못 쓰는 재료 전용")
    tg = [i for i in st.session_state.items
          if i["name"] in HALF_FOODS or "반" in (i.get("memo") or "")]
    if not tg:
        st.markdown("<div class='card empty'>대파·양배추·두부처럼<br>"
                    "남기 쉬운 재료가 아직 없어요 🌿</div>", unsafe_allow_html=True)
    for t in sorted(tg, key=days_left)[:3]:
        uses = [r for r in RECIPES if any(t["name"] in x or x in t["name"] for x in r["ing"])]
        chips = "".join(
            f"<span style='display:inline-block;background:#EEF8F4;border-radius:99px;"
            f"padding:3px 10px;margin:3px 4px 0 0;font-size:11.5px;font-weight:700;"
            f"color:#1E7A5C'>{r['emoji']} {r['name']}</span>" for r in uses[:4]) \
            or "<span style='font-size:12px;color:#94a19c'>자유롭게 활용해 보세요</span>"
        st.markdown(
            f"<div class='card'><span style='font-size:14.5px;font-weight:800'>"
            f"{t.get('emoji','🍽️')} {t['name']}</span>"
            f"<span style='float:right;font-size:11px;color:#94a19c;font-weight:700'>"
            f"D-{days_left(t)}</span><br>{chips}"
            f"<br><span style='font-size:11.5px;color:#1E7A5C;font-weight:600'>"
            f"💡 {guess_food(t['name'])[3]}</span></div>", unsafe_allow_html=True)
    back()


# ──────────────────────────────────────────────────────────────
# 장보기 / 검색 / 알레르기 / 팁
# ──────────────────────────────────────────────────────────────
def screen_shop():
    topbar("장보기 메모 📝", f"{len(st.session_state.shopping)}개 담겨 있어요")
    new = st.text_input("추가", "", placeholder="살 것 적고 Enter ↵",
                        label_visibility="collapsed")
    if new and new not in st.session_state.shopping:
        st.session_state.shopping.append(new)
        save_data()
        st.rerun()
    if not st.session_state.shopping:
        st.markdown("<div class='card empty'>메모가 비었어요 ✨</div>", unsafe_allow_html=True)
    for s in list(st.session_state.shopping)[:8]:
        c1, c2 = st.columns([5, 1.1], gap="small")
        c1.markdown(f"<div class='card' style='margin-bottom:5px;padding:10px 14px'>"
                    f"🛒 <b>{s}</b></div>", unsafe_allow_html=True)
        if c2.button("✓", key=f"s_{s}", use_container_width=True):
            st.session_state.shopping.remove(s)
            save_data()
            st.rerun()
    back()


def screen_find():
    topbar("집에 이거 있나? 🔍", "마트에서 바로 확인하세요")
    q = st.text_input("검색", "", placeholder="예) 계란", label_visibility="collapsed")
    if q:
        hits = [i for i in st.session_state.items if q in i["name"] or i["name"] in q]
        if hits:
            for h in hits:
                st.markdown(
                    f"<div class='card' style='background:linear-gradient(135deg,#E8FBF1,#D9F6E7)'>"
                    f"<span style='font-size:15px;font-weight:800;color:#1E7A5C'>"
                    f"✅ 있어요 — {h['name']}</span><br>"
                    f"<span style='font-size:12px;color:#55665f'>{ZONES[h['zone']]['name']} · "
                    f"{h.get('qty','')} · D-{days_left(h)}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div class='card' style='background:linear-gradient(135deg,#FFEFE6,#FFE3D2)'>"
                f"<span style='font-size:15px;font-weight:800;color:#C2410C'>❌ 없어요 — {q}</span>"
                f"<br><span style='font-size:12px;color:#7a6356'>사 오시면 좋겠어요</span></div>",
                unsafe_allow_html=True)
            if st.button("🛒 장보기 메모에 담기", use_container_width=True, type="primary"):
                st.session_state.shopping.append(q)
                st.session_state.seen_shopping = False
                save_data()
                go("shop")
    back()


def screen_allergy():
    topbar("알레르기 설정 🚫", "추천 레시피에서 자동으로 빼드려요")
    sel = st.multiselect("못 먹는 것", list(ALLERGY_MAP.keys()),
                         default=st.session_state.allergies, label_visibility="collapsed")
    if st.button("저장하기", use_container_width=True, type="primary"):
        st.session_state.allergies = sel
        save_data()
        st.success("저장했어요! 레시피에 바로 반영돼요")
    risky = [i["name"] for i in st.session_state.items if blocked_by_allergy(i["name"])]
    if risky:
        st.markdown(f"<div class='card' style='background:linear-gradient(135deg,#FFECEE,#FFDFE3)'>"
                    f"⚠️ <b>냉장고 속 주의 재료</b><br>{', '.join(risky[:8])}</div>",
                    unsafe_allow_html=True)
    back()


def screen_tips():
    topbar("보관법 팁 💡", "지금 냉장고에 있는 재료 기준")
    mine = st.session_state.items[:5]
    src = [(i.get("emoji", "🍽️"), i["name"], guess_food(i["name"])[3]) for i in mine] or \
          [(FOOD_DB[n][2], n, FOOD_DB[n][3]) for n in ["대파", "계란", "두부", "감자"]]
    for e, n, t in src:
        st.markdown(f"<div class='card'><span style='font-size:14px;font-weight:800'>{e} {n}</span>"
                    f"<br><span style='font-size:12.5px;color:#55665f'>{t}</span></div>",
                    unsafe_allow_html=True)
    back()


SCREENS = {"home": screen_home, "zone": screen_zone, "add": screen_add,
           "detail": screen_detail, "recipe": screen_recipe, "half": screen_half,
           "shop": screen_shop, "find": screen_find, "allergy": screen_allergy,
           "tips": screen_tips}

try:
    SCREENS.get(st.session_state.get("screen", "home"), screen_home)()
except Exception as e:
    st.error("문제가 생겨 홈으로 돌아갑니다.")
    st.caption(f"({type(e).__name__})")
    if st.button("🏠 홈으로", use_container_width=True, type="primary"):
        go("home")
