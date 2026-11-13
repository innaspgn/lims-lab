import streamlit as st
import random
from io_adapter import save_state, load_state, export_document
from student_logic import (
    make_initial_state, register_sample, select_samples,
    prepare_stage_results, change_stage_batch_logged, change_stage_batch_atomic,
    reject_sample_logged, correct_department, validate_project_state
)

st.set_page_config(page_title="LIMS • Учёт образцов", layout="wide")
if "state" not in st.session_state:
    st.session_state["state"] = make_initial_state()
if "batch_protocol" not in st.session_state:
    st.session_state["batch_protocol"] = []
    st.session_state["protocol_title"] = ""

state = st.session_state["state"]
recs, history = state["records"], state["history"]

ST_RU = {"registered": "Зарегистрирован", "accepted": "Принят", "processed": "Обработан", "released": "Выдан", "rejected": "Отклонён"}
RU_ST = {v: k for k, v in ST_RU.items()}
ACT_RU = {"stage_change": "Смена этапа", "reject": "Отбраковка", "department_edit": "Правка участка"}
FLD_RU = {"status": "Статус", "status_and_reason": "Статус и причина", "department": "Участок"}

def tr(txt):
    s = str(txt)
    for e, r in ST_RU.items():
        s = s.replace(e, f"«{r}»")
    return s

def fmt(val):
    if isinstance(val, dict):
        return f"{ST_RU.get(val.get('status', ''), '')} (причина: {val.get('reject_reason') or 'нет'})"
    return ST_RU.get(str(val), str(val))

st.sidebar.markdown("### Навигация и режим")
cb = st.sidebar.checkbox("Монохромный режим (Grayscale)")
if st.sidebar.button("Сбросить базу", use_container_width=True):
    st.session_state["state"] = make_initial_state()
    st.session_state["batch_protocol"] = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Файлы проекта")
if st.sidebar.button("Сохранить в team_state.json", use_container_width=True):
    r = save_state("team_state.json", "lab", state)
    if r["ok"]:
        st.sidebar.success("Состояние сохранено.")
    else:
        st.sidebar.error("Ошибка сохранения.")

if "load_msg" in st.session_state:
    st.sidebar.success(st.session_state.pop("load_msg"))

if st.sidebar.button("Загрузить из team_state.json", use_container_width=True):
    r = load_state("team_state.json", "lab")
    if not r["ok"]:
        st.sidebar.error("Ошибка загрузки.")
    else:
        errs = validate_project_state(r["state"])
        if errs:
            for e in errs:
                st.sidebar.error(e)
        else:
            st.session_state["state"] = r["state"]
            st.session_state["batch_protocol"] = []
            st.session_state["load_msg"] = "Работа успешно восстановлена."
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Дневник смены")
cur_note = state.get("extra", {}).get("shift_note", "")
new_note = st.sidebar.text_area(
    "Комментарий дежурного",
    value=cur_note,
    placeholder="Например: Смена №2, калибровка выполнена...",
    height=75
)
if new_note != cur_note:
    state.setdefault("extra", {})["shift_note"] = new_note

doc_lines = ["РАБОЧИЙ ДОКУМЕНТ ЛАБОРАТОРИИ", "=" * 40]
if state.get("extra", {}).get("shift_note"):
    doc_lines.append(f"ЗАМЕТКА СМЕНЫ: {state['extra']['shift_note']}")
    doc_lines.append("-" * 40)
doc_lines.append("РЕЕСТР:")
doc_lines += [f"- {x['code']} | {x['department']} | {ST_RU.get(x['status'], x['status'])} | {x['reject_reason'] or '—'}" for x in recs]
doc_lines += ["\nИСТОРИЯ:"] + [f"- [{e.get('event_id','')}] {ACT_RU.get(e.get('action',''), e.get('action',''))} | {e.get('record_id')} | {tr(e.get('details',''))}" for e in history]
doc_text = "\n".join(doc_lines)

if st.sidebar.button("Выгрузить work_document.txt", use_container_width=True):
    exp = export_document("work_document.txt", doc_text)
    if exp["ok"]:
        st.sidebar.success("Документ сохранён в папку.")
    else:
        st.sidebar.error("Ошибка выгрузки.")

