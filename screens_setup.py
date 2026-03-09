import streamlit as st
import uuid
import math
import random
import time
from collections import Counter
from shared import (
    load_db, save_db, get_player, get_play_count, go,
    music_player, calculate_roles, role_emoji,
    play_sound_html, METRONOME_SOUND, WHISTLE_SOUND
)
import streamlit.components.v1 as components


def screen_main_menu():
    import streamlit.components.v1 as components

    # Прячем нативные кнопки визуально, но оставляем кликабельными
    st.markdown("""
    <style>
    div[data-testid="stMainBlockContainer"] div[data-testid="stButton"] {
        height: 0px !important;
        min-height: 0px !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Streamlit-кнопки (визуально скрыты)
    if st.button("🕹️ Новая", key="main_new"):
        go("select_mode")
        st.rerun()
    if st.button("👥 Игроки", key="main_players"):
        go("players_list")
        st.rerun()
    if st.button("📦 Архив", key="main_archive"):
        go("archive")
        st.rerun()
    if st.button("📤 Экспорт", key="main_export"):
        go("export_import")
        st.rerun()

    # HTML главный экран
    components.html("""
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: transparent; font-family: -apple-system, sans-serif; }
        .menu-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px 10px;
            gap: 16px;
        }
        .logo { font-size: 80px; }
        .title { font-size: 24px; font-weight: bold; color: #fff; }
        .btn-big {
            width: 160px;
            height: 160px;
            border-radius: 20px;
            background: linear-gradient(135deg, #ff4b4b, #c0392b);
            border: none;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: transform 0.15s;
        }
        .btn-big:hover { transform: scale(1.05); }
        .btn-big:active { transform: scale(0.95); }
        .btn-big .icon { font-size: 48px; }
        .btn-big .label { font-size: 18px; font-weight: bold; color: #fff; }
        .row {
            display: flex;
            gap: 8px;
            width: 100%;
            max-width: 340px;
            justify-content: center;
        }
        .btn-sm {
            flex: 1;
            height: 60px;
            border-radius: 12px;
            background: #262730;
            border: 1px solid #555;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 2px;
            transition: transform 0.15s;
        }
        .btn-sm:hover { background: #3a3a4a; border-color: #ff4b4b; }
        .btn-sm:active { transform: scale(0.95); }
        .btn-sm .icon { font-size: 20px; }
        .btn-sm .label { font-size: 11px; font-weight: bold; color: #ccc; }
    </style>
    <div class="menu-wrap">
        <div class="logo">🎭</div>
        <div class="title">Mafia Companion</div>
        <button class="btn-big" onclick="clickBtn('Новая')">
            <span class="icon">🕹️</span>
            <span class="label">Новая игра</span>
        </button>
        <div class="row">
            <button class="btn-sm" onclick="clickBtn('Игроки')">
                <span class="icon">👥</span>
                <span class="label">Игроки</span>
            </button>
            <button class="btn-sm" onclick="clickBtn('Архив')">
                <span class="icon">📦</span>
                <span class="label">Архив</span>
            </button>
            <button class="btn-sm" onclick="clickBtn('Экспорт')">
                <span class="icon">📤</span>
                <span class="label">Экспорт</span>
            </button>
        </div>
    </div>
    <script>
    function clickBtn(text) {
        const doc = window.parent.document;
        const buttons = doc.querySelectorAll('button');
        for (let b of buttons) {
            if (b.textContent.includes(text)) {
                b.style.opacity = '1';
                b.style.pointerEvents = 'auto';
                b.click();
                return;
            }
        }
    }
    </script>
    """, height=420)



def screen_select_mode():
    import streamlit.components.v1 as components

    # Прячем нативные кнопки
    st.markdown("""
    <style>
    div[data-testid="stMainBlockContainer"] div[data-testid="stButton"] {
        height: 0px !important;
        min-height: 0px !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Скрытые Streamlit-кнопки
    if st.button("sm_Спорт", key="mode_sport"):
        st.session_state.game = {"mode": "спортивная", "players": [], "roles": {}}
        go("select_players"); st.rerun()
    if st.button("sm_Город", key="mode_city"):
        st.session_state.game = {"mode": "городская", "players": [], "roles": {}}
        go("select_players"); st.rerun()
    if st.button("sm_Назад", key="mode_back"):
        go("main_menu"); st.rerun()

    # HTML экран
    components.html("""
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: transparent; font-family: -apple-system, sans-serif; }
        .wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px 10px;
            gap: 12px;
            min-height: 480px;
            position: relative;
        }
        .icon { font-size: 80px; }
        .title { font-size: 22px; font-weight: bold; color: #fff; margin-bottom: 8px; }
        .cards {
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .card {
            width: 150px;
            height: 150px;
            border-radius: 18px;
            border: none;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: transform 0.15s;
        }
        .card:hover { transform: scale(1.05); }
        .card:active { transform: scale(0.95); }
        .card .emoji { font-size: 48px; }
        .card .label { font-size: 15px; font-weight: bold; }
        .card .sub { font-size: 11px; opacity: 0.7; }
        .card-sport {
            background: linear-gradient(135deg, #e67e22, #d35400);
            color: #fff;
        }
        .card-city {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: #fff;
        }
        .back-btn {
            position: absolute;
            bottom: 12px;
            left: 12px;
            background: #262730;
            border: 1px solid #555;
            color: #ccc;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.15s;
        }
        .back-btn:hover { background: #3a3a4a; border-color: #ff4b4b; }
        .back-btn:active { transform: scale(0.95); }
    </style>
    <div class="wrap">
        <div class="icon">🃏</div>
        <div class="title">Выберите режим</div>
        <div class="cards">
            <button class="card card-sport" onclick="clickBtn('sm_Спорт')">
                <span class="emoji">🏆</span>
                <span class="label">Спортивная</span>
                <span class="sub">10 игроков</span>
            </button>
            <button class="card card-city" onclick="clickBtn('sm_Город')">
                <span class="emoji">🏙️</span>
                <span class="label">Городская</span>
                <span class="sub">7+ игроков</span>
            </button>
        </div>
        <button class="back-btn" onclick="clickBtn('sm_Назад')">⬅️ Назад</button>
    </div>
    <script>
    function clickBtn(text) {
        const doc = window.parent.document;
        const buttons = doc.querySelectorAll('button');
        for (let b of buttons) {
            if (b.textContent.includes(text)) {
                b.style.opacity = '1';
                b.style.pointerEvents = 'auto';
                b.click();
                return;
            }
        }
    }
    </script>
    """, height=500)



def screen_select_players():
    import streamlit.components.v1 as components
    db = load_db()

    if "selected_pids" not in st.session_state:
        st.session_state.selected_pids = []

    count = len(st.session_state.selected_pids)
    can_go = count >= 7
    sorted_players = sorted(db['players'], key=lambda p: get_play_count(db, p['id']), reverse=True)

    # Логика счётчика
    if count <= 6:
        counter_bg = "#8b0000"; counter_text = f"{count} / 7"; counter_sub = "соберите минимум"
    elif count <= 9:
        counter_bg = "#8b7500"; counter_text = f"{count} / 10"; counter_sub = "можно начать"
    elif count == 10:
        counter_bg = "#1a6b1a"; counter_text = "10 / 10"; counter_sub = "👑 Идеально 👑"
    else:
        counter_bg = "#8b7500"; counter_text = f"{count} игроков"; counter_sub = "можно начать"

    # Логика цветов кнопок
    if can_go:
        back_style = "background:#262730;color:#ccc;border:1px solid #555;"
        repeat_style = "background:#262730;color:#ccc;border:1px solid #555;"
        start_style = "background:linear-gradient(135deg,#27ae60,#219a52);color:#fff;border:none;"
        start_disabled = ""
        start_onclick = "clickSP('sp_Старт')"
    else:
        back_style = "background:#262730;color:#ccc;border:1px solid #555;"
        if db.get('last_composition'):
            repeat_style = "background:linear-gradient(135deg,#27ae60,#219a52);color:#fff;border:none;"
        else:
            repeat_style = "background:#262730;color:#666;border:1px solid #444;"
        start_style = "background:#262730;color:#666;border:1px solid #444;opacity:0.35;"
        start_disabled = "disabled"
        start_onclick = ""

    # Генерируем HTML игроков
    players_html = ""
    for idx, p in enumerate(sorted_players):
        is_sel = p['id'] in st.session_state.selected_pids
        games = get_play_count(db, p['id'])
        games_str = f'<span class="games">({games})</span>' if games > 0 else ""
        sel_class = "sel" if is_sel else ""
        check = "✅ " if is_sel else ""
        players_html += (
            f'<button class="p-btn {sel_class}" onclick="clickSP(\'sp_t_{idx}\')">'
            f'{check}{p["nickname"]} {games_str}</button>\n'
        )

    components.html(f"""
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: transparent; font-family: -apple-system, sans-serif; }}
        .wrap {{
            display: flex;
            flex-direction: column;
            padding: 10px 8px;
            gap: 8px;
        }}
        .header {{
            text-align: center;
            padding: 4px 0;
        }}
        .header .icon {{
            font-size: 56px;
        }}
        .header .title {{
            font-size: 20px;
            font-weight: bold;
            color: #fff;
            margin: 2px 0;
        }}
        .counter {{
            text-align: center;
            padding: 10px 16px;
            border-radius: 12px;
            background: {counter_bg};
        }}
        .counter .num {{
            font-size: 32px;
            font-weight: bold;
            color: #fff;
        }}
        .counter .sub {{
            font-size: 13px;
            color: rgba(255,255,255,0.7);
            margin-top: 2px;
        }}
        .controls {{
            display: flex;
            gap: 6px;
        }}
        .ctrl-btn {{
            flex: 1;
            height: 44px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.12s;
            padding: 0 8px;
        }}
        .ctrl-btn:active {{
            transform: scale(0.95);
        }}
        .ctrl-btn:hover {{
            filter: brightness(1.15);
        }}
        .divider {{
            border-top: 1px solid #333;
            margin: 2px 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 5px;
            overflow-y: auto;
            max-height: 380px;
            padding-right: 4px;
        }}
        .grid::-webkit-scrollbar {{
            width: 4px;
        }}
        .grid::-webkit-scrollbar-thumb {{
            background: #555;
            border-radius: 4px;
        }}
        .p-btn {{
            height: 40px;
            border-radius: 8px;
            background: #262730;
            border: 1px solid #444;
            color: #999;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
            text-align: left;
            padding: 0 10px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: transform 0.12s;
        }}
        .p-btn:hover {{
            background: #3a3a4a;
            border-color: #888;
        }}
        .p-btn:active {{
            transform: scale(0.96);
        }}
        .p-btn.sel {{
            background: #1a3a1a;
            border-color: #4CAF50;
            color: #fff;
        }}
        .p-btn .games {{
            font-size: 11px;
            color: #666;
            font-weight: normal;
        }}
        .p-btn.sel .games {{
            color: #8bc78b;
        }}
        .add-section {{
            border-top: 1px solid #333;
            padding-top: 8px;
            margin-top: 4px;
        }}
        .add-title {{
            font-size: 13px;
            color: #aaa;
            margin-bottom: 6px;
            font-weight: bold;
        }}
        .add-row {{
            display: flex;
            gap: 6px;
        }}
        .add-row input {{
            flex: 1;
            height: 36px;
            border-radius: 6px;
            border: 1px solid #555;
            background: #1a1a2e;
            color: #fff;
            padding: 0 8px;
            font-size: 13px;
            outline: none;
        }}
        .add-row input:focus {{
            border-color: #4CAF50;
        }}
        .add-row input::placeholder {{
            color: #666;
        }}
        .btn-add {{
            height: 36px;
            width: 42px;
            border-radius: 6px;
            background: #2d5a2d;
            border: 1px solid #4CAF50;
            color: #fff;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
        }}
        .btn-add:hover {{
            background: #3a6a3a;
        }}
        .btn-add:active {{
            transform: scale(0.95);
        }}
    </style>
    <div class="wrap">
        <div class="header">
            <div class="icon">👥</div>
            <div class="title">Выбор игроков</div>
        </div>
        <div class="counter">
            <div class="num">{counter_text}</div>
            <div class="sub">{counter_sub}</div>
        </div>
        <div class="controls">
            <button class="ctrl-btn" style="{back_style}" onclick="clickSP('sp_Назад')">⬅️ Назад</button>
            <button class="ctrl-btn" style="{repeat_style}" onclick="clickSP('sp_Повтор')">🔄 Повтор</button>
            <button class="ctrl-btn" style="{start_style}" onclick="{start_onclick}" {start_disabled}>🚀 Старт</button>
        </div>
        <div class="divider"></div>
        <div class="grid">
            {players_html}
        </div>
        <div class="add-section">
            <div class="add-title">➕ Быстрое добавление</div>
            <div class="add-row">
                <input type="text" id="inp_name" placeholder="Имя">
                <input type="text" id="inp_nick" placeholder="Псевдоним">
                <button class="btn-add" onclick="doAdd()">+</button>
            </div>
        </div>
    </div>
    <script>
    function clickSP(text) {{
        const buttons = window.parent.document.querySelectorAll('button');
        for (let b of buttons) {{
            if (b.textContent.includes(text)) {{
                b.style.opacity = '1';
                b.style.pointerEvents = 'auto';
                b.click();
                return;
            }}
        }}
    }}
    function doAdd() {{
        const name = document.getElementById('inp_name').value.trim();
        const nick = document.getElementById('inp_nick').value.trim();
        if (!name || !nick) return;
        const url = new URL(window.parent.location);
        url.searchParams.set('qa_add', name + '|||' + nick);
        window.parent.history.replaceState(null, '', url);
        clickSP('sp_Добавить');
    }}
    </script>
    """, height=720)

    # === Скрытые ST-кнопки ===
    for idx, p in enumerate(sorted_players):
        if st.button(f"sp_t_{idx}", key=f"sel_p_{idx}"):
            pid = p['id']
            if pid in st.session_state.selected_pids:
                st.session_state.selected_pids.remove(pid)
            else:
                st.session_state.selected_pids.append(pid)
            st.rerun()

    if st.button("sp_Старт", key="sp_start"):
        if can_go:
            _finalize_players(db)
            st.rerun()

    if st.button("sp_Повтор", key="sp_repeat"):
        st.session_state.selected_pids = db.get('last_composition', [])[:]
        st.rerun()

    if st.button("sp_Назад", key="sp_back"):
        go("select_mode")
        st.rerun()

    if st.button("sp_Добавить", key="sp_add"):
        params = st.query_params
        qa = params.get("qa_add", "")
        if "|||" in qa:
            rn, nn = qa.split("|||", 1)
            if rn.strip() and nn.strip():
                pid = str(uuid.uuid4())
                db['players'].append({"id": pid, "real_name": rn.strip(), "nickname": nn.strip(), "history": []})
                save_db(db)
                st.session_state.selected_pids.append(pid)
                st.query_params.clear()
                st.rerun()

    # Прячем sp_ кнопки и скроллим вверх
    components.html("""
    <script>
    (function() {
        function hideSpButtons() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(b => {
                const text = b.textContent || '';
                if (text.startsWith('sp_')) {
                    const wrapper = b.closest('div[data-testid="stButton"]');
                    if (wrapper) {
                        wrapper.style.cssText = 'height:0!important;min-height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;opacity:0!important;position:absolute!important;pointer-events:none!important;';
                    }
                }
            });
            const main = window.parent.document.querySelector('section.main');
            if (main) main.scrollTop = 0;
            const block = window.parent.document.querySelector('[data-testid="stMainBlockContainer"]');
            if (block) block.scrollTop = 0;
            window.parent.scrollTo(0, 0);
        }
        setTimeout(hideSpButtons, 50);
        setTimeout(hideSpButtons, 200);
        setTimeout(hideSpButtons, 500);
        setTimeout(hideSpButtons, 1000);
    })();
    </script>
    """, height=0)


def _finalize_players(db):
    players = []
    for i, pid in enumerate(st.session_state.selected_pids, 1):
        pl = get_player(db, pid)
        players.append({"id": pid, "nickname": pl['nickname'], "real_name": pl['real_name'],
                         "number": i, "role": "", "fouls": 0, "status": "alive"})
    st.session_state.game['players'] = players
    db['last_composition'] = st.session_state.selected_pids[:]
    save_db(db)
    st.session_state.role_assignment_mode = None
    st.session_state.manual_assigned = {}
    go("assign_roles")


def screen_assign_roles():
    import streamlit.components.v1 as components
    game = st.session_state.game
    players = game['players']
    n = len(players)
    roles = calculate_roles(n)

    # Проверка — все ли роли назначены
    assigned_roles = Counter([p['role'] for p in players if p['role']])
    expected = Counter()
    for role, cnt in roles.items():
        expected[role] = cnt
    all_done = assigned_roles == expected

    sorted_p = sorted(players, key=lambda p: p['number'])

    # === Генерируем HTML таблицы игроков ===
    table_html = ""
    for p in sorted_p:
        if p['role'] == 'Мирный':
            bg = "#1a3a1a"
            text = f'❤️ #{p["number"]} {p["nickname"]}'
            align = "left"
        elif p['role'] in ['Дон', 'Мафия', 'Шериф']:
            emoji = role_emoji(p['role'])
            bg = "#2a1a1a" if p['role'] in ['Дон', 'Мафия'] else "#1a2a3d"
            text = f'#{p["number"]} {p["nickname"]} — {emoji} {p["role"]}'
            align = "right"
        else:
            bg = "#1a1a3d"
            text = f'#{p["number"]} {p["nickname"]} — ❓'
            align = "center"
        table_html += (
            f'<div style="background:{bg};padding:8px 14px;margin:3px 0;'
            f'border-radius:6px;color:white;font-size:15px;text-align:{align};">'
            f'{text}</div>\n'
        )

    # === Логика кнопок ===
    night_style = "background:linear-gradient(135deg,#27ae60,#219a52);color:#fff;border:none;" if all_done else "background:#262730;color:#666;border:1px solid #444;opacity:0.35;"
    night_disabled = "" if all_done else "disabled"
    night_onclick = "clickAR('ar_Ночь0')" if all_done else ""

    # Ручной режим — сетка выбора ролей
    manual_html = ""
    if st.session_state.get('role_assignment_mode') == "manual":
        for role_name in ["Дон", "Шериф", "Мафия"]:
            role_count = roles.get(role_name, 0)
            if role_count == 0:
                continue
            already = [p for p in players if p['role'] == role_name]
            remaining = role_count - len(already)
            if remaining <= 0:
                names = ", ".join([f"#{p['number']}" for p in sorted(already, key=lambda x: x['number'])])
                manual_html += f'<div style="color:#8bc78b;font-size:14px;padding:4px 0;font-weight:bold;">{role_emoji(role_name)} {role_name}: {names} ✅</div>'
                continue
            manual_html += f'<div style="color:#ccc;font-size:14px;padding:6px 0 2px;font-weight:bold;">{role_emoji(role_name)} {role_name} — выберите {remaining}:</div>'
            manual_html += '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px;">'
            for p in sorted_p:
                has_role = p['role'] != ""
                if has_role:
                    lbl = f"{role_emoji(p['role'])}#{p['number']}"
                    manual_html += f'<button style="flex:0 0 18%;height:36px;border-radius:6px;background:#333;border:1px solid #555;color:#666;font-size:12px;font-weight:bold;cursor:default;" disabled>{lbl}</button>'
                else:
                    lbl = f"#{p['number']}"
                    manual_html += f'<button style="flex:0 0 18%;height:36px;border-radius:6px;background:#262730;border:1px solid #666;color:#ccc;font-size:12px;font-weight:bold;cursor:pointer;" onclick="clickAR(\'ar_m_{role_name}_{p["number"]}\')">{lbl}</button>'
            manual_html += '</div>'

    # Кнопки снятия роли (если не все назначены)
    cancel_html = ""
    if not all_done:
        for p in sorted_p:
            if p['role'] in ['Дон', 'Мафия', 'Шериф']:
                cancel_html += f'<button style="width:100%;height:32px;border-radius:6px;background:#3a1a1a;border:1px solid #662222;color:#ff8888;font-size:12px;font-weight:bold;cursor:pointer;margin:2px 0;" onclick="clickAR(\'ar_cancel_{p["number"]}\')">✖ Снять роль #{p["number"]}</button>'

    components.html(f"""
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: transparent; font-family: -apple-system, sans-serif; }}
        .wrap {{ display: flex; flex-direction: column; padding: 10px 8px; gap: 8px; }}
        .header {{ text-align: center; padding: 4px 0; }}
        .header .icon {{ font-size: 56px; }}
        .header .title {{ font-size: 20px; font-weight: bold; color: #fff; margin: 2px 0; }}
        .row {{ display: flex; gap: 6px; }}
        .btn {{
            flex: 1; height: 44px; border-radius: 10px;
            font-size: 13px; font-weight: bold; cursor: pointer;
            transition: transform 0.12s; padding: 0 6px;
        }}
        .btn:active {{ transform: scale(0.95); }}
        .btn:hover {{ filter: brightness(1.15); }}
        .btn-gray {{ background: #262730; color: #ccc; border: 1px solid #555; }}
        .btn-blue {{ background: linear-gradient(135deg, #3498db, #2980b9); color: #fff; border: none; }}
        .btn-orange {{ background: linear-gradient(135deg, #e67e22, #d35400); color: #fff; border: none; }}
        .btn-red {{ background: #3a1a1a; color: #ff8888; border: 1px solid #662222; }}
        .divider {{ border-top: 1px solid #333; margin: 4px 0; }}
        .table {{ display: flex; flex-direction: column; gap: 0; }}
        .status {{ text-align: center; padding: 8px; font-size: 16px; font-weight: bold; }}
        .status.ok {{ color: #4CAF50; }}
        .manual-section {{ padding: 4px 0; }}
    </style>
    <div class="wrap">
        <div class="header">
            <div class="icon">📜</div>
            <div class="title">Раздача ролей</div>
        </div>
        <div class="row">
            <button class="btn btn-blue" onclick="clickAR('ar_Случайно')">🎲 Случайно</button>
            <button class="btn btn-orange" onclick="clickAR('ar_Вручную')">✋ Вручную</button>
            <button class="btn btn-red" onclick="clickAR('ar_Сбросить')">🗑️ Сбросить</button>
        </div>
        <div class="divider"></div>
        <div class="manual-section">{manual_html}</div>
        {cancel_html}
        <div class="divider"></div>
        <div class="table">{table_html}</div>
        {"<div class='status ok'>✅ Все роли назначены!</div>" if all_done else ""}
        <div class="divider"></div>
        <div class="row">
            <button class="btn btn-gray" onclick="clickAR('ar_Назад')">⬅️ Назад</button>
            <button class="btn btn-gray" onclick="clickAR('ar_Перемешать')">🔀 Номерки</button>
            <button class="btn" style="{night_style}" onclick="{night_onclick}" {night_disabled}>🌙 Ночь 0</button>
        </div>
    </div>
    <script>
    function clickAR(text) {{
        const buttons = window.parent.document.querySelectorAll('button');
        for (let b of buttons) {{
            if (b.textContent.includes(text)) {{
                b.style.opacity = '1';
                b.style.pointerEvents = 'auto';
                b.click();
                return;
            }}
        }}
    }}
    </script>
    """, height=max(600, 280 + n * 38 + (len(manual_html) > 0) * 200))

    # === Скрытые ST-кнопки ===
    if st.button("ar_Случайно", key="ar_auto"):
        _do_auto_assign(players, roles)
        st.session_state.role_assignment_mode = "auto"
        st.rerun()

    if st.button("ar_Вручную", key="ar_manual"):
        st.session_state.role_assignment_mode = "manual"
        st.session_state.manual_assigned = {}
        for p in players: p['role'] = ""
        st.rerun()

    if st.button("ar_Сбросить", key="ar_reset"):
        for p in players: p['role'] = ""
        st.session_state.manual_assigned = {}
        st.session_state.role_assignment_mode = None
        st.rerun()

    if st.button("ar_Назад", key="ar_back"):
        go("select_players"); st.rerun()

    if st.button("ar_Перемешать", key="ar_shuffle"):
        numbers = list(range(1, n + 1))
        random.shuffle(numbers)
        for i, p in enumerate(sorted(players, key=lambda x: x['number'])):
            p['number'] = numbers[i]
        st.rerun()

    if st.button("ar_Ночь0", key="ar_night0"):
        if all_done:
            go("night_zero"); st.rerun()

    # Кнопки ручного назначения
    for role_name in ["Дон", "Шериф", "Мафия"]:
        for p in sorted_p:
            if st.button(f"ar_m_{role_name}_{p['number']}", key=f"ar_m_{role_name}_{p['number']}"):
                if not p['role']:
                    p['role'] = role_name
                    ma = st.session_state.get('manual_assigned', {})
                    ma[f"{role_name}_{p['number']}"] = p['number']
                    st.session_state.manual_assigned = ma
                    _recalc_peaceful(players, roles)
                    st.rerun()

    # Кнопки снятия роли
    for p in sorted_p:
        if st.button(f"ar_cancel_{p['number']}", key=f"ar_cancel_{p['number']}"):
            p['role'] = ""
            ma = st.session_state.get('manual_assigned', {})
            for k in [k for k, v in ma.items() if v == p['number']]: del ma[k]
            st.session_state.manual_assigned = ma
            _recalc_peaceful(players, roles)
            st.rerun()

    # Прячем ar_ кнопки и скроллим вверх
    components.html("""
    <script>
    (function() {
        function hideArButtons() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(b => {
                const text = b.textContent || '';
                if (text.startsWith('ar_')) {
                    const wrapper = b.closest('div[data-testid="stButton"]');
                    if (wrapper) {
                        wrapper.style.cssText = 'height:0!important;min-height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;opacity:0!important;position:absolute!important;pointer-events:none!important;';
                    }
                }
            });
            const main = window.parent.document.querySelector('section.main');
            if (main) main.scrollTop = 0;
            window.parent.scrollTo(0, 0);
        }
        setTimeout(hideArButtons, 50);
        setTimeout(hideArButtons, 200);
        setTimeout(hideArButtons, 500);
        setTimeout(hideArButtons, 1000);
    })();
    </script>
    """, height=0)



def _do_auto_assign(players, roles):
    role_list = []
    for role, cnt in roles.items():
        role_list.extend([role] * cnt)
    random.shuffle(role_list)
    sorted_p = sorted(players, key=lambda p: p['number'])
    for i, p in enumerate(sorted_p):
        p['role'] = role_list[i]


def _recalc_peaceful(players, roles):
    key_roles = ['Дон', 'Шериф', 'Мафия']
    all_key_done = all(
        len([p for p in players if p['role'] == r]) >= roles.get(r, 0)
        for r in key_roles
    )
    if all_key_done:
        for p in players:
            if not p['role']: p['role'] = "Мирный"
    else:
        for p in players:
            if p['role'] == 'Мирный': p['role'] = ""


def _render_manual_roles_by_role(players, roles, n):
    sorted_p = sorted(players, key=lambda p: p['number'])
    for role_name in ["Дон", "Шериф", "Мафия"]:
        role_count = roles.get(role_name, 0)
        if role_count == 0: continue
        already = [p for p in players if p['role'] == role_name]
        remaining = role_count - len(already)
        if remaining <= 0:
            names = ", ".join([f"#{p['number']}" for p in sorted(already, key=lambda x: x['number'])])
            st.markdown(f"**{role_emoji(role_name)} {role_name}**: {names} ✅")
            continue
        st.markdown(f"**{role_emoji(role_name)} {role_name}** — выберите {remaining}:")

        # Все номерки по порядку, занятые — disabled
        cols_count = 5
        rows_count = math.ceil(n / cols_count)
        for r in range(rows_count):
            columns = st.columns(cols_count)
            for c in range(cols_count):
                idx = r * cols_count + c
                if idx >= n: break
                p = sorted_p[idx]
                with columns[c]:
                    has_role = p['role'] != ""
                    if has_role:
                        lbl = f"{role_emoji(p['role'])}#{p['number']}"
                    else:
                        lbl = f"#{p['number']}"
                    if st.button(lbl, key=f"manual_{role_name}_{p['number']}", disabled=has_role, use_container_width=True):
                        p['role'] = role_name
                        ma = st.session_state.get('manual_assigned', {})
                        ma[f"{role_name}_{p['number']}"] = p['number']
                        st.session_state.manual_assigned = ma
                        _recalc_peaceful(players, roles)
                        st.rerun()
        st.markdown("")


def screen_night_zero():
    game = st.session_state.game

    if "n0_timer_start" not in st.session_state: st.session_state.n0_timer_start = None
    if "n0_timer_duration" not in st.session_state: st.session_state.n0_timer_duration = 60
    if "n0_timer_paused" not in st.session_state: st.session_state.n0_timer_paused = False
    if "n0_timer_paused_remaining" not in st.session_state: st.session_state.n0_timer_paused_remaining = 60

    st.markdown(
        '<div style="text-align:center;padding:20px 0 5px;">'
        '<p style="font-size:80px;margin:0;">🌙</p>'
        '<p style="font-size:22px;font-weight:bold;color:#fff;">Ночь 0 — Знакомство</p></div>',
        unsafe_allow_html=True
    )
    music_player()
    st.markdown("---")

    remaining = _get_n0_remaining()
    progress = min(100, int(((60 - remaining) / 60) * 100))
    is_running = st.session_state.n0_timer_start is not None
    is_paused = st.session_state.n0_timer_paused
    is_idle = not is_running and not is_paused

    col_reset, col_timer, col_pause = st.columns([1, 3, 1])
    with col_reset:
        if not is_idle:
            if st.button("🔄", key="n0_reset", use_container_width=True):
                st.session_state.n0_timer_start = time.time()
                st.session_state.n0_timer_duration = 60
                st.session_state.n0_timer_paused = False; st.rerun()
    with col_pause:
        if is_running:
            if st.button("⏸️", key="n0_pause", use_container_width=True):
                st.session_state.n0_timer_paused = True
                st.session_state.n0_timer_paused_remaining = remaining
                st.session_state.n0_timer_start = None; st.rerun()
        elif is_paused:
            if st.button("▶️", key="n0_unpause", use_container_width=True):
                st.session_state.n0_timer_paused = False
                st.session_state.n0_timer_start = time.time()
                st.session_state.n0_timer_duration = st.session_state.n0_timer_paused_remaining; st.rerun()
    with col_timer:
        timer_ph = st.empty()

    color = "white" if remaining > 10 else "red"
    timer_ph.markdown(f'''
    <div style="text-align:center;">
        <p style="font-size:72px;font-weight:bold;margin:0;color:{color};line-height:1;">{remaining}</p>
        <div style="background:#333;border-radius:6px;height:8px;margin:4px 20px;">
            <div style="background:#4CAF50;width:{progress}%;height:100%;border-radius:6px;"></div>
        </div>
    </div>''', unsafe_allow_html=True)

    if is_idle:
        if st.button("▶️ Старт таймера", use_container_width=True, key="n0_start"):
            st.session_state.n0_timer_start = time.time()
            st.session_state.n0_timer_duration = 60; st.rerun()

    st.markdown("---")
    st.markdown("### 📝 Заметки ведущего")
    notes = st.text_area("Очерёдность стрельбы:", value=st.session_state.get('mafia_notes', ''), key="mn_input", height=100)
    st.session_state.mafia_notes = notes
    st.markdown("---")

    # Кнопка ТОЛЬКО когда таймер не крутится
    if not is_running:
        if st.button("☀️ Наступает Утро 1", use_container_width=True, key="to_day1"):
            st.session_state.day_number = 1
            st.session_state.current_speaker = 0
            st.session_state.nominees = {}
            st.session_state.game_log.append("Ночь 0: Знакомство")
            st.session_state.n0_timer_start = None
            st.session_state.n0_timer_paused = False
            go("game_day"); st.rerun()


    if is_running:
        _run_n0_timer(timer_ph)


def _get_n0_remaining():
    if st.session_state.get("n0_timer_paused"):
        return st.session_state.get("n0_timer_paused_remaining", 60)
    if st.session_state.get("n0_timer_start") is None:
        return st.session_state.get("n0_timer_duration", 60)
    elapsed = time.time() - st.session_state.n0_timer_start
    return max(0, st.session_state.n0_timer_duration - int(elapsed))


def _run_n0_timer(timer_ph):
    start = st.session_state.n0_timer_start
    total = st.session_state.n0_timer_duration
    if start is None: return
    while True:
        elapsed = time.time() - start
        sec = max(0, total - int(elapsed))
        progress = min(100, int(((total - sec) / max(total, 1)) * 100))
        color = "white" if sec > 10 else "red"
        timer_ph.markdown(f'''
        <div style="text-align:center;">
            <p style="font-size:72px;font-weight:bold;margin:0;color:{color};line-height:1;">{sec}</p>
            <div style="background:#333;border-radius:6px;height:8px;margin:4px 20px;">
                <div style="background:#4CAF50;width:{progress}%;height:100%;border-radius:6px;"></div>
            </div>
        </div>''', unsafe_allow_html=True)
        if sec <= 10 and sec > 0: play_sound_html(METRONOME_SOUND)
        if sec == 0: play_sound_html(WHISTLE_SOUND); break
        time.sleep(1)


def screen_players_list():
    db = load_db()
    st.markdown(
        '<div style="text-align:center;padding:20px 0 5px;">'
        '<p style="font-size:80px;margin:0;">📋</p>'
        '<p style="font-size:22px;font-weight:bold;color:#fff;">База игроков</p></div>',
        unsafe_allow_html=True
    )
    with st.form("add_player"):
        c1, c2 = st.columns(2)
        rn = c1.text_input("Реальное имя"); nn = c2.text_input("Псевдоним")
        if st.form_submit_button("➕ Добавить") and rn and nn:
            db['players'].append({"id": str(uuid.uuid4()), "real_name": rn.strip(), "nickname": nn.strip(), "history": []})
            save_db(db); st.rerun()
    for idx, p in enumerate(db['players']):
        with st.expander(f"🧑 {p['real_name']} ({p['nickname']})"):
            nn = st.text_input("Имя", value=p['real_name'], key=f"ed_n_{idx}")
            nk = st.text_input("Псевдоним", value=p['nickname'], key=f"ed_k_{idx}")
            if st.button("💾", key=f"ed_s_{idx}"):
                p['real_name'] = nn.strip(); p['nickname'] = nk.strip(); save_db(db); st.rerun()
    st.markdown("---")
    if st.button("⬅️ Назад", use_container_width=True): go("main_menu"); st.rerun()


def screen_edit_player():
    db = load_db()
    pid = st.session_state.get('edit_player_id')
    player = get_player(db, pid) if pid else None
    if not player:
        st.error("Не найден")
        if st.button("⬅️"): go("players_list"); st.rerun()
        return
    st.header(f"✏️ {player['real_name']}")
    if st.button("⬅️ Назад", use_container_width=True): go("players_list"); st.rerun()
    new_name = st.text_input("Имя", value=player['real_name'], key="edit_rn")
    new_nick = st.text_input("Псевдоним", value=player['nickname'], key="edit_nn")
    if st.button("💾 Сохранить", use_container_width=True):
        player['real_name'] = new_name.strip(); player['nickname'] = new_nick.strip()
        save_db(db); go("players_list"); st.rerun()