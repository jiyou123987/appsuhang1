# -*- coding: utf-8 -*-
"""
우리집 냉장고 (My Family Fridge) — v4
Streamlit 단일 파일 · 모바일 세로형 · 한 화면 = 한 기능
좌우 사이드 아이콘 + 진짜 냉장고처럼 보이는 칸 UI
"""

import os
import re
import json
import base64
import hashlib
import datetime as dt

import streamlit as st

st.set_page_config(page_title="우리집 냉장고", page_icon="🧊",
                   layout="centered", initial_sidebar_state="collapsed")

DATA_FILE = "fridge_data.json"
TODAY = dt.date.today()
WD = ["월", "화", "수", "목", "금", "토", "일"]

ZONES = {
    "frozen": {"name": "냉동칸",   "emoji": "🧊"},
    "dairy":  {"name": "유제품칸", "emoji": "🥛"},
    "meat":   {"name": "고기칸",   "emoji": "🥩"},
    "side":   {"name": "반찬칸",   "emoji": "🍱"},
    "veg":    {"name": "야채칸",   "emoji": "🥬"},
    "fruit":  {"name": "과일칸",   "emoji": "🍎"},
}
ZKEYS = list(ZONES.keys())

FOOD_DB = {
    "우유":     ("dairy", 7,  "🥛", "개봉 후엔 도어칸 말고 안쪽 선반에. 문쪽은 온도가 들쭉날쭉해요."),
    "요구르트": ("dairy", 14, "🥤", "뚜껑을 꼭 닫아 냄새 흡수를 막아주세요."),
    "치즈":     ("dairy", 21, "🧀", "랩 대신 종이포일로 싸면 덜 눅눅해져요."),
    "버터":     ("dairy", 60, "🧈", "냄새를 잘 먹어요. 밀폐용기에 따로 보관하세요."),
    "계란":     ("dairy", 21, "🥚", "뾰족한 쪽을 아래로 두면 더 오래가요. 씻지 말고 넣기."),
    "두부":     ("side",  5,  "🧈", "남으면 물에 잠기게 담가 매일 물을 갈아주세요."),
    "대파":     ("veg",   10, "🌿", "송송 썰어 지퍼백에 얼리면 2개월! 흰 부분은 따로."),
    "양파":     ("veg",   30, "🧅", "통째로는 실온 망에. 깐 건 밀폐해서 냉장."),
    "당근":     ("veg",   21, "🥕", "신문지에 싸서 세워두면 수분이 덜 빠져요."),
    "감자":     ("veg",   30, "🥔", "냉장은 금지! 사과 한 알과 함께 어두운 실온에."),
    "애호박":   ("veg",   10, "🥒", "자른 단면에 랩을 밀착시켜 주세요."),
    "양배추":   ("veg",   14, "🥬", "심을 파내고 젖은 키친타월을 끼워두면 오래가요."),
    "시금치":   ("veg",   5,  "🥬", "세워서 보관. 눕히면 금방 물러요."),
    "버섯":     ("veg",   7,  "🍄", "씻지 말고 종이봉투에. 물기가 최대의 적이에요."),
    "무":       ("veg",   21, "🥗", "잎을 잘라내고 신문지에 싸서 세워두세요."),
    "오이":     ("veg",   7,  "🥒", "랩에 싸서 세워 보관하면 무르지 않아요."),
    "토마토":   ("fruit", 7,  "🍅", "꼭지를 아래로. 덜 익었으면 실온에 두세요."),
    "사과":     ("fruit", 21, "🍎", "에틸렌이 나와요. 다른 채소와 꼭 분리!"),
    "바나나":   ("fruit", 5,  "🍌", "냉장 금지. 꼭지를 랩으로 감싸면 며칠 더 버텨요."),
    "딸기":     ("fruit", 3,  "🍓", "먹기 직전에 씻기. 키친타월 깔고 한 겹만."),
    "포도":     ("fruit", 7,  "🍇", "씻지 않은 채로 통풍되는 용기에."),
    "귤":       ("fruit", 14, "🍊", "상자째 두지 말고 한 겹씩 펴서 통풍시켜요."),
    "수박":     ("fruit", 5,  "🍉", "자른 면에 랩을 밀착. 통째로는 실온이 더 달아요."),
    "닭고기":   ("meat",  2,  "🍗", "핏물을 닦고 한 끼씩 소분해 냉동하면 안전해요."),
    "돼지고기": ("meat",  3,  "🥓", "공기를 빼고 밀착 포장. 3일 넘기면 냉동으로."),
    "소고기":   ("meat",  3,  "🥩", "키친타월로 핏물 제거 후 랩 밀착 포장."),
    "생선":     ("meat",  2,  "🐟", "내장을 빼고 물기를 닦아 랩+지퍼백 이중으로."),
    "새우":     ("frozen", 30, "🦐", "해동은 냉장실에서 천천히. 재냉동은 금물."),
    "만두":     ("frozen", 90, "🥟", "서로 붙지 않게 펼쳐 얼린 뒤 봉지에 모아주세요."),
    "아이스크림": ("frozen", 180, "🍦", "문쪽은 녹았다 얼어요. 가장 안쪽에 두세요."),
    "김치":     ("side",  60, "🥬", "공기 접촉이 산패의 원인. 꾹 눌러 국물에 잠기게."),
    "햄":       ("side",  14, "🍖", "개봉 후엔 밀폐용기로 옮겨 담아주세요."),
    "밥":       ("side",  2,  "🍚", "따뜻할 때 한 공기씩 랩에 싸서 냉동하면 갓 지은 맛."),
    "식빵":     ("side",  5,  "🍞", "냉장은 오히려 노화를 촉진해요. 냉동 후 바로 구우세요."),
}
HALF_FOODS = {"대파", "양배추", "두부", "애호박", "당근", "양파", "무", "식빵", "수박"}

