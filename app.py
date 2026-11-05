"""나의 근무 달력 — 유형과 시작일만 고르는 Streamlit 앱.

배포 파일: app.py / requirements.txt (Python 3.11 또는 3.12 권장)

설치: python -m pip install -r requirements.txt
실행: python -m streamlit run app.py --browser.gatherUsageStats=false
GitHub: 두 파일을 저장소에 올리고 Streamlit에서 실행 파일을 app.py로 지정합니다.
기존 앱을 교체할 때는 실행 파일 경로를 확인한 뒤 앱을 재시작하세요.

이 앱은 계정, 비밀번호, 외부 저장소, API 키, 환경변수를 사용하지 않습니다.
근무표는 날짜 차이를 반복 주기로 나누어 계산합니다. 저장/연결 설정이 없습니다.
선택값은 현재 페이지 주소의 쿼리 문자열에 반영됩니다. 주소를 즐겨찾기하면
동일한 유형/시작일/조회 월을 다시 열 수 있습니다. 다른 사람과도 그 주소를
공유할 수 있으므로 주소에는 민감한 정보를 입력하지 마세요.

시작일은 반복 순서의 '첫 번째' 근무일입니다. 시작일 이전은 빈칸으로 표시합니다.
프리셋은 예시일 뿐이며 '4조 2교대' 등의 공식 표준을 뜻하지 않습니다.
회사마다 순서가 다르면 '직접 정하기'에서 실제 순서를 입력하세요.
주말에도 동일하게 반복하며 공휴일/대체근무/휴가/근무시간은 계산하지 않습니다.
날짜 선택/조회 범위: 1900-01-01 ~ 2199-12-31. 오늘은 한국 시간 기준입니다.

인터넷 없이 사용: 최초 설치는 인터넷이 필요합니다. 이후 PC에서 실행할 때는
외부 서비스에 연결하지 않습니다. 휴대폰에서 접속하려면 실행 중인 PC와
같은 Wi-Fi/LAN에 연결하고 아래 명령을 사용합니다.
python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --browser.gatherUsageStats=false
접속: http://실제-PC의-WiFi-IP:8501 (localhost는 PC 자체 접속용입니다.)
HTTP이므로 신뢰하는 사설 네트워크에서만 사용하세요. PC를 끄면 접속되지 않습니다.
Streamlit Cloud로 배포하면 인터넷이 필요하며, 휴대폰 단독 설치 앱은 아닙니다.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html import escape
from typing import Mapping

import streamlit as st

MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2199, 12, 31)
KST = timezone(timedelta(hours=9))
CUSTOM_ID = "custom"
DEFAULT_CUSTOM = "주주야야비휴"

SHIFT_LABELS = {"day": "주간", "night": "야간", "off": "비번", "rest": "휴무"}
ALIASES = {
    "주": "day", "주간": "day",
    "야": "night", "야간": "night",
    "비": "off", "비번": "off",
    "휴": "rest", "휴무": "rest",
}
WEEKDAYS = ("일", "월", "화", "수", "목", "금", "토")
WEEKDAY_LONG = ("월", "화", "수", "목", "금", "토", "일")


@dataclass(frozen=True)
class Preset:
    id: str
    label: str
    pattern: tuple[str, ...]


PRESETS = (
    Preset("4d", "4일 · 주야비휴", ("day", "night", "off", "rest")),
    Preset("4day", "4일 · 주주휴휴", ("day", "day", "rest", "rest")),
    Preset("4night", "4일 · 야야휴휴", ("night", "night", "rest", "rest")),
    Preset("6off", "6일 · 주주야야비휴", ("day", "day", "night", "night", "off", "rest")),
    Preset("6rest", "6일 · 주주야야휴휴", ("day", "day", "night", "night", "rest", "rest")),
    Preset("8d", "8일 · 주주야야비비휴휴", ("day", "day", "night", "night", "off", "off", "rest", "rest")),
    Preset("2d", "2일 · 주야", ("day", "night")),
    Preset("3d", "3일 · 주야휴", ("day", "night", "rest")),
)
PRESET_BY_ID = {p.id: p for p in PRESETS}
OPTIONS = tuple(PRESET_BY_ID) + (CUSTOM_ID,)

CSS = """
<style>
:root { color-scheme: light; }
.stApp, [data-testid="stAppViewContainer"] { background:#F4F7FA; color:#1C2E44; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stMainBlockContainer"] {
    max-width:760px; padding-top:3.4rem; padding-bottom:1.4rem;
    font-family:system-ui,-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;
}
[data-testid="stVerticalBlock"] { gap:0.75rem; }
[data-testid="stWidgetLabel"] p { color:#1C2E44 !important; font-size:13px; font-weight:650; }
[data-testid="stCaptionContainer"] p { color:#53657A !important; font-size:12px; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stDateInput"] [data-baseweb="input"] {
    background:#FFFFFF !important; color:#1C2E44 !important;
    border-color:#D8E2EB !important; border-radius:11px !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stDateInput"] input { color:#1C2E44 !important; font-size:13px !important; }
[data-testid="stDateInput"] input { background:#FFFFFF !important; }
[data-testid="stSelectbox"] [data-baseweb="select"] svg,
[data-testid="stDateInput"] svg { fill:#53657A !important; }
.st-key-settings {
    border:1px solid #DFE7EE !important; background:#FFFFFF;
    border-radius:18px !important; padding:16px !important;
}
.st-key-settings [data-testid="stHorizontalBlock"] {
    flex-wrap:nowrap !important; gap:12px !important;
}
.st-key-settings [data-testid="stColumn"] {
    min-width:0 !important; width:0 !important;
}
.st-key-settings [data-testid="stColumn"]:first-child { flex:1.45 1 0 !important; }
.st-key-settings [data-testid="stColumn"]:last-child { flex:1 1 0 !important; }
.st-key-navigation [data-testid="stHorizontalBlock"] {
    flex-wrap:nowrap !important; gap:8px !important; align-items:center;
}
.st-key-navigation [data-testid="stColumn"] {
    min-width:0 !important; width:0 !important; flex:1 1 0 !important;
}
.st-key-navigation [data-testid="stColumn"]:nth-child(2) { flex:2.65 1 0 !important; }
.st-key-navigation button {
    min-height:42px; padding:0 5px; width:100%; background:#FFFFFF !important;
    border:1px solid #D8E2EB !important; color:#1C2E44 !important; border-radius:11px;
}
.st-key-navigation button p { font-size:12px !important; color:inherit !important; white-space:nowrap; }
.st-key-navigation button:hover:not(:disabled) { border-color:#17675D !important; background:#ECF6F3 !important; }
.st-key-navigation button:disabled { opacity:.4; }
.st-key-navigation button:focus-visible { outline:3px solid #17675D; outline-offset:2px; }
.sc-heading { margin:0 0 3px; color:#1C2E44; font-size:28px; letter-spacing:-1.1px; line-height:1.25; font-weight:800; }
.sc-heading-mark {
    display:inline-block; width:22px; height:23px; margin-right:9px; vertical-align:-2px;
    border:2px solid #17675D; border-radius:6px; position:relative; background:#FFFFFF;
}
.sc-heading-mark:before {
    content:''; position:absolute; top:5px; left:0; right:0; border-top:2px solid #17675D;
}
.sc-heading-mark:after {
    content:''; position:absolute; width:5px; height:5px; left:5px; top:11px;
    border-radius:2px; background:#17675D; box-shadow:7px 0 0 #BEDCD4;
}
.sc-subtitle { color:#53657A; font-size:13px; line-height:1.6; margin:0 0 4px; }
.sc-sequence { display:flex; flex-wrap:wrap; align-items:center; gap:5px; margin-top:1px; }
.sc-chip { display:inline-block; padding:4px 8px; border-radius:7px; font-size:11px; line-height:1.5; font-weight:700; white-space:nowrap; }
.sc-arrow { color:#697B8E; font-size:11px; }
.sc-repeat { color:#53657A; font-size:11px; margin-left:4px; white-space:nowrap; }
.sc-explain { color:#53657A; font-size:11px; margin-top:8px; line-height:1.5; }
.sc-month { color:#1C2E44; font-size:21px; line-height:42px; text-align:center; margin:0; font-weight:800; letter-spacing:-.6px; white-space:nowrap; }
.sc-calendar { background:#FFFFFF; border:1px solid #DFE7EE; border-radius:18px; padding:10px 9px 6px; }
.sc-calendar table { width:100%; border-collapse:collapse; table-layout:fixed; border:0; margin:0; color:#1C2E44; }
.sc-calendar th, .sc-calendar td { border:0; text-align:center; padding:0; }
.sc-calendar th { height:32px; font-size:11px; color:#53657A; font-weight:650; }
.sc-calendar th:first-child, .sc-calendar .sc-sunday .sc-date { color:#AD3E48; }
.sc-calendar th:last-child, .sc-calendar .sc-saturday .sc-date { color:#315F9D; }
.sc-calendar td { height:68px; vertical-align:top; border-top:1px solid #EDF1F5; }
.sc-cell { display:flex; flex-direction:column; align-items:center; justify-content:flex-start; padding:6px 1px; gap:4px; }
.sc-date { display:inline-flex; width:25px; height:25px; align-items:center; justify-content:center; font-size:13px; font-weight:600; font-variant-numeric:tabular-nums; }
.sc-today .sc-date { color:#FFFFFF !important; background:#17675D; border-radius:50%; font-weight:800; }
.sc-badge { display:inline-block; min-width:34px; box-sizing:border-box; padding:3px 6px; border-radius:7px; font-size:11px; line-height:1.4; font-weight:700; white-space:nowrap; }
.sc-day { color:#865000; background:#FFF1D4; }
.sc-night { color:#2D4A7E; background:#E8EEFF; }
.sc-off { color:#17675D; background:#E3F4ED; }
.sc-rest { color:#52617A; background:#EDF1F6; }
.sc-before { color:#8492A2; font-size:13px; line-height:22px; }
.sc-footnote { display:flex; flex-wrap:wrap; gap:5px 14px; color:#53657A; font-size:11px; line-height:1.6; }
.sc-dot { display:inline-block; height:7px; width:7px; margin-right:4px; border-radius:50%; background:#17675D; }
.sc-sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }
@media (max-width:640px) {
    [data-testid="stMainBlockContainer"] { padding:2.8rem 14px 1rem; }
    .sc-heading { font-size:25px; }
    .st-key-settings { padding:13px !important; }
    .sc-calendar { padding:7px 4px 3px; border-radius:16px; }
    .sc-calendar td { height:57px; }
    .sc-cell { padding:4px 0; gap:3px; }
    .sc-date { width:22px; height:22px; font-size:12px; }
    .sc-badge { min-width:31px; padding:3px 4px; font-size:10px; border-radius:6px; }
    .sc-month { font-size:18px; }
}
@media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto !important; } }
</style>
"""


def today_kst() -> date:
    return min(max(datetime.now(KST).date(), MIN_DATE), MAX_DATE)


def parse_pattern(raw: str) -> tuple[str, ...]:
    """Accept compact codes or full labels, never interpreting executable content."""
    if not isinstance(raw, str) or len(raw) > 240:
        raise ValueError("반복 순서는 31일 이내로 입력해 주세요.")
    text = raw.strip()
    if not text:
        raise ValueError("반복 순서를 입력해 주세요. 예: 주주야야비휴")
    text = re.sub(r"주간|야간|비번|휴무", lambda m: m.group(0)[0], text)
    text = re.sub(r"[\s,，/·→>\-]+", "", text)
    if not text or any(ch not in "주야비휴" for ch in text):
        raise ValueError("주·야·비·휴만 사용해 주세요. 예: 주주야야비휴")
    if len(text) > 31:
        raise ValueError("반복 순서는 1~31일로 입력해 주세요.")
    return tuple(ALIASES[ch] for ch in text)


def shift_on(day: date, start: date, pattern: tuple[str, ...]) -> str | None:
    if not pattern or any(key not in SHIFT_LABELS for key in pattern):
        raise ValueError("올바른 근무 순서가 필요합니다.")
    delta = (day - start).days
    return None if delta < 0 else pattern[delta % len(pattern)]


def month_start(day: date) -> date:
    return day.replace(day=1)


def move_month(day: date, amount: int) -> date:
    index = day.year * 12 + day.month - 1 + amount
    year, month0 = divmod(index, 12)
    if not MIN_DATE.year <= year <= MAX_DATE.year:
        raise ValueError("조회 가능한 날짜 범위를 벗어났습니다.")
    return date(year, month0 + 1, 1)


def safe_date(value: object, default: date) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return default
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return default
    return parsed if MIN_DATE <= parsed <= MAX_DATE else default


def decode_settings(params: Mapping[str, str], today: date) -> tuple[str, date, str, date]:
    preset = params.get("type", PRESETS[0].id)
    if preset not in OPTIONS:
        preset = PRESETS[0].id
    start = safe_date(params.get("start"), today)
    raw = params.get("seq", DEFAULT_CUSTOM)
    try:
        parse_pattern(raw)
    except ValueError:
        raw = DEFAULT_CUSTOM
    raw_month = params.get("month", "")
    viewed = safe_date(raw_month + "-01", month_start(start)) if isinstance(raw_month, str) else month_start(start)
    return preset, start, raw, month_start(viewed)


def pattern_html(pattern: tuple[str, ...], start: date) -> str:
    chips = '<span class="sc-arrow" aria-hidden="true">→</span>'.join(
        f'<span class="sc-chip sc-{key}">{SHIFT_LABELS[key]}</span>' for key in pattern
    )
    first = SHIFT_LABELS[pattern[0]]
    return (
        f'<div class="sc-sequence" aria-label="반복 근무 순서">{chips}'
        f'<span class="sc-repeat">↻ {len(pattern)}일 반복</span></div>'
        f'<div class="sc-explain">{start.month}월 {start.day}일은 '
        f'<strong>첫 번째 {first}</strong>부터 시작해요.</div>'
    )


def calendar_html(viewed: date, start: date, pattern: tuple[str, ...], today: date) -> str:
    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(viewed.year, viewed.month)
    caption = f"{viewed.year}년 {viewed.month}월 근무 달력"
    parts = [
        f'<section class="sc-calendar" aria-label="{caption}">',
        f'<table><caption class="sc-sr-only">{caption}</caption><thead><tr>',
        *(f'<th scope="col">{day}</th>' for day in WEEKDAYS),
        '</tr></thead><tbody>',
    ]
    for week in weeks:
        parts.append('<tr>')
        for weekday, number in enumerate(week):
            if not number:
                parts.append('<td class="sc-empty" aria-hidden="true"></td>')
                continue
            day = date(viewed.year, viewed.month, number)
            shift = shift_on(day, start, pattern)
            classes = ['sc-cell']
            if weekday == 0:
                classes.append('sc-sunday')
            elif weekday == 6:
                classes.append('sc-saturday')
            if day == today:
                classes.append('sc-today')
            label = SHIFT_LABELS[shift] if shift else "시작일 이전"
            description = f"{day.year}년 {day.month}월 {day.day}일 {WEEKDAY_LONG[day.weekday()]}요일, {label}"
            if day == start:
                description += ", 반복 시작일"
            if day == today:
                description += ", 오늘"
            badge = (f'<span class="sc-badge sc-{shift}">{label}</span>' if shift else
                     '<span class="sc-before" aria-label="시작일 이전">—</span>')
            safe_desc = escape(description, quote=True)
            parts.append(
                f'<td aria-label="{safe_desc}" title="{safe_desc}"><div class="{" ".join(classes)}">'
                f'<time class="sc-date" datetime="{day.isoformat()}">{number}</time>{badge}</div></td>'
            )
        parts.append('</tr>')
    parts.append('</tbody></table></section>')
    return ''.join(parts)


def initialize(today: date) -> None:
    if st.session_state.get("_initialized"):
        return
    preset, start, raw, viewed = decode_settings(st.query_params.to_dict(), today)
    st.session_state.update({
        "preset": preset, "start_date": start, "custom_input": raw,
        "_custom_saved": raw, "_month": viewed, "_seen_start": start,
        "_initialized": True,
    })


def navigate(amount: int) -> None:
    st.session_state["_month"] = move_month(st.session_state["_month"], amount)


def go_today() -> None:
    st.session_state["_month"] = month_start(today_kst())


def update_address(preset: str, start: date, viewed: date, raw: str) -> None:
    wanted = {"type": preset, "start": start.isoformat(), "month": viewed.strftime("%Y-%m")}
    if preset == CUSTOM_ID:
        # Only validated shift codes enter the URL, not the original text.
        wanted["seq"] = ''.join(SHIFT_LABELS[key][0] for key in parse_pattern(raw))
    if st.query_params.to_dict() != wanted:
        st.query_params.from_dict(wanted)


def main() -> None:
    st.set_page_config(page_title="나의 근무 달력", page_icon="🗓️", layout="centered")
    today = today_kst()
    initialize(today)
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        '<h1 class="sc-heading"><span class="sc-heading-mark" aria-hidden="true"></span>나의 근무 달력</h1>'
        '<p class="sc-subtitle">유형과 시작일만 고르면, 앞으로의 근무가 한눈에.</p>',
        unsafe_allow_html=True,
    )
    with st.container(key="settings", border=True):
        left, right = st.columns([1.45, 1], gap="small")
        with left:
            preset = st.selectbox(
                "근무 유형", options=OPTIONS, key="preset",
                format_func=lambda key: "직접 정하기" if key == CUSTOM_ID else PRESET_BY_ID[key].label,
            )
        with right:
            start = st.date_input(
                "시작일", min_value=MIN_DATE, max_value=MAX_DATE,
                format="YYYY-MM-DD", key="start_date",
            )
        raw = st.session_state["_custom_saved"]
        if preset == CUSTOM_ID:
            if "custom_input" not in st.session_state:
                st.session_state["custom_input"] = raw
            raw = st.text_input("반복 순서", key="custom_input", max_chars=240, placeholder="예: 주주야야비휴")
            st.session_state["_custom_saved"] = raw
        try:
            pattern = parse_pattern(raw) if preset == CUSTOM_ID else PRESET_BY_ID[preset].pattern
        except ValueError as exc:
            st.warning(str(exc))
            return
        if start is None:
            st.info("시작일을 달력에서 선택해 주세요.")
            return
        st.markdown(pattern_html(pattern, start), unsafe_allow_html=True)
    if start != st.session_state["_seen_start"]:
        st.session_state["_month"] = month_start(start)
        st.session_state["_seen_start"] = start
    viewed = st.session_state["_month"]
    with st.container(key="navigation"):
        prev, title, nxt, current = st.columns([1, 2.65, 1, 1], gap="small")
        with prev:
            st.button("이전", key="previous", help="이전 달", use_container_width=True,
                      on_click=navigate, args=(-1,), disabled=viewed == month_start(MIN_DATE))
        with title:
            st.markdown(f'<h2 class="sc-month">{viewed.year}년 {viewed.month}월</h2>', unsafe_allow_html=True)
        with nxt:
            st.button("다음", key="next", help="다음 달", use_container_width=True,
                      on_click=navigate, args=(1,), disabled=viewed == month_start(MAX_DATE))
        with current:
            st.button("오늘", key="today", help="한국 시간 기준 이번 달", use_container_width=True, on_click=go_today)
    st.markdown(calendar_html(viewed, start, pattern, today), unsafe_allow_html=True)
    st.markdown(
        '<div class="sc-footnote"><span><span class="sc-dot"></span>오늘</span>'
        '<span>주말에도 선택한 순서대로 반복돼요.</span>'
        '<span>선택한 주소를 즐겨찾기하면 설정이 유지돼요.</span></div>',
        unsafe_allow_html=True,
    )
    update_address(preset, start, viewed, raw)


if __name__ == "__main__":
    main()
