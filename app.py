# -*- coding: utf-8 -*-
"""
우리집 냉장고 (My Family Fridge)
- Streamlit 단일 파일 앱 / 모바일 세로형 / 한 화면 = 한 기능 (스크롤 최소화)
- 기능: 칸별 냉장고 UI, 재료 등록(사진 자동인식), 생명력 게이지, 상세정보,
        임박재료 우선 레시피, 반쪽 소비 레시피, 보관법 팁, 알레르기 필터,
        장보기 메모(느낌표 뱃지), 가족 재고 확인(장보는 중 검색)
"""

import os
import json
import base64
import hashlib
import datetime as dt

import streamlit as st

# ──────────────────────────────────────────────────────────────
# 기본 설정
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="우리집 냉장고",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DATA_FILE = "fridge_data.json"
TODAY = dt.date.today()

ZONES = {
    "veg":   {"name": "야채칸",   "emoji": "🥬", "color": "#B7E4C7"},
    "meat":  {"name": "고기칸",   "emoji": "🥩", "color": "#FFC9C9"},
    "dairy": {"name": "유제품칸", "emoji": "🥛", "color": "#D8E9FF"},
    "fruit": {"name": "과일칸",   "emoji": "🍎", "color": "#FFE0B2"},
    "side":  {"name": "반찬칸",   "emoji": "🍱", "color": "#FFF1A8"},
    "frozen":{"name": "냉동칸",   "emoji": "🧊", "color": "#CFE8F3"},
}

# 재료명 → (칸, 기본 소비기한(일), 이모지, 보관법 팁)
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

# 반쪽만 쓰고 남기 쉬운 재료
HALF_FOODS = {"대파", "양배추", "두부", "애호박", "당근", "양파", "무", "식빵"}