# 사진 파일명 자동 인식용 (영문 → 한글)
EN2KO = {
    "milk": "우유", "egg": "계란", "cheese": "치즈", "butter": "버터",
    "yogurt": "요구르트", "tofu": "두부", "onion": "양파", "carrot": "당근",
    "potato": "감자", "cabbage": "양배추", "spinach": "시금치",
    "mushroom": "버섯", "cucumber": "오이", "tomato": "토마토",
    "apple": "사과", "banana": "바나나", "strawberry": "딸기",
    "grape": "포도", "orange": "귤", "watermelon": "수박",
    "chicken": "닭고기", "pork": "돼지고기", "beef": "소고기",
    "fish": "생선", "shrimp": "새우", "dumpling": "만두",
    "icecream": "아이스크림", "kimchi": "김치", "ham": "햄",
    "rice": "밥", "bread": "식빵", "radish": "무", "greenonion": "대파",
}

RECIPES = [
    {"name": "계란찜",         "emoji": "🍳", "ing": ["계란", "대파"],                   "time": "10분"},
    {"name": "파기름 볶음밥",   "emoji": "🍚", "ing": ["대파", "밥", "계란"],             "time": "15분"},
    {"name": "두부김치",       "emoji": "🥬", "ing": ["두부", "김치", "돼지고기"],       "time": "20분"},
    {"name": "된장찌개",       "emoji": "🍲", "ing": ["두부", "애호박", "양파", "감자"],  "time": "25분"},
    {"name": "양배추전",       "emoji": "🥞", "ing": ["양배추", "계란"],                 "time": "15분"},
    {"name": "닭볶음탕",       "emoji": "🍗", "ing": ["닭고기", "감자", "당근", "양파"],  "time": "40분"},
    {"name": "제육볶음",       "emoji": "🥓", "ing": ["돼지고기", "양파", "대파"],       "time": "25분"},
    {"name": "버섯크림파스타",  "emoji": "🍝", "ing": ["버섯", "우유", "양파"],           "time": "20분"},
    {"name": "토마토달걀볶음",  "emoji": "🍅", "ing": ["토마토", "계란", "대파"],         "time": "10분"},
    {"name": "감자채볶음",     "emoji": "🥔", "ing": ["감자", "양파"],                   "time": "15분"},
    {"name": "시금치나물",     "emoji": "🥬", "ing": ["시금치"],                         "time": "10분"},
    {"name": "프렌치토스트",   "emoji": "🍞", "ing": ["식빵", "계란", "우유"],           "time": "10분"},
    {"name": "새우볶음밥",     "emoji": "🍤", "ing": ["새우", "밥", "계란", "당근"],     "time": "20분"},
    {"name": "소고기무국",     "emoji": "🍲", "ing": ["소고기", "무", "대파"],           "time": "30분"},
    {"name": "치즈라면",       "emoji": "🍜", "ing": ["치즈", "계란", "대파"],           "time": "8분"},
    {"name": "오이무침",       "emoji": "🥒", "ing": ["오이", "양파"],                   "time": "10분"},
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

# ══════════════════════════════════════════════════════════════
#  스타일  ※ 들여쓰기 금지 (마크다운이 코드블록으로 오인함)
# ══════════════════════════════════════════════════════════════
CSS = """
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp {background:radial-gradient(1200px 500px at 50% -10%,#EAF6FF 0%,transparent 60%),linear-gradient(180deg,#FBFDFE 0%,#EDF5F3 48%,#E4F0F4 100%); background-attachment:fixed;}
.block-container {padding:0.5rem 0.55rem 0.7rem !important; max-width:430px !important;}
html, body, [class*="css"], button, input {font-family:'Pretendard','Apple SD Gothic Neo',-apple-system,'Malgun Gothic',sans-serif !important; -webkit-tap-highlight-color:transparent;}
div[data-testid="stVerticalBlock"] {gap:0.32rem !important;}
div[data-testid="stHorizontalBlock"] {gap:0.34rem !important;}

.topbar {background:linear-gradient(135deg,#7FE0C4 0%,#5ECBD6 52%,#73B8F0 100%); border-radius:23px; padding:12px 17px; margin-bottom:9px; box-shadow:0 9px 22px -11px rgba(70,180,185,.85); position:relative; overflow:hidden;}
.topbar:after {content:''; position:absolute; right:-28px; top:-40px; width:120px; height:120px; border-radius:50%; background:rgba(255,255,255,.17);}
.tb-t {color:#fff; font-weight:850; font-size:18px; letter-spacing:-0.8px; position:relative;}
.tb-s {color:rgba(255,255,255,.95); font-weight:650; font-size:11px; margin-top:2px; position:relative;}

.fr-top {background:linear-gradient(180deg,#F7FBFA,#E9F3F1); border-radius:22px 22px 7px 7px; padding:9px 0 7px; margin-bottom:4px; box-shadow:0 5px 14px -9px rgba(50,100,92,.6); text-align:center; border:1px solid rgba(255,255,255,.9);}
.fr-hdl {width:46px; height:5px; border-radius:99px; margin:0 auto 5px; background:linear-gradient(90deg,#DCEAE6,#BED6CF);}
.fr-lbl {font-size:9.5px; font-weight:800; color:#9FB2AC; letter-spacing:2.5px;}
.fr-bot {height:13px; border-radius:7px 7px 20px 20px; background:linear-gradient(180deg,#E9F3F1,#DCEAE6); margin-top:4px; box-shadow:0 8px 18px -10px rgba(50,100,92,.65);}
.shelf {height:4px; border-radius:99px; background:linear-gradient(90deg,rgba(190,214,207,0),rgba(170,200,192,.75),rgba(190,214,207,0)); margin:2px 6px;}

div[data-testid="column"] .stButton > button {width:100%; border:none; border-radius:19px; padding:11px 3px; min-height:80px; font-weight:800; font-size:12.5px; line-height:1.5; color:#235349; background:linear-gradient(165deg,#FFFFFF 0%,#F3FAF8 100%); box-shadow:0 5px 13px -7px rgba(50,100,92,.55), inset 0 1px 0 rgba(255,255,255,.9); transition:transform .17s cubic-bezier(.3,1.5,.5,1), box-shadow .17s; white-space:pre-line;}
div[data-testid="column"] .stButton > button:hover {transform:translateY(-3px) scale(1.025); color:#0E7A5E; box-shadow:0 10px 18px -8px rgba(50,130,110,.55);}
div[data-testid="column"] .stButton > button:active {transform:scale(.95);}

.sb .stButton > button {min-height:58px !important; padding:5px 0 !important; font-size:11px !important; line-height:1.35 !important; font-weight:800 !important; border-radius:17px !important; white-space:pre-line !important; background:linear-gradient(165deg,#FFFFFF,#FFF6E2) !important; color:#6E5B2C !important; box-shadow:0 4px 11px -6px rgba(185,150,65,.75), inset 0 1px 0 rgba(255,255,255,.95) !important;}
.sb .stButton > button:hover {transform:translateY(-2px) scale(1.04) !important; color:#B07A12 !important;}
.sb-r .stButton > button {background:linear-gradient(165deg,#FFFFFF,#EFF1FF) !important; color:#4E5585 !important; box-shadow:0 4px 11px -6px rgba(110,120,200,.65), inset 0 1px 0 rgba(255,255,255,.95) !important;}
.sb-r .stButton > button:hover {color:#3B44A0 !important;}

.stButton > button[kind="primary"] {background:linear-gradient(135deg,#54D3AE,#41C0CF) !important; color:#fff !important; border:none !important; font-weight:850 !important; border-radius:18px !important; padding:11px !important; font-size:14px !important; min-height:0 !important; box-shadow:0 8px 17px -9px rgba(65,192,207,.95) !important;}
.stButton > button[kind="secondary"] {background:rgba(255,255,255,.92) !important; color:#5A6A65 !important; border:none !important; border-radius:16px !important; font-weight:750 !important; font-size:13px !important; min-height:0 !important; box-shadow:0 3px 9px -5px rgba(50,100,92,.5) !important;}
.stButton > button:focus {box-shadow:none !important; outline:none !important;}

.card {background:rgba(255,255,255,.96); border-radius:19px; padding:11px 14px; margin-bottom:7px; box-shadow:0 6px 16px -11px rgba(50,100,92,.6); font-size:12.5px; color:#2F403B; animation:pop .3s cubic-bezier(.3,1.3,.5,1);}
@keyframes pop {from{opacity:0; transform:translateY(8px);} to{opacity:1; transform:none;}}
.gbg {background:#EBF1EF; border-radius:99px; height:8px; overflow:hidden;}
.gfl {height:8px; border-radius:99px; transition:width .6s ease;}
.badge {display:inline-block; padding:2px 9px; border-radius:99px; font-size:9.5px; font-weight:850; color:#fff;}
.chr {border-radius:50%; display:flex; align-items:center; justify-content:center; position:relative; box-shadow:0 5px 12px -7px rgba(50,100,92,.7); border:2.5px solid #fff;}
.face {position:absolute; right:-3px; bottom:-4px;}
.wig {animation:wg 2.4s ease-in-out infinite;}
@keyframes wg {0%,100%{transform:rotate(-4deg);} 50%{transform:rotate(4deg);}}
.hint {font-size:10.5px; color:#9AA8A3; text-align:center; margin-top:5px; font-weight:650;}
.chip {display:inline-block; background:#EDF8F4; border-radius:99px; padding:3px 10px; margin:3px 4px 0 0; font-size:11px; font-weight:750; color:#1C7A5B;}
.stTextInput input, .stNumberInput input, .stDateInput input {border-radius:14px !important; border:1.5px solid #E2ECE8 !important; font-size:13px !important;}
div[data-baseweb="select"] > div {border-radius:14px !important;}
.stTabs [data-baseweb="tab"] {border-radius:13px; padding:5px 13px; font-size:12.5px; font-weight:750;}
.stTabs [aria-selected="true"] {background:linear-gradient(135deg,#54D3AE,#41C0CF); color:#fff;}
label {font-size:11.5px !important; font-weight:750 !important; color:#5A6A65 !important;}
</style>
"""

if hasattr(st, "html"):
    st.html(CSS)
else:
    st.markdown(CSS, unsafe_allow_html=True)


def H(html):
    st.markdown(" ".join(str(html).split()), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  데이터
# ══════════════════════════════════════════════════════════════
def guess_food(name):
    name = (name or "").strip()
    if name in FOOD_DB:
        return FOOD_DB[name]
    for k, v in FOOD_DB.items():
        if k and (k in name or name in k):
            return v
    return ("side", 7, "🍽️", "밀폐용기에 담아 냉장 보관하고 3~5일 안에 드세요.")


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
        name = str(it.get("name") or "").strip()
        if not name:
            continue
        g = guess_food(name)
        buy = _d(it.get("buy"), TODAY)
        try:
            total = int(it.get("total_days"))
        except (TypeError, ValueError):
            total = int(g[1])
        total = max(1, min(total, 3650))
        exp = _d(it.get("expire"), buy + dt.timedelta(days=total))
        out.append({
            "id": str(it.get("id") or hashlib.md5(
                f"{name}{len(out)}{dt.datetime.now()}".encode()).hexdigest()[:8]),
            "name": name,
            "zone": it.get("zone") if it.get("zone") in ZONES else g[0],
            "emoji": str(it.get("emoji") or g[2]),
            "qty": str(it.get("qty") or "1개"),
            "memo": str(it.get("memo") or ""),
            "buy": buy.isoformat(), "expire": exp.isoformat(), "total_days": total})
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
            json.dump({"items": st.session_state.foods,
                       "shopping": st.session_state.shopping,
                       "allergies": st.session_state.allergies,
                       "seen_shopping": st.session_state.seen_shopping},
                      f, ensure_ascii=False, indent=1)
    except Exception:
        pass


if "foods" not in st.session_state:
    _d0 = load_data()
    st.session_state.foods = sanitize(_d0.get("items"))
    _sp = _d0.get("shopping")
    st.session_state.shopping = [str(x) for x in _sp] if isinstance(_sp, list) else []
    _al = _d0.get("allergies")
    st.session_state.allergies = [x for x in _al if x in ALLERGY_MAP] if isinstance(_al, list) else []
    st.session_state.seen_shopping = bool(_d0.get("seen_shopping", True))
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


# ══════════════════════════════════════════════════════════════
#  계산
# ══════════════════════════════════════════════════════════════
def days_left(item):
    try:
        e = _d(item.get("expire"))
        return (e - TODAY).days if e else 7
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
    wig = "wig" if days_left(item) > 3 else ""
    if url:
        return (f"<img class='{wig}' src='{url}' style='width:{size}px;height:{size}px;"
                f"border-radius:50%;object-fit:cover;border:2.5px solid {color};'>")
    return (f"<div class='chr {wig}' style='width:{size}px;height:{size}px;"
            f"background:{TINT.get(color, '#EEF2F1')};border-color:{color};"
            f"font-size:{int(size * .5)}px;'>{item.get('emoji', '🍽️')}"
            f"<span class='face' style='font-size:{int(size * .33)}px'>{face}</span></div>")


def gauge_html(item):
    ratio, color, label, _ = life_info(item)
    left = days_left(item)
    txt = f"D-{left}" if left > 0 else ("오늘까지!" if left == 0 else f"{-left}일 지남")
    return (f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"font-size:10.5px;color:#7C8A85;font-weight:750;margin:4px 0 3px;'>"
            f"<span>{txt}</span><span class='badge' style='background:{color}'>{label}</span></div>"
            f"<div class='gbg'><div class='gfl' style='width:{ratio * 100:.0f}%;background:{color}'></div></div>")


def blocked_by_allergy(name):
    name = name or ""
    for a in st.session_state.allergies:
        for bad in ALLERGY_MAP.get(a, []):
            if bad in name or name in bad:
                return a
    return None


# ══════════════════════════════════════════════════════════════
#  사진 인식 (API 키 없어도 동작하는 오프라인 추정 내장)
# ══════════════════════════════════════════════════════════════
def ai_key():
    try:
        k = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        k = ""
    return k or os.environ.get("OPENAI_API_KEY", "")


def guess_from_filename(fname):
    """파일명에서 재료 추정 — 키 없이도 동작"""
    s = (fname or "").lower()
    s = re.sub(r"\.(jpg|jpeg|png|webp|heic)$", "", s)
    for ko in FOOD_DB:
        if ko in (fname or ""):
            g = FOOD_DB[ko]
            return {"name": ko, "zone": g[0], "days": g[1], "emoji": g[2], "how": "파일명"}
    for en, ko in EN2KO.items():
        if en in s.replace("_", "").replace("-", "").replace(" ", ""):
            g = FOOD_DB.get(ko, guess_food(ko))
            return {"name": ko, "zone": g[0], "days": g[1], "emoji": g[2], "how": "파일명"}
    return None


def guess_from_colors(image_bytes):
    """평균 색으로 보관 칸만이라도 추정 — Pillow 없으면 건너뜀"""
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((32, 32))
        px = list(im.getdata())
        r = sum(p[0] for p in px) / len(px)
        g = sum(p[1] for p in px) / len(px)
        b = sum(p[2] for p in px) / len(px)
        if g > r and g > b:
            return {"name": "", "zone": "veg", "days": 7, "emoji": "🥬", "how": "색상"}
        if r > g * 1.25 and r > b * 1.25:
            return {"name": "", "zone": "fruit", "days": 7, "emoji": "🍎", "how": "색상"}
        if r > 190 and g > 185 and b > 180:
            return {"name": "", "zone": "dairy", "days": 7, "emoji": "🥛", "how": "색상"}
    except Exception:
        pass
    return None


def ai_recognize(image_bytes, fname=""):
    """1순위 AI → 2순위 파일명 → 3순위 색상"""
    key = ai_key()
    if key:
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
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}])
            t = r.choices[0].message.content.strip()
            o = json.loads(t[t.find("{"): t.rfind("}") + 1])
            if str(o.get("name", "")).strip():
                return {"name": str(o["name"]).strip(),
                        "zone": o.get("zone") if o.get("zone") in ZONES else "side",
                        "days": int(o.get("days", 7)),
                        "emoji": str(o.get("emoji", "🍽️")), "how": "AI"}
        except Exception:
            pass
    return guess_from_filename(fname) or guess_from_colors(image_bytes)


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
    st.session_state.foods.append({
        "id": hashlib.md5(f"{name}{dt.datetime.now()}".encode()).hexdigest()[:8],
        "name": name, "zone": zone if zone in ZONES else "side", "emoji": emoji or "🍽️",
        "qty": qty or "1개", "memo": memo or "", "buy": buy.isoformat(),
        "expire": (buy + dt.timedelta(days=total)).isoformat(), "total_days": total})
    save_data()