st.sidebar.download_button(
    label="Скачать отчёт (.txt)",
    data=doc_text,
    file_name="work_document.txt",
    mime="text/plain",
    use_container_width=True
)
# Палитра с картинки: Васильковый (#7e95c4), Салатовый (#b5dca8), Сиреневый (#e8cbf7)

if cb:
    c_blue, c_green, c_lilac, c_deep = "#18181b", "#d4d4d8", "#e4e4e7", "#27272a"
    bg, card, brd, txt_main, txt_card = "#f4f4f5", "#ffffff", "#a1a1aa", "#18181b", "#18181b"
    bm = {"registered": "#e4e4e7", "accepted": "#d4d4d8", "processed": "#a1a1aa", "released": "#18181b", "rejected": "#fff"}
    tm = {"registered": "#18181b", "accepted": "#18181b", "processed": "#18181b", "released": "#fff", "rejected": "#000"}
else:
    c_blue, c_green, c_lilac, c_deep = "#7e95c4", "#b5dca8", "#e8cbf7", "#3a4d75"
    bg = "linear-gradient(135deg, #eef3fa 0%, #f5f0fa 50%, #eff8ec 100%)"
    card, brd, txt_main, txt_card = "rgba(255, 255, 255, 0.85)", "#b5c4e0", "#222f4a", "#1e293b"
    bm = {"registered": "#dbe5f5", "accepted": "#b5dca8", "processed": "#e8cbf7", "released": "#3a4d75", "rejected": "#f3e5f5"}
    tm = {"registered": "#222f4a", "accepted": "#1e4214", "processed": "#4a2561", "released": "#ffffff", "rejected": "#6a1b9a"}

css = (
    "<style>@import url('https://googleapis.com');"
    "@keyframes slideIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}"
    f".stApp{{background:{bg};font-family:'Inter',sans-serif;color:{txt_main}}}"
    f"section[data-testid='stSidebar']{{background:linear-gradient(180deg,#e4ecf7 0%,#edf7ea 100%);border-right:1px solid {brd}}}"
    f"label, .stMarkdown p, .stSelectbox label, .stTextInput label, .stTextArea label{{color:{txt_main}!important;font-weight:600!important}}"
    f".top-banner{{background:linear-gradient(120deg,{c_deep} 0%,{c_blue} 65%,{c_lilac} 100%);color:#fff;padding:24px 30px;border-radius:20px;border:1px solid {brd};margin-bottom:18px;box-shadow:0 10px 25px rgba(58,77,117,0.15);animation:slideIn 0.4s ease}}"
    f".tile{{padding:18px 22px;border-radius:18px;border:1px solid {brd};transition:all 0.25s ease;box-shadow:0 6px 16px rgba(58,77,117,0.06);animation:slideIn 0.5s ease}}"
    ".tile:hover{transform:translateY(-4px);box-shadow:0 12px 24px rgba(58,77,117,0.14)}"
    f".panel-hdr{{font-size:17px;font-weight:700;color:{c_deep};margin:16px 0 10px;display:flex;align-items:center;gap:8px}}"
    f".dot{{width:9px;height:9px;border-radius:50%;background:{c_blue};display:inline-block}}"
    f".tbl-card{{background:{card};border:1px solid {brd};border-radius:18px;overflow:hidden;box-shadow:0 4px 16px rgba(58,77,117,0.05)}}"
    f"table.lims{{width:100%;border-collapse:collapse;font-size:13.5px;color:{txt_main}}}"
    f"table.lims th{{text-align:left;padding:12px 14px;font-size:11px;text-transform:uppercase;letter-spacing:0.6px;color:#ffffff;border-bottom:1px solid {brd};background:{c_deep}}}"
    f"table.lims td{{padding:11px 14px;border-bottom:1px solid {brd};transition:background 0.2s ease}}"
    "table.lims tr:last-child td{border-bottom:none}"
    "table.lims tbody tr:hover td{background:rgba(181,220,168,0.28)}"
    f".bdg{{padding:4px 11px;border-radius:99px;font-size:11.5px;font-weight:700;display:inline-block;border:1px solid {brd}}}"
    f".stTabs [data-baseweb='tab-list']{{background:{card};padding:6px;border-radius:14px;border:1px solid {brd};gap:6px;flex-wrap:wrap}}"
    f".stTabs [data-baseweb='tab']{{background:{c_green}!important;border-radius:10px!important;padding:8px 14px!important;font-size:13px!important;font-weight:700!important;color:{txt_main}!important;border:1px solid {brd}!important}}"
    f".stTabs [data-baseweb='tab'] p{{color:{txt_main}!important;margin:0!important}}"
    f".stTabs [aria-selected='true']{{background:{c_deep}!important;color:#ffffff!important;border-color:{c_deep}!important}}"
    ".stTabs [aria-selected='true'] p{color:#ffffff!important}"
    f"button{{background:{c_lilac}!important;color:{txt_main}!important;border:1px solid {c_blue}!important;border-radius:10px!important;font-weight:700!important}}"
    f"button:hover{{background:{c_deep}!important;color:#ffffff!important}}"
    "</style>"
)
st.markdown(css, unsafe_allow_html=True)