RECIPES = [
    {"name": "계란찜",       "emoji": "🍳", "ing": ["계란", "대파"],                 "time": "10분"},
    {"name": "파기름 볶음밥", "emoji": "🍚", "ing": ["대파", "밥", "계란"],           "time": "15분"},
    {"name": "두부김치",     "emoji": "🥬", "ing": ["두부", "김치", "돼지고기"],     "time": "20분"},
    {"name": "된장찌개",     "emoji": "🍲", "ing": ["두부", "애호박", "양파", "감자"], "time": "25분"},
    {"name": "양배추전",     "emoji": "🥞", "ing": ["양배추", "계란"],               "time": "15분"},
    {"name": "닭볶음탕",     "emoji": "🍗", "ing": ["닭고기", "감자", "당근", "양파"], "time": "40분"},
    {"name": "제육볶음",     "emoji": "🥓", "ing": ["돼지고기", "양파", "대파"],     "time": "25분"},
    {"name": "버섯크림파스타","emoji": "🍝", "ing": ["버섯", "우유", "양파"],         "time": "20분"},
    {"name": "토마토달걀볶음","emoji": "🍅", "ing": ["토마토", "계란", "대파"],       "time": "10분"},
    {"name": "감자채볶음",   "emoji": "🥔", "ing": ["감자", "양파"],                 "time": "15분"},
    {"name": "시금치나물",   "emoji": "🥬", "ing": ["시금치"],                       "time": "10분"},
    {"name": "프렌치토스트", "emoji": "🍞", "ing": ["식빵", "계란", "우유"],         "time": "10분"},
    {"name": "새우볶음밥",   "emoji": "🍤", "ing": ["새우", "밥", "계란", "당근"],   "time": "20분"},
    {"name": "어묵국",       "emoji": "🍢", "ing": ["대파", "무"],                   "time": "15분"},
    {"name": "치즈라면",     "emoji": "🍜", "ing": ["치즈", "계란", "대파"],         "time": "8분"},
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
# 스타일 (모바일 세로형 / 접속 기기에 따라 폭 자동 조절)
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {
    padding: 0.6rem 0.7rem 0.4rem 0.7rem !important;
    max-width: 440px !important;   /* PC에서는 폰 비율, 모바일에서는 꽉 차게 */
}
@media (max-width: 480px) {
    .block-container { max-width: 100% !important; padding: 0.4rem 0.5rem !important; }
}
html, body, [class*="css"] { font-family: 'Pretendard','Apple SD Gothic Neo',sans-serif; }

/* 상단바 */
.topbar {
    display:flex; align-items:center; justify-content:space-between;
    background:linear-gradient(135deg,#A8E6CF,#7FD1C1);
    border-radius:18px; padding:8px 14px; margin-bottom:8px;
    color:#1b4332; font-weight:800; font-size:17px;
    box-shadow:0 3px 10px rgba(127,209,193,.35);
}
.topbar small { font-weight:600; font-size:11px; opacity:.85; }

/* 냉장고 바디 */
.fridge {
    background:linear-gradient(160deg,#F7FBFA,#E7F3F0);
    border:3px solid #CFE3DD; border-radius:26px;
    padding:10px 8px 6px 8px; box-shadow:inset 0 2px 8px rgba(0,0,0,.05);
}
/* 칸 버튼 */
div[data-testid="column"] .stButton > button {
    width:100%; border-radius:20px; border:2px solid #E3EFEA;
    background:#FFFFFF; color:#2d3a35; font-weight:700; font-size:13px;
    padding:10px 2px; line-height:1.35; min-height:74px;
    box-shadow:0 2px 6px rgba(0,0,0,.06); transition:.15s;
}
div[data-testid="column"] .stButton > button:hover {
    transform:translateY(-2px); border-color:#7FD1C1; color:#13795f;
}
/* 사이드 아이콘 */
.sideicon .stButton > button {
    min-height:44px !important; font-size:18px !important; padding:4px !important;
    border-radius:16px !important; background:#FFFDF6 !important;
    border:2px solid #FFE9A8 !important;
}
.card {
    background:#fff; border-radius:18px; padding:10px 12px; margin-bottom:7px;
    box-shadow:0 2px 7px rgba(0,0,0,.07); font-size:13px;
}
.gauge-bg { background:#EDF1EF; border-radius:10px; height:9px; width:100%; overflow:hidden; }
.gauge-fl { height:9px; border-radius:10px; }
.badge {
    display:inline-block; padding:1px 8px; border-radius:999px;
    font-size:10.5px; font-weight:800; color:#fff;
}
.chr {
    width:46px; height:46px; border-radius:50%; display:flex;
    align-items:center; justify-content:center; font-size:24px;
    border:2.5px solid #fff; box-shadow:0 2px 6px rgba(0,0,0,.14);
}
.hint { font-size:11px; color:#8b9690; text-align:center; margin-top:4px; }
.stButton > button:focus { box-shadow:none !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 데이터 저장/로드
# ──────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"items": [], "shopping": [], "allergies": [], "seen_shopping": True}


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "items": st.session_state.items,
                "shopping": st.session_state.shopping,
                "allergies": st.session_state.allergies,
                "seen_shopping": st.session_state.seen_shopping,
            }, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


if "items" not in st.session_state:
    d = load_data()
    st.session_state.items = d.get("items", [])
    st.session_state.shopping = d.get("shopping", [])
    st.session_state.allergies = d.get("allergies", [])
    st.session_state.seen_shopping = d.get("seen_shopping", True)
    st.session_state.screen = "home"
    st.session_state.zone = None
    st.session_state.sel = None
    st.session_state.draft = None
    st.session_state.imgcache = {}


def go(screen, **kw):
    st.session_state.screen = screen
    for k, v in kw.items():
        st.session_state[k] = v
    st.rerun()


# ──────────────────────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────────────────────
def days_left(item):
    return (dt.date.fromisoformat(item["expire"]) - TODAY).days


def life_info(item):
    """생명력 게이지 비율과 색/문구/표정"""
    total = max(item.get("total_days", 7), 1)
    left = days_left(item)
    ratio = max(0.0, min(1.0, left / total))
    if left < 0:
        return 0.0, "#B0B7B4", "만료", "💀"
    if left <= 1:
        return max(ratio, .07), "#E5484D", "위급", "😵"
    if left <= 3:
        return max(ratio, .2), "#F76808", "임박", "😰"
    if left <= 7:
        return max(ratio, .4), "#F5C518", "주의", "🙂"
    return ratio, "#30A46C", "신선", "😄"


def guess_food(name):
    """이름으로 칸/기한/이모지/팁 추론"""
    if name in FOOD_DB:
        return FOOD_DB[name]
    for k, v in FOOD_DB.items():
        if k in name or name in k:
            return v
    return ("side", 7, "🍽️", "밀폐용기에 담아 냉장 보관하고 3~5일 안에 드세요.")


def char_html(item, size=46):
    """재료 대표 캐릭터 — AI 이미지가 있으면 그걸, 없으면 신선도 반응형 캐릭터"""
    url = st.session_state.imgcache.get(item["name"])
    _, color, _, face = life_info(item)
    if url:
        return (f"<img src='{url}' style='width:{size}px;height:{size}px;border-radius:50%;"
                f"object-fit:cover;border:2.5px solid {color};'>")
    emoji = item.get("emoji", "🍽️")
    tint = {"#30A46C": "#DFF5E9", "#F5C518": "#FFF6D6", "#F76808": "#FFE6D5",
            "#E5484D": "#FFE0E1", "#B0B7B4": "#ECEFEE"}[color]
    return (f"<div class='chr' style='background:{tint};width:{size}px;height:{size}px;"
            f"font-size:{int(size*0.52)}px;border-color:{color};position:relative;'>{emoji}"
            f"<span style='position:absolute;right:-3px;bottom:-3px;font-size:{int(size*0.34)}px;'>{face}</span></div>")


def gauge_html(item):
    ratio, color, label, _ = life_info(item)
    left = days_left(item)
    txt = f"D-{left}" if left > 0 else ("오늘까지" if left == 0 else f"{-left}일 지남")
    return (f"<div style='display:flex;justify-content:space-between;font-size:11px;"
            f"color:#6b7672;margin:3px 0 2px;'><span>{txt}</span>"
            f"<span class='badge' style='background:{color}'>{label}</span></div>"
            f"<div class='gauge-bg'><div class='gauge-fl' style='width:{ratio*100:.0f}%;background:{color}'></div></div>")


def blocked_by_allergy(name):
    for a in st.session_state.allergies:
        for bad in ALLERGY_MAP.get(a, []):
            if bad in name or name in bad:
                return a
    return None


def ai_available():
    key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    return bool(key), key


def ai_recognize(image_bytes):
    """사진 → 음식명/칸/예상 소비기한 (실패 시 None)"""
    ok, key = ai_available()
    if not ok:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        b64 = base64.b64encode(image_bytes).decode()
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": [
                {"type": "text", "text":
                    "사진 속 식재료를 식별해 JSON만 출력. 형식: "
                    '{"name":"한국어 재료명","zone":"veg|meat|dairy|fruit|side|frozen",'
                    '"days":숫자(구입일 기준 권장 소비기한),"emoji":"이모지 1개"}'},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
            max_tokens=120,
        )
        t = r.choices[0].message.content.strip()
        t = t[t.find("{"): t.rfind("}") + 1]
        return json.loads(t)
    except Exception:
        return None


def ai_character(name):
    """재료 대표 캐릭터 이미지 실시간 생성 (실패해도 앱은 정상 동작)"""
    ok, key = ai_available()
    if not ok or name in st.session_state.imgcache:
        return
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        r = client.images.generate(
            model="gpt-image-1", size="1024x1024",
            prompt=(f"귀엽고 동글동글한 '{name}' 캐릭터 마스코트, 파스텔 민트 배경, "
                    "단순한 플랫 일러스트, 큰 눈, 웃는 얼굴, 텍스트 없음, 중앙 배치"),
        )
        st.session_state.imgcache[name] = "data:image/png;base64," + r.data[0].b64_json
    except Exception:
        pass


def add_item(name, zone, total_days, emoji, qty, memo, buy_date):
    st.session_state.items.append({
        "id": hashlib.md5(f"{name}{dt.datetime.now()}".encode()).hexdigest()[:8],
        "name": name, "zone": zone, "emoji": emoji, "qty": qty, "memo": memo,
        "buy": buy_date.isoformat(),
        "expire": (buy_date + dt.timedelta(days=int(total_days))).isoformat(),
        "total_days": int(total_days),
        "opened": False,
    })
    save_data()


def topbar(title, sub=""):
    st.markdown(f"<div class='topbar'><div>{title}<br><small>{sub}</small></div>"
                f"<div style='font-size:22px'>🧊</div></div>", unsafe_allow_html=True)


def back_button(to="home"):
    if st.button("‹ 뒤로", use_container_width=True, key=f"back_{st.session_state.screen}"):
        go(to)


# ──────────────────────────────────────────────────────────────
# 화면 1. 홈 — 냉장고
# ──────────────────────────────────────────────────────────────
def screen_home():
    items = st.session_state.items
    urgent = [i for i in items if days_left(i) <= 3]
    topbar("우리집 냉장고", f"재료 {len(items)}개 · 임박 {len(urgent)}개")

    side, main = st.columns([1, 4.4], gap="small")

    with side:
        st.markdown("<div class='sideicon'>", unsafe_allow_html=True)
        if st.button("🍳", key="s_recipe", help="임박 재료 우선 레시피", use_container_width=True):
            go("recipe")
        if st.button("🥢", key="s_half", help="남은 반쪽 소비 레시피", use_container_width=True):
            go("half")
        badge = "❗" if (st.session_state.shopping and not st.session_state.seen_shopping) else "📝"
        if st.button(badge, key="s_shop", help="장보기 메모", use_container_width=True):
            st.session_state.seen_shopping = True
            save_data()
            go("shop")
        if st.button("🔍", key="s_find", help="집에 이거 있나? (장보는 중 확인)", use_container_width=True):
            go("find")
        if st.button("🚫", key="s_allergy", help="알레르기 설정", use_container_width=True):
            go("allergy")
        if st.button("💡", key="s_tip", help="보관법 팁", use_container_width=True):
            go("tips")
        st.markdown("</div>", unsafe_allow_html=True)

    with main:
        st.markdown("<div class='fridge'>", unsafe_allow_html=True)
        keys = list(ZONES.keys())
        for row in range(3):
            c = st.columns(2, gap="small")
            for j in range(2):
                z = keys[row * 2 + j]
                zi = ZONES[z]
                n = len([i for i in items if i["zone"] == z])
                warn = len([i for i in items if i["zone"] == z and days_left(i) <= 3])
                mark = f"  ❗{warn}" if warn else ""
                with c[j]:
                    if st.button(f"{zi['emoji']}\n\n{zi['name']}\n{n}개{mark}",
                                 key=f"z_{z}", use_container_width=True):
                        go("zone", zone=z)
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("＋ 재료 넣기", use_container_width=True, type="primary", key="add_main"):
            go("add", zone="veg")

    st.markdown("<div class='hint'>칸을 누르면 재료를 볼 수 있어요 · 왼쪽 아이콘은 추가 기능</div>",
                unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 화면 2. 칸 상세
# ──────────────────────────────────────────────────────────────
def screen_zone():
    z = st.session_state.zone
    zi = ZONES[z]
    items = sorted([i for i in st.session_state.items if i["zone"] == z], key=days_left)
    topbar(f"{zi['emoji']} {zi['name']}", f"{len(items)}개 보관 중")

    if not items:
        st.markdown("<div class='card' style='text-align:center;padding:26px 10px;'>"
                    "텅 비었어요 🫙<br><span style='font-size:11.5px;color:#8b9690'>"
                    "아래에서 재료를 넣어보세요</span></div>", unsafe_allow_html=True)
    for it in items[:6]:
        c1, c2 = st.columns([1, 4.2], gap="small")
        with c1:
            st.markdown(char_html(it), unsafe_allow_html=True)
        with c2:
            st.markdown(f"<b style='font-size:13.5px'>{it['name']}</b> "
                        f"<span style='font-size:11px;color:#8b9690'>{it.get('qty','')}</span>"
                        f"{gauge_html(it)}", unsafe_allow_html=True)
            if st.button("상세 보기", key=f"d_{it['id']}", use_container_width=True):
                go("detail", sel=it["id"])
    if len(items) > 6:
        st.markdown(f"<div class='hint'>외 {len(items)-6}개 더 있어요</div>", unsafe_allow_html=True)

    a, b = st.columns(2, gap="small")
    with a:
        if st.button("＋ 여기에 넣기", use_container_width=True, type="primary", key="add_z"):
            go("add", zone=z)
    with b:
        back_button()


# ──────────────────────────────────────────────────────────────
# 화면 3. 재료 등록 (사진 자동인식 + 수정 가능)
# ──────────────────────────────────────────────────────────────
def screen_add():
    topbar("재료 넣기", "사진을 찍으면 자동으로 채워져요")
    ok, _ = ai_available()

    tab_cam, tab_hand = st.tabs(["📷 사진으로", "✍️ 직접 입력"])

    with tab_cam:
        up = st.file_uploader("재료 사진", type=["jpg", "jpeg", "png"],
                              label_visibility="collapsed", key="up")
        if up and st.button("🔎 자동 인식하기", use_container_width=True, type="primary"):
            with st.spinner("사진을 보는 중…"):
                r = ai_recognize(up.getvalue())
            if r:
                st.session_state.draft = r
                st.success(f"'{r.get('name')}' 로 인식했어요. 아래에서 고칠 수 있어요.")
            else:
                st.session_state.draft = {"name": "", "zone": st.session_state.zone,
                                          "days": 7, "emoji": "🍽️"}
                st.warning("자동 인식을 못 했어요. 아래에 직접 적어주세요." if ok
                           else "자동 인식은 OPENAI_API_KEY가 있을 때 작동해요. 직접 입력해 주세요.")

    with tab_hand:
        st.caption("자주 넣는 재료는 한 번에 선택할 수 있어요")
        pick = st.selectbox("빠른 선택", ["직접 입력"] + list(FOOD_DB.keys()),
                            label_visibility="collapsed")
        if pick != "직접 입력":
            z, d, e, _ = FOOD_DB[pick]
            st.session_state.draft = {"name": pick, "zone": z, "days": d, "emoji": e}

    df = st.session_state.draft or {"name": "", "zone": st.session_state.zone or "veg",
                                    "days": 7, "emoji": "🍽️"}

    with st.form("f_add", clear_on_submit=False):
        name = st.text_input("이름", df.get("name", ""), placeholder="예) 대파")
        c1, c2 = st.columns(2)
        zlist = list(ZONES.keys())
        zidx = zlist.index(df.get("zone")) if df.get("zone") in zlist else 0
        with c1:
            zone = st.selectbox("칸", zlist, index=zidx,
                                format_func=lambda k: f"{ZONES[k]['emoji']} {ZONES[k]['name']}")
        with c2:
            qty = st.text_input("수량", "1개")
        c3, c4 = st.columns(2)
        with c3:
            buy = st.date_input("구입일", TODAY)
        with c4:
            days = st.number_input("소비기한(일)", 1, 720, int(df.get("days", 7)))
        memo = st.text_input("메모", "", placeholder="개봉함 / 반만 씀 등")
        sub = st.form_submit_button("냉장고에 넣기 🧊", use_container_width=True, type="primary")

    if sub:
        if not name.strip():
            st.error("이름을 적어주세요.")
        else:
            g = guess_food(name.strip())
            add_item(name.strip(), zone, days, df.get("emoji") or g[2], qty, memo, buy)
            if ok:
                with st.spinner("캐릭터를 그리는 중…"):
                    ai_character(name.strip())
            st.session_state.draft = None
            bad = blocked_by_allergy(name.strip())
            if bad:
                st.warning(f"⚠️ 가족 알레르기 '{bad}' 관련 재료예요.")
            st.success(f"{name} 넣었어요! 보관법: {g[3]}")
            st.session_state.last_tip = (name.strip(), g[3])
            go("zone", zone=zone)

    back_button()


# ──────────────────────────────────────────────────────────────
# 화면 4. 재료 상세
# ──────────────────────────────────────────────────────────────
def screen_detail():
    it = next((i for i in st.session_state.items if i["id"] == st.session_state.sel), None)
    if not it:
        go("home")
    ratio, color, label, face = life_info(it)
    g = guess_food(it["name"])
    topbar(f"{it['name']}", f"{ZONES[it['zone']]['name']} · {label}")

    c1, c2 = st.columns([1, 3], gap="small")
    with c1:
        st.markdown(char_html(it, 62), unsafe_allow_html=True)
    with c2:
        st.markdown(gauge_html(it), unsafe_allow_html=True)

    st.markdown(
        f"<div class='card'>"
        f"🗓 구입일 <b>{it['buy']}</b><br>"
        f"⏰ 소비기한 <b>{it['expire']}</b> (총 {it['total_days']}일)<br>"
        f"📦 수량 <b>{it.get('qty','-')}</b><br>"
        f"📝 메모 {it.get('memo') or '-'}<br>"
        f"💡 <b>보관법</b> {g[3]}</div>", unsafe_allow_html=True)

    bad = blocked_by_allergy(it["name"])
    if bad:
        st.error(f"🚫 알레르기 주의 — {bad}")

    c3, c4 = st.columns(2, gap="small")
    with c3:
        if st.button("🍽 다 먹었어요", use_container_width=True):
            st.session_state.items = [x for x in st.session_state.items if x["id"] != it["id"]]
            if it["name"] not in st.session_state.shopping:
                st.session_state.shopping.append(it["name"])
                st.session_state.seen_shopping = False
            save_data()
            go("shop")
    with c4:
        if st.button("✏️ 기한 수정", use_container_width=True):
            st.session_state.edit = True
    if st.session_state.get("edit"):
        nd = st.date_input("새 소비기한", dt.date.fromisoformat(it["expire"]))
        if st.button("저장", use_container_width=True, type="primary"):
            it["expire"] = nd.isoformat()
            it["total_days"] = max((nd - dt.date.fromisoformat(it["buy"])).days, 1)
            st.session_state.edit = False
            save_data()
            st.rerun()

    back_button("zone")


# ──────────────────────────────────────────────────────────────
# 화면 5. 임박 재료 우선 레시피
# ──────────────────────────────────────────────────────────────
def screen_recipe():
    items = st.session_state.items
    have = {i["name"] for i in items}
    urgent = {i["name"] for i in items if days_left(i) <= 3}
    topbar("오늘 뭐 해먹지", f"임박 재료 {len(urgent)}개 우선")

    scored = []
    for r in RECIPES:
        if any(blocked_by_allergy(x) for x in r["ing"]):
            continue
        hit = [x for x in r["ing"] if any(x in h or h in x for h in have)]
        miss = [x for x in r["ing"] if x not in hit]
        u = len([x for x in hit if x in urgent])
        if hit:
            scored.append((u * 10 + len(hit) - len(miss) * 2, r, hit, miss, u))
    scored.sort(key=lambda x: -x[0])

    if not scored:
        st.markdown("<div class='card' style='text-align:center;padding:24px'>"
                    "재료를 조금 더 넣어주세요 🥲</div>", unsafe_allow_html=True)
    for _, r, hit, miss, u in scored[:4]:
        tag = ("<span class='badge' style='background:#E5484D'>임박 소비</span>" if u else "")
        mis = ("<br><span style='color:#c2410c;font-size:11.5px'>+ 필요: "
               + ", ".join(miss) + "</span>") if miss else \
              "<br><span style='color:#30A46C;font-size:11.5px'>✓ 재료 다 있어요</span>"
        st.markdown(
            f"<div class='card'><b style='font-size:14px'>{r['emoji']} {r['name']}</b> {tag}"
            f"<span style='float:right;font-size:11px;color:#8b9690'>{r['time']}</span>"
            f"<br><span style='font-size:11.5px;color:#55605b'>사용: {', '.join(hit)}</span>{mis}</div>",
            unsafe_allow_html=True)
        if miss and st.button(f"🛒 부족한 재료 담기", key=f"rb_{r['name']}", use_container_width=True):
            for m in miss:
                if m not in st.session_state.shopping:
                    st.session_state.shopping.append(m)
            st.session_state.seen_shopping = False
            save_data()
            st.toast("장보기 메모에 담았어요")
    back_button()


# ──────────────────────────────────────────────────────────────
# 화면 6. 남은 반쪽 소비 레시피
# ──────────────────────────────────────────────────────────────
def screen_half():
    topbar("남은 반쪽 구하기", "한 번에 다 못 쓰는 재료 전용")
    targets = [i for i in st.session_state.items
               if i["name"] in HALF_FOODS or "반" in (i.get("memo") or "")]
    if not targets:
        st.markdown("<div class='card' style='text-align:center;padding:22px'>"
                    "대파·양배추·두부처럼 남기 쉬운 재료가 아직 없어요 🌿<br>"
                    "<span style='font-size:11.5px;color:#8b9690'>넣어두면 소비 레시피를 모아드릴게요</span>"
                    "</div>", unsafe_allow_html=True)
    for t in targets[:3]:
        uses = [r for r in RECIPES if any(t["name"] in x or x in t["name"] for x in r["ing"])]
        chips = " ".join(f"{r['emoji']}{r['name']}" for r in uses[:4]) or "자유롭게 활용해 보세요"
        st.markdown(
            f"<div class='card'><b>{t.get('emoji','🍽️')} {t['name']}</b>"
            f"<span style='float:right;font-size:11px;color:#8b9690'>D-{days_left(t)}</span>"
            f"<br><span style='font-size:12px'>{chips}</span>"
            f"<br><span style='font-size:11.5px;color:#13795f'>💡 {guess_food(t['name'])[3]}</span></div>",
            unsafe_allow_html=True)
    back_button()


# ──────────────────────────────────────────────────────────────
# 화면 7. 장보기 메모
# ──────────────────────────────────────────────────────────────
def screen_shop():
    topbar("장보기 메모", f"{len(st.session_state.shopping)}개 담김")
    new = st.text_input("추가", "", placeholder="살 것 적고 Enter",
                        label_visibility="collapsed")
    if new:
        if new not in st.session_state.shopping:
            st.session_state.shopping.append(new)
            save_data()
            st.rerun()
    for s in list(st.session_state.shopping)[:9]:
        c1, c2 = st.columns([5, 1], gap="small")
        c1.markdown(f"<div class='card' style='margin-bottom:4px'>🛒 {s}</div>",
                    unsafe_allow_html=True)
        if c2.button("✓", key=f"sh_{s}", use_container_width=True):
            st.session_state.shopping.remove(s)
            save_data()
            st.rerun()
    if not st.session_state.shopping:
        st.markdown("<div class='card' style='text-align:center;padding:22px'>"
                    "메모가 비었어요 ✨</div>", unsafe_allow_html=True)
    back_button()


# ──────────────────────────────────────────────────────────────
# 화면 8. 집에 이거 있나? (가족 공유용 빠른 확인)
# ──────────────────────────────────────────────────────────────
def screen_find():
    topbar("집에 이거 있나?", "마트에서 바로 확인하세요")
    q = st.text_input("검색", "", placeholder="예) 계란", label_visibility="collapsed")
    if q:
        hits = [i for i in st.session_state.items if q in i["name"] or i["name"] in q]
        if hits:
            for h in hits:
                st.markdown(f"<div class='card'><b style='color:#13795f'>✅ 있어요 — {h['name']}</b> "
                            f"({h.get('qty','')})<br><span style='font-size:11.5px;color:#55605b'>"
                            f"{ZONES[h['zone']]['name']} · D-{days_left(h)}</span></div>",
                            unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='card'><b style='color:#c2410c'>❌ 없어요 — {q}</b><br>"
                        f"<span style='font-size:11.5px;color:#55605b'>사 오시면 좋겠어요</span></div>",
                        unsafe_allow_html=True)
            if st.button("🛒 장보기 메모에 담기", use_container_width=True, type="primary"):
                st.session_state.shopping.append(q)
                st.session_state.seen_shopping = False
                save_data()
                go("shop")
    back_button()


# ──────────────────────────────────────────────────────────────
# 화면 9. 알레르기 설정
# ──────────────────────────────────────────────────────────────
def screen_allergy():
    topbar("알레르기 설정", "추천 레시피에서 자동으로 빼드려요")
    sel = st.multiselect("우리 가족이 못 먹는 것", list(ALLERGY_MAP.keys()),
                         default=st.session_state.allergies, label_visibility="collapsed")
    if st.button("저장", use_container_width=True, type="primary"):
        st.session_state.allergies = sel
        save_data()
        st.success("저장했어요. 레시피 추천에 바로 반영돼요.")
    risky = [i["name"] for i in st.session_state.items if blocked_by_allergy(i["name"])]
    if risky:
        st.markdown(f"<div class='card'>⚠️ 냉장고 속 주의 재료<br>"
                    f"<b>{', '.join(risky[:8])}</b></div>", unsafe_allow_html=True)
    back_button()


# ──────────────────────────────────────────────────────────────
# 화면 10. 보관법 팁
# ──────────────────────────────────────────────────────────────
def screen_tips():
    topbar("보관법 팁", "지금 냉장고에 있는 재료 기준")
    mine = st.session_state.items[:5]
    if not mine:
        for n in ["대파", "계란", "두부", "감자"]:
            st.markdown(f"<div class='card'><b>{FOOD_DB[n][2]} {n}</b><br>"
                        f"<span style='font-size:12px'>{FOOD_DB[n][3]}</span></div>",
                        unsafe_allow_html=True)
    for it in mine:
        st.markdown(f"<div class='card'><b>{it.get('emoji','🍽️')} {it['name']}</b><br>"
                    f"<span style='font-size:12px'>{guess_food(it['name'])[3]}</span></div>",
                    unsafe_allow_html=True)
    back_button()


# ──────────────────────────────────────────────────────────────
# 라우터
# ──────────────────────────────────────────────────────────────
SCREENS = {
    "home": screen_home, "zone": screen_zone, "add": screen_add, "detail": screen_detail,
    "recipe": screen_recipe, "half": screen_half, "shop": screen_shop,
    "find": screen_find, "allergy": screen_allergy, "tips": screen_tips,
}
SCREENS.get(st.session_state.screen, screen_home)()