def topbar(title, sub=""):
    H(f"<div class='topbar'><div class='tb-t'>{title}</div><div class='tb-s'>{sub}</div></div>")


def back(to="home"):
    if st.button("‹  뒤로", use_container_width=True, key=f"bk_{st.session_state.screen}"):
        go(to)


# ══════════════════════════════════════════════════════════════
#  홈 — 진짜 냉장고 문짝 + 좌우 사이드 아이콘
# ══════════════════════════════════════════════════════════════
def screen_home():
    foods = st.session_state.foods
    urg = [i for i in foods if days_left(i) <= 3]
    sub = f"재료 {len(foods)}개" + (f" · 서두를 재료 {len(urg)}개 ⚠️" if urg else " · 모두 신선해요 ✨")
    topbar("우리집 냉장고 🧊", sub)

    left, mid, right = st.columns([1, 3.3, 1], gap="small")

    # ── 왼쪽 사이드: 요리 관련
    with left:
        H("<div class='sb'>")
        if st.button("🍳\n레시피", key="s1", use_container_width=True,
                     help="임박한 재료부터 쓰는 요리 추천"):
            go("recipe")
        if st.button("🥢\n반쪽", key="s2", use_container_width=True,
                     help="남은 반쪽 재료 소비 레시피"):
            go("half")
        if st.button("💡\n보관법", key="s3", use_container_width=True,
                     help="재료별 보관 팁"):
            go("tips")
        H("</div>")

    # ── 가운데: 냉장고
    with mid:
        H("<div class='fr-top'><div class='fr-hdl'></div>"
          "<div class='fr-lbl'>F A M I L Y &nbsp; F R I D G E</div></div>")
        for row in range(3):
            cols = st.columns(2, gap="small")
            for j in range(2):
                z = ZKEYS[row * 2 + j]
                zi = ZONES[z]
                n = sum(1 for i in foods if i.get("zone") == z)
                w = sum(1 for i in foods if i.get("zone") == z and days_left(i) <= 3)
                tail = f"{n}개" + (f"  ❗{w}" if w else "")
                with cols[j]:
                    if st.button(f"{zi['emoji']}\n{zi['name']}\n{tail}",
                                 key=f"z{z}", use_container_width=True):
                        go("zone", zone=z)
            if row < 2:
                H("<div class='shelf'></div>")
        H("<div class='fr-bot'></div>")

    # ── 오른쪽 사이드: 장보기 관련
    with right:
        H("<div class='sb sb-r'>")
        mk = "❗\n장보기" if (st.session_state.shopping and not st.session_state.seen_shopping) else "📝\n장보기"
        if st.button(mk, key="s4", use_container_width=True, help="살 것 메모"):
            st.session_state.seen_shopping = True
            save_data()
            go("shop")
        if st.button("🔍\n있나?", key="s5", use_container_width=True,
                     help="마트에서 집에 있는지 확인"):
            go("find")
        if st.button("🚫\n알레르기", key="s6", use_container_width=True,
                     help="못 먹는 재료 설정"):
            go("allergy")
        H("</div>")

    st.write("")
    if st.button("＋  재료 넣기", use_container_width=True, type="primary", key="addm"):
        go("add", zone="veg")
    H("<div class='hint'>칸을 눌러 재료 보기 · 좌우는 기능 버튼</div>")