ticker_text = (
    "СРОЧНЫЕ НОВОСТИ, УВЕДОМЛЕНИЯ И СТАТУС РАБОТЫ: &nbsp;&nbsp;"
    "• «График работы в праздничные дни изменен: с 1 по 3 мая мы на выходных» &nbsp;&nbsp;&nbsp;&nbsp;"
    "• «Технические работы на сервере запланированы на субботу с 02:00 до 05:00» &nbsp;&nbsp;&nbsp;&nbsp;"
    "• «Прием заказов на сайте работает круглосуточно» &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
)

ticker_text = (
    "СРОЧНЫЕ НОВОСТИ, УВЕДОМЛЕНИЯ И СТАТУС РАБОТЫ: &nbsp;&nbsp;"
    "• «График работы в праздничные дни изменен: с 1 по 3 мая мы на выходных» &nbsp;&nbsp;&nbsp;&nbsp;"
    "• «Технические работы на сервере запланированы на субботу с 02:00 до 05:00» &nbsp;&nbsp;&nbsp;&nbsp;"
    "• «Прием заказов на сайте работает круглосуточно» &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
)

st.markdown(
    "<style>"
    "@keyframes marquee{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}"
    "@keyframes float3d{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-7px) rotate(2deg)}}"
    f".ticker-wrap{{overflow:hidden;white-space:nowrap;background:{card};border:1px solid {brd};border-radius:12px;padding:9px 0;margin-bottom:14px;box-shadow:0 2px 10px rgba(58,77,117,0.04)}}"
    f".ticker-move{{display:inline-block;animation:marquee 32s linear infinite;font-size:12px;font-weight:700;letter-spacing:0.4px;color:{c_deep}}}"
    ".ticker-wrap:hover .ticker-move{animation-play-state:paused}"
    ".hero-flex{display:flex;justify-content:space-between;align-items:center;gap:20px}"
    ".orb-3d{animation:float3d 5s ease-in-out infinite;flex-shrink:0}"
    "</style>"
    f"<div class='ticker-wrap'><div class='ticker-move'>{ticker_text}{ticker_text}</div></div>"
    "<div class='top-banner'><div class='hero-flex'>"
    "<div><div style='font-size:11px;font-weight:700;letter-spacing:1.8px;opacity:0.9'>LABORATORY CONTROL SYSTEM • 3D EDITION</div>"
    "<div style='font-size:28px;font-weight:800;letter-spacing:-0.5px;margin-top:4px'>Учёт и маршрутизация лабораторных образцов</div>"
    "<div style='font-size:13px;opacity:0.85;margin-top:6px'>Интеллектуальный контроль этапов, пакетная валидация и журнал событий</div></div>"
    "<svg class='orb-3d' width='104' height='104' viewBox='0 0 120 120' fill='none'>"
    "<defs>"
    "<linearGradient id='glassBody' x1='0' y1='0' x2='1' y2='1'><stop offset='0%' stop-color='#ffffff' stop-opacity='0.45'/><stop offset='100%' stop-color='#7e95c4' stop-opacity='0.15'/></linearGradient>"
    "<linearGradient id='mintLiquid' x1='0' y1='0' x2='0' y2='1'><stop offset='0%' stop-color='#d8f3cf'/><stop offset='100%' stop-color='#7bb86a'/></linearGradient>"
    "<linearGradient id='lilacLiquid' x1='0' y1='0' x2='0' y2='1'><stop offset='0%' stop-color='#f3e1fc'/><stop offset='100%' stop-color='#b57edc'/></linearGradient>"
    "<radialGradient id='dropGlow' cx='30%' cy='30%' r='70%'><stop offset='0%' stop-color='#ffffff'/><stop offset='100%' stop-color='#b5dca8'/></radialGradient>"
    "</defs>"
    "<ellipse cx='64' cy='106' rx='36' ry='6' fill='#1e293b' fill-opacity='0.28'/>"
    "<path d='M44 22 H64 M47 22 V44 L26 88 C24 93 27 98 33 98 H75 C81 98 84 93 82 88 L61 44 V22' fill='url(#glassBody)' stroke='#ffffff' stroke-width='2' stroke-opacity='0.75'/>"
    "<path d='M34 72 L28 86 C26 90 29 94 34 94 H74 C79 94 82 90 80 86 L74 72 Z' fill='url(#mintLiquid)'/>"
    "<ellipse cx='54' cy='72' rx='20' ry='4' fill='#e8fce1' fill-opacity='0.8'/>"
    "<path d='M45 48 L35 76' stroke='#ffffff' stroke-width='2.5' stroke-linecap='round' stroke-opacity='0.6'/>"
    "<g transform='rotate(14 88 62)'>"
    "<rect x='78' y='28' width='18' height='64' rx='9' fill='url(#glassBody)' stroke='#ffffff' stroke-width='2' stroke-opacity='0.85'/>"
    "<path d='M80 56 H94 V82 C94 86 91 90 87 90 C83 90 80 86 80 82 Z' fill='url(#lilacLiquid)'/>"
    "<ellipse cx='87' cy='56' rx='7' ry='2.5' fill='#f8edff'/>"
    "<line x1='83' y1='35' x2='83' y2='75' stroke='#ffffff' stroke-width='2' stroke-linecap='round' stroke-opacity='0.65'/>"
    "</g>"
    "<circle cx='34' cy='34' r='6' fill='url(#dropGlow)'/>"
    "<circle cx='102' cy='24' r='4.5' fill='#e8cbf7'/>"
    "<circle cx='52' cy='83' r='2.5' fill='#ffffff' fill-opacity='0.85'/>"
    "</svg></div></div>",
    unsafe_allow_html=True
)
lab_tips = [
    "Правило №1: кофе пьём строго за пределами реакторной зоны.",
    "Идеально наклеенная этикетка ускоряет анализ на 15%.",
    "Образцы в статусе «Принят» требуют строгого соблюдения температурного режима (+4°C).",
    "Предварительная валидация предотвращает ошибки при групповом переводе этапов.",
    "Каждая выданная пробирка увеличивает общий показатель эффективности лаборатории."
]
if "current_tip" not in st.session_state:
    st.session_state["current_tip"] = random.choice(lab_tips)

