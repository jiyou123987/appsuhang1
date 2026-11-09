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

[날짜 메모]
달력의 날짜를 누르면 200자 메모를 작성/확인/수정할 수 있습니다.
메모가 있는 날짜에는 작은 메모 아이콘만 표시하고 본문은 팝업에서만 보여줍니다.
메모는 해당 기기/브라우저/접속 주소의 localStorage에 저장합니다.
앱 새로고침/월 이동 후에도 같은 브라우저에서는 유지되지만, 다른 기기와 공유되지
않으며 브라우저 사이트 데이터 삭제/시크릿 모드 종료/주소 변경 시 유실될 수 있습니다.
메모 본문을 서버, URL, 달력 툴팁으로 전송하지 않습니다. 별도 DB/Secrets는 없습니다.

시작일은 반복 순서의 '첫 번째' 근무일입니다. 시작일 이전은 빈칸으로 표시합니다.
프리셋은 예시일 뿐이며 '4조 2교대' 등의 공식 표준을 뜻하지 않습니다.
회사마다 순서가 다르면 '직접 정하기'에서 실제 순서를 입력한 뒤
'달력에 적용'을 누르세요. 예: 주주주야비휴 → 주간 3일/야간/비번/휴무 반복.
입력 중인 초안과 실제 적용한 순서는 따로 보관하므로 다른 유형을 선택하거나
월을 넘겨도 마지막으로 적용한 직접 입력 순서가 기본값으로 되돌아가지 않습니다.
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
.st-key-custom_pattern_form [data-baseweb="input"] {
    background:#FFFFFF !important; color:#1C2E44 !important;
    border-color:#D8E2EB !important; border-radius:11px !important;
}
.st-key-custom_pattern_form input { background:#FFFFFF !important; color:#1C2E44 !important; font-size:16px !important; }
.st-key-custom_pattern_form [data-testid="stFormSubmitButton"] button {
    background:#17675D !important; border-color:#17675D !important; color:#FFFFFF !important;
    min-height:40px; border-radius:10px;
}
.st-key-custom_pattern_form [data-testid="stFormSubmitButton"] button p { color:#FFFFFF !important; font-size:13px; }
.st-key-custom_pattern_form [data-testid="stFormSubmitButton"] button:focus-visible {
    outline:3px solid #17675D; outline-offset:2px;
}
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
.st-key-navigation [data-testid="stColumn"]:first-child button p,
.st-key-navigation [data-testid="stColumn"]:nth-child(3) button p { font-size:21px !important; line-height:1; }
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
.sc-calendar button.sc-cell {
    appearance:none; position:relative; width:100%; min-height:68px; box-sizing:border-box;
    border:0; margin:0; background:transparent; color:inherit; font-family:inherit; cursor:pointer;
}
.sc-calendar button.sc-cell:hover { background:#F7FAFC; border-radius:8px; }
.sc-calendar button.sc-cell:focus-visible { outline:2px solid #17675D; outline-offset:-2px; border-radius:8px; }
.sc-note-indicator { position:absolute; top:7px; right:3px; width:12px; height:12px; color:#17675D; line-height:0; }
.sc-note-indicator[hidden] { display:none !important; }
.sc-note-indicator svg { width:100%; height:100%; }
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
    .sc-calendar button.sc-cell { min-height:57px; }
    .sc-note-indicator { top:5px; right:1px; width:10px; height:10px; }
    .sc-cell { padding:4px 0; gap:3px; }
    .sc-date { width:22px; height:22px; font-size:12px; }
    .sc-badge { min-width:31px; padding:3px 4px; font-size:10px; border-radius:6px; }
    .sc-month { font-size:18px; }
}
@media (prefers-reduced-motion:reduce) { * { scroll-behavior:auto !important; } }
</style>
"""


MEMO_MAX_CHARS = 200

MEMO_HTML = """
<p id="sc-storage-warning" class="sc-storage-warning" role="status" hidden></p>
<dialog id="sc-note-dialog" aria-labelledby="sc-note-title" aria-describedby="sc-note-help">
  <form id="sc-note-form">
    <div class="sc-note-header">
      <h3 id="sc-note-title">날짜 메모</h3>
      <button id="sc-note-close" type="button" class="sc-note-close" aria-label="메모 닫기">×</button>
    </div>
    <p id="sc-note-help">메모는 이 기기의 브라우저에만 저장돼요.</p>
    <label for="sc-note-text" class="sc-note-label">짧은 메모</label>
    <textarea id="sc-note-text" rows="5" placeholder="이날 기억할 일을 짧게 적어 주세요."></textarea>
    <div class="sc-note-count"><span id="sc-note-count">0 / 200</span></div>
    <p id="sc-note-error" role="alert" hidden></p>
    <div class="sc-note-actions">
      <button id="sc-note-delete" class="sc-note-delete" type="button" hidden>삭제</button>
      <span class="sc-note-spacer"></span>
      <button id="sc-note-cancel" class="sc-note-cancel" type="button">닫기</button>
      <button id="sc-note-save" class="sc-note-save" type="submit">저장</button>
    </div>
  </form>
</dialog>
"""

MEMO_CSS = """
:host { font-family:system-ui,-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif; }
[hidden] { display:none !important; }
.sc-storage-warning { color:#865000; font-size:12px; margin:0; }
#sc-note-dialog {
    box-sizing:border-box; width:min(400px,calc(100vw - 32px)); padding:20px; margin:auto;
    max-height:calc(100dvh - 32px); overflow:auto; border:1px solid #DFE7EE;
    border-radius:18px; background:#FFFFFF; color:#1C2E44; color-scheme:light;
    box-shadow:0 20px 60px #1C2E4429;
    font-family:system-ui,-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;
}
#sc-note-dialog::backdrop { background:#1C2E4466; }
.sc-note-header { display:flex; align-items:center; justify-content:space-between; gap:12px; }
#sc-note-title { font-size:19px; font-weight:800; margin:0; line-height:1.4; letter-spacing:-.5px; }
#sc-note-help { color:#53657A; font-size:12px; line-height:1.6; margin:7px 0 16px; }
.sc-note-label { color:#1C2E44; font-size:13px; font-weight:650; display:block; margin-bottom:7px; }
#sc-note-text {
    box-sizing:border-box; display:block; width:100%; min-height:132px; max-height:40dvh;
    resize:vertical; padding:12px; border:1px solid #D8E2EB; border-radius:11px;
    background:#FFFFFF; color:#1C2E44; font:inherit; font-size:16px; line-height:1.65;
}
#sc-note-text::placeholder { color:#697B8E; }
#sc-note-text:focus { outline:2px solid #17675D; outline-offset:1px; }
.sc-note-count { color:#53657A; font-size:11px; text-align:right; margin:5px 0 12px; font-variant-numeric:tabular-nums; }
#sc-note-error { color:#AD3E48; font-size:12px; line-height:1.6; margin:8px 0 12px; }
.sc-note-actions { display:flex; align-items:center; gap:8px; }
.sc-note-spacer { flex:1; }
button {
    cursor:pointer; font:inherit; font-size:13px; font-weight:650; min-height:42px;
    padding:0 15px; border:1px solid #D8E2EB; border-radius:10px; background:#FFFFFF; color:#1C2E44;
}
button:focus-visible { outline:3px solid #17675D; outline-offset:2px; }
button:disabled { cursor:default; opacity:.45; }
.sc-note-close { padding:0; width:38px; min-height:38px; border:0; font-size:25px; color:#53657A; }
.sc-note-save { background:#17675D; border-color:#17675D; color:#FFFFFF; }
.sc-note-delete { color:#AD3E48; border-color:#EAD9DD; }
.sc-note-save:hover:not(:disabled) { background:#12564E; }
.sc-note-cancel:hover, .sc-note-close:hover { background:#F4F7FA; }
@media (max-width:400px) { #sc-note-dialog { padding:16px; } }
"""

MEMO_JS = r"""
export default function(component) {
    const { parentElement, data } = component;
    const $ = id => parentElement.querySelector('#' + id);
    const dialog = $('sc-note-dialog');
    const form = $('sc-note-form');
    const title = $('sc-note-title');
    const textarea = $('sc-note-text');
    const counter = $('sc-note-count');
    const error = $('sc-note-error');
    const warning = $('sc-storage-warning');
    const save = $('sc-note-save');
    const remove = $('sc-note-delete');
    const maxChars = Number(data?.maxChars) || 200;
    // Same origin + same path, independent of month, preset, start date or query string.
    const prefix = 'shift-calendar:memo:v1:' + window.location.pathname + ':';
    let storage = null;
    let activeDay = null;
    let openedRaw = null;
    let openedText = '';
    let invalidRecord = false;
    let externalChange = false;
    let stopped = false;

    try { storage = window.localStorage; }
    catch (_) { storage = null; }

    function showError(message) {
        error.textContent = message;
        error.hidden = !message;
    }
    function storageWarning() {
        const message = '메모 저장을 사용할 수 없어요. 브라우저의 사이트 저장 허용을 확인해 주세요.';
        // Avoid a childList observer loop when browser storage is blocked.
        if (warning.textContent !== message) warning.textContent = message;
        warning.hidden = false;
    }
    function read(day) {
        if (!storage) throw new Error('Storage unavailable');
        const raw = storage.getItem(prefix + day);
        if (raw === null) return { raw: null, text: '', invalid: false };
        try {
            const item = JSON.parse(raw);
            if (!item || item.version !== 1 || typeof item.text !== 'string' ||
                !item.text.trim() || Array.from(item.text).length > maxChars) {
                return { raw, text: '', invalid: true };
            }
            return { raw, text: item.text, invalid: false };
        } catch (_) { return { raw, text: '', invalid: true }; }
    }
    function refreshMarkers() {
        if (stopped) return;
        let failed = false;
        const buttons = document.querySelectorAll('.sc-calendar [data-sc-memo-day]');
        buttons.forEach(button => {
            let exists = false;
            try { exists = read(button.dataset.scMemoDay).raw !== null; }
            catch (_) { failed = true; }
            const marker = button.querySelector('.sc-note-indicator');
            if (marker) marker.hidden = !exists;
            const base = button.dataset.scBaseLabel || '';
            button.setAttribute('aria-label', base + (exists ? ', 메모 있음, 눌러서 보기' : ', 눌러서 메모 쓰기'));
            // Deliberately never copy memo text into the calendar, tooltip, label or URL.
        });
        if (failed || !storage) storageWarning();
    }
    function updateCounter() {
        const size = Array.from(textarea.value).length;
        counter.textContent = size + ' / ' + maxChars;
        save.disabled = !storage || invalidRecord || externalChange || !textarea.value.trim() || size > maxChars;
        if (size > maxChars) showError('메모는 ' + maxChars + '자 안으로 적어 주세요.');
        else if (!invalidRecord && !externalChange) showError('');
    }
    function openNote(day) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return;
        let item;
        try { item = read(day); }
        catch (_) {
            storageWarning();
            item = { raw: null, text: '', invalid: false };
            storage = null;
        }
        activeDay = day;
        openedRaw = item.raw;
        openedText = item.text;
        invalidRecord = item.invalid;
        externalChange = false;
        const [year, month, date] = day.split('-').map(Number);
        title.textContent = year + '년 ' + month + '월 ' + date + '일 메모';
        textarea.value = item.text;
        textarea.disabled = !storage || item.invalid;
        remove.hidden = item.raw === null;
        remove.disabled = !storage;
        showError('');
        updateCounter();
        if (!storage) showError('이 브라우저에서 메모를 저장할 수 없어요. 사이트 저장 허용을 확인해 주세요.');
        else if (item.invalid) showError('저장된 메모를 읽을 수 없어요. 이 날짜의 메모를 삭제한 뒤 다시 작성해 주세요.');
        if (!dialog.open) dialog.showModal();
        textarea.focus();
    }
    function closeNote(force = false) {
        if (!force && textarea.value !== openedText &&
            !window.confirm('저장하지 않고 닫을까요?')) return;
        dialog.close();
        textarea.value = '';
        openedText = '';
        openedRaw = null;
        activeDay = null;
    }
    function unchanged() {
        if (!storage || !activeDay) return false;
        if (storage.getItem(prefix + activeDay) !== openedRaw) {
            externalChange = true;
            save.disabled = true;
            showError('다른 창에서 이 메모가 변경됐어요. 닫았다 다시 열어 확인해 주세요. 입력 중인 내용은 복사할 수 있어요.');
            return false;
        }
        return true;
    }
    function submit(event) {
        event.preventDefault();
        updateCounter();
        if (save.disabled || !activeDay) return;
        try {
            if (!unchanged()) return;
            storage.setItem(prefix + activeDay, JSON.stringify({
                version: 1, text: textarea.value.trim(), updatedAt: new Date().toISOString()
            }));
        } catch (_) {
            showError('메모를 저장하지 못했어요. 브라우저 저장 공간과 사이트 저장 허용을 확인해 주세요.');
            return;
        }
        refreshMarkers();
        closeNote(true);
    }
    function deleteNote() {
        if (!activeDay || !storage || openedRaw === null) return;
        if (!window.confirm('이 날짜의 메모를 삭제할까요?')) return;
        try {
            if (!unchanged()) return;
            storage.removeItem(prefix + activeDay);
        } catch (_) { showError('메모를 삭제하지 못했어요. 다시 시도해 주세요.'); return; }
        refreshMarkers();
        closeNote(true);
    }
    function clickCalendar(event) {
        const button = event.target?.closest?.('.sc-calendar [data-sc-memo-day]');
        if (!button) return;
        event.preventDefault();
        openNote(button.dataset.scMemoDay);
    }
    function storageChanged(event) {
        if (event.key !== null && !event.key.startsWith(prefix)) return;
        refreshMarkers();
        if (dialog.open && activeDay && (event.key === null || event.key === prefix + activeDay)) {
            try { unchanged(); } catch (_) { showError('메모 저장 상태를 확인할 수 없어요.'); }
        }
    }
    form.onsubmit = submit;
    textarea.oninput = updateCounter;
    remove.onclick = deleteNote;
    $('sc-note-close').onclick = () => closeNote();
    $('sc-note-cancel').onclick = () => closeNote();
    dialog.oncancel = event => { event.preventDefault(); closeNote(); };
    dialog.onclick = event => {
        if (event.target !== dialog) return;
        const box = dialog.getBoundingClientRect();
        if (event.clientX < box.left || event.clientX > box.right ||
            event.clientY < box.top || event.clientY > box.bottom) closeNote();
    };
    document.addEventListener('click', clickCalendar);
    window.addEventListener('storage', storageChanged);
    const observer = new MutationObserver(refreshMarkers);
    observer.observe(document.body, { childList: true, subtree: true });
    refreshMarkers();
    return () => {
        stopped = true;
        observer.disconnect();
        document.removeEventListener('click', clickCalendar);
        window.removeEventListener('storage', storageChanged);
        if (dialog.open) dialog.close();
        textarea.value = '';
    };
}
"""


@st.cache_resource
def memo_component():
    """Register once; notes never leave the user's browser or enter Python state."""
    return st.components.v2.component(
        "shift_calendar_memos", html=MEMO_HTML, css=MEMO_CSS, js=MEMO_JS,
    )


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
                f'<td aria-label="{safe_desc}" title="{safe_desc}">'
                f'<button type="button" class="{" ".join(classes)}" data-sc-memo-day="{day.isoformat()}" '
                f'data-sc-base-label="{safe_desc}" aria-label="{safe_desc}, 눌러서 메모 쓰기">'
                f'<time class="sc-date" datetime="{day.isoformat()}">{number}</time>{badge}'
                '<span class="sc-note-indicator" hidden aria-hidden="true">'
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" '
                'stroke-linecap="round" stroke-linejoin="round" focusable="false">'
                '<path d="M9.5 1.5H3a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V6Z"/>'
                '<path d="M9 1.5V6h4.5M5 8.5h6M5 11h4"/></svg></span></button></td>'
            )
        parts.append('</tr>')
    parts.append('</tbody></table></section>')
    return ''.join(parts)


def initialize(today: date) -> None:
    if st.session_state.get("_initialized"):
        # An already-open app may retain its session while this file is updated.
        # Migrate its custom state without touching dates or the selected preset.
        saved = st.session_state.get("_custom_saved", DEFAULT_CUSTOM)
        st.session_state.setdefault("_custom_draft", st.session_state.get("custom_input", saved))
        st.session_state.setdefault("_custom_error", "")
        try:
            parse_pattern(saved)
        except ValueError:
            st.session_state["_custom_saved"] = DEFAULT_CUSTOM
            st.session_state["_custom_error"] = "반복 순서를 다시 입력한 후 적용해 주세요."
        return
    preset, start, raw, viewed = decode_settings(st.query_params.to_dict(), today)
    st.session_state.update({
        "preset": preset, "start_date": start, "custom_input": raw,
        "_custom_saved": raw, "_custom_draft": raw, "_custom_error": "",
        "_month": viewed, "_seen_start": start, "_initialized": True,
    })


def apply_custom_pattern() -> None:
    """Commit the form's complete value, never a stale widget/default/preset value.

    Streamlit batches text and the submit action in one request. Keep applied
    state separate from the widget's draft, so incomplete/invalid drafts never
    replace the actual schedule or erase a previously valid custom cycle.
    """
    raw = st.session_state.get("custom_input", "")
    st.session_state["_custom_draft"] = raw
    try:
        pattern = parse_pattern(raw)
    except ValueError as exc:
        st.session_state["_custom_error"] = str(exc)
        return
    st.session_state["_custom_saved"] = ''.join(SHIFT_LABELS[key][0] for key in pattern)
    st.session_state["_custom_error"] = ""
    start = st.session_state.get("start_date")
    if isinstance(start, date):
        # Show the beginning of the new cycle so the first entered day is visible.
        st.session_state["_month"] = month_start(start)


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
        # Only the applied value drives calculations and the saved URL. A form
        # commits mobile/desktop text input and its submit action together.
        if preset == CUSTOM_ID:
            if "custom_input" not in st.session_state:
                st.session_state["custom_input"] = st.session_state["_custom_draft"]
            with st.form("custom_pattern_form", clear_on_submit=False, border=False):
                st.text_input(
                    "반복 순서", key="custom_input", max_chars=240,
                    placeholder="예: 주주주야비휴",
                    help="주·야·비·휴를 하루에 한 글자씩, 1~31일 순서로 입력해 주세요. 주간·야간·비번·휴무 전체 이름도 가능해요.",
                )
                st.form_submit_button(
                    "달력에 적용", key="apply_custom", on_click=apply_custom_pattern,
                    use_container_width=True,
                )
            st.caption("주=주간 · 야=야간 · 비=비번 · 휴=휴무 / 입력 후 '달력에 적용'을 눌러 주세요.")
            if st.session_state["_custom_error"]:
                st.warning(st.session_state["_custom_error"] + " 달력은 마지막으로 적용한 순서를 유지해요.")
        raw = st.session_state["_custom_saved"]
        pattern = parse_pattern(raw) if preset == CUSTOM_ID else PRESET_BY_ID[preset].pattern
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
            st.button("←", key="previous", help="이전 달", use_container_width=True,
                      on_click=navigate, args=(-1,), disabled=viewed == month_start(MIN_DATE))
        with title:
            st.markdown(f'<h2 class="sc-month">{viewed.year}년 {viewed.month}월</h2>', unsafe_allow_html=True)
        with nxt:
            st.button("→", key="next", help="다음 달", use_container_width=True,
                      on_click=navigate, args=(1,), disabled=viewed == month_start(MAX_DATE))
        with current:
            st.button("오늘", key="today", help="한국 시간 기준 이번 달", use_container_width=True, on_click=go_today)
    st.markdown(calendar_html(viewed, start, pattern, today), unsafe_allow_html=True)
    memo_component()(key="calendar_memos", data={"maxChars": MEMO_MAX_CHARS, "month": viewed.isoformat()})
    st.markdown(
        '<div class="sc-footnote"><span><span class="sc-dot"></span>오늘</span>'
        '<span>주말에도 선택한 순서대로 반복돼요.</span>'
        '<span>선택한 주소를 즐겨찾기하면 설정이 유지돼요.</span>'
        '<span>날짜를 누르면 메모 · 이 브라우저에만 저장</span></div>',
        unsafe_allow_html=True,
    )
    update_address(preset, start, viewed, raw)


if __name__ == "__main__":
    main()