# ══════════════════════════════════════════════════════════════
def screen_zone():
    z = st.session_state.zone if st.session_state.zone in ZONES else "veg"
    zi = ZONES[z]
    foods = sorted([i for i in st.session_state.foods if i.get("zone") == z], key=days_left)
    topbar(f"{zi['emoji']} {zi['name']}", f"{len(foods)}개 보관 중 · 급한 것부터 보여드려요")

    if not foods:
        H("<div class='card' style='text-align:center;padding:24px 12px;color:#8A9793'>"
          "텅 비었어요 🫙<br><span style='font-size:11px'>아래에서 재료를 넣어보세요</span></div>")
    for it in foods[:5]:
        c1, c2 = st.columns([1, 4.3], gap="small")
        with c1:
            H(f"<div style='padding-top:7px'>{char_html(it)}</div>")
        with c2:
            H(f"<b style='font-size:14px'>{it['name']}</b>"
              f"<span style='font-size:10.5px;color:#94A19C;font-weight:650'> {it.get('qty', '')}</span>"
              f"{gauge_html(it)}")
        if st.button("상세 보기 ›", key=f"d{it['id']}", use_container_width=True):
            go("detail", sel=it["id"], edit=False)
    if len(foods) > 5:
        H(f"<div class='hint'>외 {len(foods) - 5}개 더 있어요</div>")

    a, b = st.columns(2, gap="small")
    with a:
        if st.button("＋ 넣기", use_container_width=True, type="primary", key="addz"):
            go("add", zone=z)
    with b:
        back()