c_tip_txt, c_tip_btn = st.columns([4.5, 1])
with c_tip_txt:
    st.markdown(
        f"<div style='background:{card};border:1px solid {brd};border-radius:12px;padding:10px 16px;margin-bottom:14px;font-size:13px;color:{txt_main}'>"
        f"<b style='color:{c_deep}'>ЗАМЕТКА ЛАБОРАТОРИИ:</b> {st.session_state['current_tip']}</div>",
        unsafe_allow_html=True
    )
with c_tip_btn:
    if st.button("Обновить совет", use_container_width=True):
        st.session_state["current_tip"] = random.choice(lab_tips)
        st.rerun()

k1, k2, k3, k4 = st.columns(4)
k1.markdown(f"<div class='tile' style='background:{c_deep};color:#ffffff'><span style='font-size:11px;font-weight:700;opacity:0.85'>ВСЕГО В БАЗЕ</span><div style='font-size:28px;font-weight:800;margin-top:2px'>{len(recs)}</div></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='tile' style='background:{c_blue};color:#ffffff'><span style='font-size:11px;font-weight:700;opacity:0.9'>В РАБОТЕ</span><div style='font-size:28px;font-weight:800;margin-top:2px'>{sum(1 for r in recs if r['status'] in ['registered','accepted','processed'])}</div></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='tile' style='background:{c_green};color:{txt_card}'><span style='font-size:11px;font-weight:700;opacity:0.85'>ВЫДАНО</span><div style='font-size:28px;font-weight:800;margin-top:2px'>{sum(1 for r in recs if r['status']=='released')}</div></div>", unsafe_allow_html=True)
k4.markdown(f"<div class='tile' style='background:{c_lilac};color:{txt_card}'><span style='font-size:11px;font-weight:700;opacity:0.85'>СОБЫТИЙ ИСТОРИИ</span><div style='font-size:28px;font-weight:800;margin-top:2px'>{len(history)}</div></div>", unsafe_allow_html=True)
col_left, col_right = st.columns([1.05, 1.3])