def screen_add():
    topbar("재료 넣기 ＋", "사진을 올리면 자동으로 채워져요")
    tab1, tab2 = st.tabs(["📷 사진으로", "✍️ 직접"])

    with tab1:
        up = st.file_uploader("사진", type=["jpg", "jpeg", "png", "webp"],
                              label_visibility="collapsed", key="up")
        if up and st.button("🔎 자동 인식", use_container_width=True, type="primary"):
            with st.spinner("사진을 보는 중…"):
                r = ai_recognize(up.getvalue(), up.name)
            if r:
                st.session_state.draft = r
                how = r.get("how", "")
                if r.get("name"):
                    st.success(f"‘{r['name']}’ 같아요! ({how} 추정) 틀리면 아래에서 고치세요")
                else:
                    st.info(f"{ZONES[r['zone']]['name']} 재료로 보여요 ({how} 추정). 이름만 적어주세요")
            else:
                st.info("이름을 알아내지 못했어요. 아래에 직접 적어주세요 ✍️")

    with tab2:
        pick = st.selectbox("빠른 선택", ["직접 입력"] + list(FOOD_DB.keys()),
                            label_visibility="collapsed")
        if pick != "직접 입력":
            z0, d0, e0, _ = FOOD_DB[pick]
            st.session_state.draft = {"name": pick, "zone": z0, "days": d0, "emoji": e0}

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
            go("zone", zone=zone)
    back()


def screen_detail():
    it = next((i for i in st.session_state.foods if i["id"] == st.session_state.sel), None)
    if not it:
        go("home")
    _, color, label, _ = life_info(it)
    g = guess_food(it["name"])
    left = days_left(it)
    exp = _d(it["expire"], TODAY)
    buy = _d(it["buy"], TODAY)
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

    topbar(f"{it.get('emoji', '🍽️')} {it['name']}", f"{ZONES[it['zone']]['name']} · {label}")

    c1, c2 = st.columns([1, 3], gap="small")
    with c1:
        H(char_html(it, 64))
    with c2:
        H(f"<div style='padding-top:10px'>{gauge_html(it)}</div>")

    H(f"<div class='card' style='text-align:center;padding:14px 12px;"
      f"background:linear-gradient(135deg,{TINT.get(color, '#EEF2F1')},#FFFFFF)'>"
      f"<div style='font-size:10.5px;font-weight:850;color:#8A9793'>남은 소비기한</div>"
      f"<div style='font-size:27px;font-weight:900;color:{color};letter-spacing:-1.2px;"
      f"line-height:1.35'>{big}</div>"
      f"<div style='font-size:13px;font-weight:800;color:#44544E'>📅 {exp_txt} 까지</div>"
      f"<div style='font-size:11px;color:#8A9793;font-weight:650;margin-top:3px'>{msg}</div></div>")

    H(f"<div class='card' style='line-height:1.75'>"
      f"🗓 <b>구입</b> {buy_txt} <span style='color:#94A19C'>({passed}일째 보관 중)</span><br>"
      f"⏰ <b>소비기한</b> {it['expire']} <span style='color:#94A19C'>(총 {it['total_days']}일)</span><br>"
      f"📦 <b>수량</b> {it.get('qty', '-')}<br>"
      f"📝 <b>메모</b> {it.get('memo') or '-'}</div>"
      f"<div class='card' style='background:linear-gradient(135deg,#FFFBEC,#FFF5D8)'>"
      f"💡 <b>보관 팁</b><br><span style='font-size:12px'>{g[3]}</span></div>")

    bad = blocked_by_allergy(it["name"])
    if bad:
        st.error(f"🚫 알레르기 주의 — {bad}")

    a, b = st.columns(2, gap="small")
    with a:
        if st.button("🍽 다 먹었어요", use_container_width=True):
            st.session_state.foods = [x for x in st.session_state.foods if x["id"] != it["id"]]
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
        nd = st.date_input("새 소비기한", exp)
        if st.button("저장", use_container_width=True, type="primary"):
            it["expire"] = nd.isoformat()
            it["total_days"] = max((nd - buy).days, 1)
            st.session_state.edit = False
            save_data()
            st.rerun()
    back("zone")