with col_left:
    st.markdown("<div class='panel-hdr'><span class='dot'></span> Пульт управления</div>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["Смена этапа", "Исправление участка", "Отбраковка", "Регистрация"])
    with t1:
        if "stage_codes_input" not in st.session_state:
            st.session_state["stage_codes_input"] = ""

        active_samples = [r["code"] for r in recs if r["status"] not in ["released", "rejected"]]
        if active_samples:
            st.caption("Быстрое добавление активных кодов:")
            chip_cols = st.columns(min(len(active_samples) + 1, 5))
            for idx, scode in enumerate(active_samples[:4]):
                if chip_cols[idx].button(f"+ {scode}", key=f"chip_{scode}", use_container_width=True):
                    cur_v = st.session_state["stage_codes_input"].strip()
                    st.session_state["stage_codes_input"] = f"{cur_v}, {scode}" if cur_v else scode
                    st.rerun()
            if chip_cols[-1].button("Очистить", key="chip_clear", use_container_width=True):
                st.session_state["stage_codes_input"] = ""
                st.rerun()

        raw_txt = st.text_area(
            "Коды образцов",
            key="stage_codes_input",
            placeholder="lab001, LAB004, LAB999",
            height=85
        )
        mode_ru = st.radio(
            "Режим обработки",
            ["Частично (по одному)", "Строго («все или ни одного»)"],
            horizontal=True
        )
        tgt_ru = st.selectbox("Целевой этап", ["Принят", "Обработан", "Выдан"])
        tgt = RU_ST[tgt_ru]
        c1, c2 = st.columns(2)
        if c1.button("Проверка", use_container_width=True):
            if not raw_txt.strip():
                st.warning("Введите хотя бы один код образца для проверки.")
            else:
                st.session_state["batch_protocol"] = prepare_stage_results(recs, raw_txt, tgt)
                st.session_state["protocol_title"] = f"Предпросмотр («{tgt_ru}»)"
        if c2.button("Выполнение", use_container_width=True):
            if not raw_txt.strip():
                st.warning("Введите хотя бы один код образца перед выполнением.")
            else:
                if mode_ru.startswith("Строго"):
                    res_list = change_stage_batch_atomic(state, raw_txt, tgt)
                else:
                    res_list = change_stage_batch_logged(state, raw_txt, tgt)
                st.session_state["batch_protocol"] = res_list
                st.session_state["protocol_title"] = f"Протокол • {mode_ru} («{tgt_ru}»)"
                st.rerun()
        if st.session_state["batch_protocol"]:
            st.markdown(f"**{st.session_state['protocol_title']}**")
            for it in st.session_state["batch_protocol"]:
                if it["ok"]:
                    st.success(f"{it['record_id']}: {tr(it['message'])}")
                else:
                    st.error(f"{it['record_id']}: {tr(it['message'])}")


    with t2:
        with st.form("dept_f", clear_on_submit=True):
            ec = st.text_input("Код (только «Зарегистрирован»)")
            ed = st.selectbox("Новый участок", state.get("extra", {}).get("departments", ["Участок А", "Участок Б"]))
            if st.form_submit_button("Изменить участок", use_container_width=True):
                r = correct_department(state, ec, ed)
                if r["ok"]:
                    st.success(tr(r["message"]))
                    st.rerun()
                else:
                    st.error(tr(r["message"]))
    with t3:
        with st.form("rej_f", clear_on_submit=True):
            jc = st.text_input("Код образца")
            jr = st.text_input("Причина отклонения")
            if st.form_submit_button("Отклонить", use_container_width=True):
                r = reject_sample_logged(state, jc, jr)
                if r["ok"]:
                    st.success(tr(r["message"]))
                    st.rerun()
                else:
                    st.error(tr(r["message"]))
    with t4:
        with st.form("reg_f", clear_on_submit=True):
            rc = st.text_input("Код (LABxxx)")
            rd = st.selectbox("Участок", state.get("extra", {}).get("departments", ["Участок А", "Участок Б"]))
            if st.form_submit_button("Зарегистрировать", use_container_width=True):
                r = register_sample(recs, rc, rd)
                if r["ok"]:
                    st.success(tr(r["message"]))
                    st.rerun()
                else:
                    st.error(tr(r["message"]))

with col_right:
    st.markdown("<div class='panel-hdr'><span class='dot'></span> Живой реестр образцов</div>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    fd = f1.selectbox("Участок", ["Все", "Участок А", "Участок Б"])
    fs_ru = f2.selectbox("Статус", ["Все", "Зарегистрирован", "Принят", "Обработан", "Выдан", "Отклонён"])
    ff = f3.text_input("Поиск ID", placeholder="LAB...", key="search_id_box")
    shown = select_samples(recs, None if fd == "Все" else fd, None if fs_ru == "Все" else RU_ST[fs_ru], ff.strip() or None)
    if not shown:
        st.info("Записи не найдены.")
    else:
        rows = "".join(f"<tr><td><b>{r['code']}</b></td><td>{r['department']}</td><td><span class='bdg' style='background:{bm[r['status']]};color:{tm[r['status']]}'>{ST_RU[r['status']]}</span></td><td style='color:#6b4c55'>{r['reject_reason'] or '—'}</td></tr>" for r in shown)
        st.markdown(f"<div class='tbl-card'><table class='lims'><thead><tr><th>Код</th><th>Участок</th><th>Статус</th><th>Примечание</th></tr></thead><tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)
    if ff.strip() and shown:
        target_sample = shown[0]
        st_code = target_sample["status"]
        if st_code == "rejected":
            temp_lbl, brd_col, bars = "QUARANTINE", "#b91c1c", "|| ||| | ||| ||"
        elif st_code == "released":
            temp_lbl, brd_col, bars = "-20°C ARCHIVE", "#4d7c0f", "|||| | || || ||||"
        else:
            temp_lbl, brd_col, bars = "+4°C ACTIVE", "#7e95c4", "||| | || ||| | ||"

        st.markdown(
            f"<div style='background:#ffffff;border:2px dashed {brd_col};border-radius:14px;padding:12px 16px;margin-top:12px;font-family:monospace;color:#222f4a;box-shadow:0 4px 12px rgba(0,0,0,0.04)'>"
            f"<div style='font-size:10.5px;color:#64748b;display:flex;justify-content:space-between'><span>LAB-PASS</span><b style='color:{brd_col}'>{temp_lbl}</b></div>"
            f"<div style='font-size:18px;font-weight:800;letter-spacing:3px;margin:6px 0'>{bars}</div>"
            f"<div style='font-size:13px;font-weight:700'>{target_sample['code']} • {target_sample['department']}</div>"
            f"<div style='font-size:11.5px;color:#3a4d75;margin-top:2px'>Статус: {ST_RU.get(st_code, st_code)}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        

done_pct = int((sum(1 for r in recs if r["status"] == "released") / len(recs)) * 100) if recs else 0
cnt_a = sum(1 for r in recs if r["department"] == "Участок А")
cnt_b = sum(1 for r in recs if r["department"] == "Участок Б")
pct_a = int((cnt_a / len(recs)) * 100) if recs else 50
pct_b = 100 - pct_a if recs else 50

c_prog, c_dept = st.columns([1.2, 1])
with c_prog:
    st.markdown(
        f"<div style='background:{card};border:1px solid {brd};border-radius:14px;padding:14px 18px;margin-top:16px'>"
        f"<div style='display:flex;justify-content:space-between;font-size:12px;font-weight:700;color:{c_deep};margin-bottom:8px'>"
        f"<span>ПРОГРЕСС ВЫДАЧИ ОБРАЗЦОВ</span><span>{done_pct}% ЗАВЕРШЕНО</span></div>"
        f"<div style='background:#e2e8f0;border-radius:99px;height:10px;overflow:hidden'>"
        f"<div style='background:linear-gradient(90deg,{c_blue},{c_green});width:{done_pct}%;height:100%;border-radius:99px;transition:width 0.4s ease'></div>"
        f"</div></div>",
        unsafe_allow_html=True
    )

with c_dept:
    st.markdown(
        f"<div style='background:{card};border:1px solid {brd};border-radius:14px;padding:14px 18px;margin-top:16px'>"
        f"<div style='display:flex;justify-content:space-between;font-size:12px;font-weight:700;color:{c_deep};margin-bottom:8px'>"
        f"<span>УЧАСТОК А: {cnt_a} ({pct_a}%)</span><span>УЧАСТОК Б: {cnt_b} ({pct_b}%)</span></div>"
        f"<div style='display:flex;background:#e2e8f0;border-radius:99px;height:10px;overflow:hidden'>"
        f"<div style='background:{c_blue};width:{pct_a}%;height:100%;transition:width 0.4s ease'></div>"
        f"<div style='background:{c_lilac};width:{pct_b}%;height:100%;transition:width 0.4s ease'></div>"
        f"</div></div>",
        unsafe_allow_html=True
    )

st.markdown("<div class='panel-hdr'><span class='dot'></span> Лента истории событий (Timeline)</div>", unsafe_allow_html=True)
if not history:
    st.info("История пуста. Выполните любое действие в пульте управления, чтобы появилась первая карточка события.")
else:
    hf1, hf2 = st.columns([1, 2])
    h_act_filter = hf1.selectbox("Тип события", ["Все действия", "Смена этапа", "Отбраковка", "Правка участка"])
    h_code_filter = hf2.text_input("Фильтр истории по коду", placeholder="Например: LAB001")

    filtered_hist = []
    for e in reversed(history):
        act_ru_name = ACT_RU.get(e.get("action", ""), e.get("action", ""))
        if h_act_filter != "Все действия" and act_ru_name != h_act_filter:
            continue
        if h_code_filter.strip() and h_code_filter.strip().upper() not in str(e.get("record_id", "")).upper():
            continue
        filtered_hist.append(e)

    if not filtered_hist:
        st.info("По заданному фильтру событий не найдено.")
    else:
        for e in filtered_hist:
            act_name = ACT_RU.get(e.get("action", ""), e.get("action", ""))
            fld_name = FLD_RU.get(e.get("field", ""), e.get("field", ""))
            b_val = fmt(e.get("before", ""))
            a_val = fmt(e.get("after", ""))
            st.markdown(
                f"<div style='background:{card};border-left:5px solid {c_blue};border-top:1px solid {brd};border-right:1px solid {brd};border-bottom:1px solid {brd};"
                f"border-radius:12px;padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center'>"
                f"<div><span style='background:{c_lilac};color:{txt_main};padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;margin-right:8px'>{e.get('event_id','—')}</span>"
                f"<b style='color:{c_deep}'>{act_name}</b> • Образец <b>{e.get('record_id','')}</b> ({fld_name}): "
                f"<span style='opacity:0.75'>{b_val}</span> ➔ <b>{a_val}</b></div>"
                f"<div style='font-size:12px;color:#475569'>{tr(e.get('details',''))}</div></div>",
                unsafe_allow_html=True
            )

with st.expander("📄 Предпросмотр рабочего документа (work_document.txt)"):
    st.code(doc_text, language="text")