def screen_recipe():
    foods = st.session_state.foods
    have = {i["name"] for i in foods}
    urg = {i["name"] for i in foods if days_left(i) <= 3}
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
        H("<div class='card' style='text-align:center;padding:24px;color:#8A9793'>"
          "재료를 조금 더 넣어주세요 🥲</div>")
    for _, r, hit, miss, u in sc[:4]:
        tag = "<span class='badge' style='background:#FF8A3D'>임박 소비</span>" if u else ""
        info = (f"<br><span style='color:#D1620B;font-size:11px;font-weight:750'>"
                f"＋ 필요: {', '.join(miss)}</span>" if miss else
                "<br><span style='color:#1E9E6A;font-size:11px;font-weight:750'>"
                "✓ 재료가 다 있어요!</span>")
        H(f"<div class='card'><span style='font-size:14.5px;font-weight:850'>{r['emoji']} {r['name']}</span> {tag}"
          f"<span style='float:right;font-size:10.5px;color:#94A19C;font-weight:750'>{r['time']}</span>"
          f"<br><span style='font-size:11px;color:#66756F'>사용: {', '.join(hit)}</span>{info}</div>")
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
    tg = [i for i in st.session_state.foods
          if i["name"] in HALF_FOODS or "반" in (i.get("memo") or "")]
    if not tg:
        H("<div class='card' style='text-align:center;padding:24px;color:#8A9793'>"
          "대파·양배추·두부처럼<br>남기 쉬운 재료가 아직 없어요 🌿</div>")
    for t in sorted(tg, key=days_left)[:3]:
        uses = [r for r in RECIPES if any(t["name"] in x or x in t["name"] for x in r["ing"])]
        chips = "".join(f"<span class='chip'>{r['emoji']} {r['name']}</span>" for r in uses[:4]) \
            or "<span style='font-size:11.5px;color:#94A19C'>자유롭게 활용해 보세요</span>"
        H(f"<div class='card'><span style='font-size:14px;font-weight:850'>"
          f"{t.get('emoji', '🍽️')} {t['name']}</span>"
          f"<span style='float:right;font-size:10.5px;color:#94A19C;font-weight:750'>D-{days_left(t)}</span>"
          f"<br>{chips}<br><span style='font-size:11px;color:#1C7A5B;font-weight:650'>"
          f"💡 {guess_food(t['name'])[3]}</span></div>")
    back()


def screen_shop():
    topbar("장보기 메모 📝", f"{len(st.session_state.shopping)}개 담겨 있어요")
    new = st.text_input("추가", "", placeholder="살 것 적고 Enter ↵", label_visibility="collapsed")
    if new and new not in st.session_state.shopping:
        st.session_state.shopping.append(new)
        save_data()
        st.rerun()
    if not st.session_state.shopping:
        H("<div class='card' style='text-align:center;padding:24px;color:#8A9793'>"
          "메모가 비었어요 ✨</div>")
    for s in list(st.session_state.shopping)[:8]:
        c1, c2 = st.columns([5, 1.1], gap="small")
        with c1:
            H(f"<div class='card' style='margin-bottom:4px;padding:10px 14px'>🛒 <b>{s}</b></div>")
        if c2.button("✓", key=f"s_{s}", use_container_width=True):
            st.session_state.shopping.remove(s)
            save_data()
            st.rerun()
    back()


def screen_find():
    topbar("집에 이거 있나? 🔍", "마트에서 바로 확인하세요")
    q = st.text_input("검색", "", placeholder="예) 계란", label_visibility="collapsed")
    if q:
        hits = [i for i in st.session_state.foods if q in i["name"] or i["name"] in q]
        if hits:
            for h in hits:
                H(f"<div class='card' style='background:linear-gradient(135deg,#E8FBF1,#D9F6E7)'>"
                  f"<span style='font-size:15px;font-weight:850;color:#1C7A5B'>✅ 있어요 — {h['name']}</span>"
                  f"<br><span style='font-size:11.5px;color:#55665F'>{ZONES[h['zone']]['name']} · "
                  f"{h.get('qty', '')} · D-{days_left(h)}</span></div>")
        else:
            H(f"<div class='card' style='background:linear-gradient(135deg,#FFEFE6,#FFE3D2)'>"
              f"<span style='font-size:15px;font-weight:850;color:#C2410C'>❌ 없어요 — {q}</span>"
              f"<br><span style='font-size:11.5px;color:#7A6356'>사 오시면 좋겠어요</span></div>")
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
    risky = [i["name"] for i in st.session_state.foods if blocked_by_allergy(i["name"])]
    if risky:
        H(f"<div class='card' style='background:linear-gradient(135deg,#FFECEE,#FFDFE3)'>"
          f"⚠️ <b>냉장고 속 주의 재료</b><br>{', '.join(risky[:8])}</div>")
    back()


def screen_tips():
    topbar("보관법 팁 💡", "지금 냉장고에 있는 재료 기준")
    mine = st.session_state.foods[:5]
    src = [(i.get("emoji", "🍽️"), i["name"], guess_food(i["name"])[3]) for i in mine] or \
          [(FOOD_DB[n][2], n, FOOD_DB[n][3]) for n in ["대파", "계란", "두부", "감자"]]
    for e, n, t in src:
        H(f"<div class='card'><span style='font-size:13.5px;font-weight:850'>{e} {n}</span><br>"
          f"<span style='font-size:12px;color:#55665F'>{t}</span></div>")
    back()


SCREENS = {"home": screen_home, "zone": screen_zone, "add": screen_add,
           "detail": screen_detail, "recipe": screen_recipe, "half": screen_half,
           "shop": screen_shop, "find": screen_find, "allergy": screen_allergy,
           "tips": screen_tips}

SCREENS.get(st.session_state.get("screen", "home"), screen_home)()
