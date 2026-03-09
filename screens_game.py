import streamlit as st
import math
import time
from shared import (
    go, get_alive, get_speaker_order,
    play_sound_html, METRONOME_SOUND, WHISTLE_SOUND, sync_music,
    role_emoji, p_num, p_name, p_bar_text
)
import streamlit.components.v1 as components

GRID_COLS = 5


def _toggle_roles():
    st.session_state.show_roles = st.session_state.get("show_roles_cb", False)


def screen_game_day():
    sync_music()
    game = st.session_state.game
    players = game['players']
    day = st.session_state.day_number
    order = get_speaker_order(day, players)
    speaker_idx = st.session_state.current_speaker

    if "day_phase" not in st.session_state: st.session_state.day_phase = "idle"
    if "timer_start_time" not in st.session_state: st.session_state.timer_start_time = None
    if "timer_duration" not in st.session_state: st.session_state.timer_duration = 60
    if "timer_paused" not in st.session_state: st.session_state.timer_paused = False
    if "timer_paused_remaining" not in st.session_state: st.session_state.timer_paused_remaining = 60

    phase = st.session_state.day_phase
    all_done = speaker_idx >= len(order)
    show_roles = st.session_state.get("show_roles", False)

    # --- Хелперы форматирования ---
    def fmt_num(p):
        """Номер: -5- или -5-⭐"""
        base = f"-{p['number']}-"
        if show_roles and p.get('role'):
            base += role_emoji(p['role'])
        return base

    def fmt_full(p):
        """Полное: -5- Князь или -5-⭐ Князь (Шериф)"""
        num = fmt_num(p)
        nick = p['nickname']
        if show_roles and p.get('role'):
            return f"{num} {nick} ({p['role']})"
        return f"{num} {nick}"

    def fmt_grid(p):
        """Для сетки: -5- или -5-⭐"""
        return fmt_num(p)

    # --- Текущий и следующий ---
    is_first_speaker = False
    is_last_speaker = False
    if not all_done:
        current = order[speaker_idx]
        is_first_speaker = (speaker_idx == 0)
        is_last_speaker = (speaker_idx == len(order) - 1)
        if is_first_speaker:
            current_label = f"📢 Открывает стол {fmt_full(current)}"
        elif is_last_speaker:
            current_label = f"🔒 Закрывает стол {fmt_full(current)}"
        else:
            current_label = f"🗣️ Говорит {fmt_full(current)}"
        if speaker_idx + 1 < len(order):
            nxt = order[speaker_idx + 1]
            next_label = f"Готовится {fmt_full(nxt)}"
        else:
            next_label = ""
    else:
        current_label = "✅ Все высказались"
        next_label = ""

    remaining = _get_remaining()
    if phase != "speaking":
        timer_color = "#555"
    elif remaining > 10:
        timer_color = "#fff"
    elif remaining > 5:
        timer_color = "#ff8c00"
    else:
        timer_color = "#ff2222"

    # --- Главная кнопка ---
    if all_done:
        has_nominees = bool(st.session_state.get("nominees"))
        if has_nominees:
            main_btn_html = """
            <div class="btn-row" style="margin:4px 0;">
                <button class="btn btn-gray" onclick="clickDay('day_НикогоНочь')">❌ Никого → Ночь</button>
                <button class="btn btn-gold" onclick="clickDay('day_Голосование')">🗳️ Голосование</button>
            </div>
            """
        else:
            main_btn_html = """
            <button class="btn btn-gold" style="width:100%;height:52px;border-radius:12px;font-size:16px;font-weight:bold;cursor:pointer;border:none;"
                onclick="clickDay('day_НикогоНочь')">🌙 К ночи</button>
            """
    elif phase == "idle":
        cur = order[speaker_idx]
        label = f"▶️ Старт {fmt_full(cur)}"
        if is_first_speaker or is_last_speaker:
            main_btn_html = f'<button class="main-btn-special" onclick="clickDay(\'day_Старт\')">{label}</button>'
        else:
            main_btn_html = f'<button class="main-btn-start" onclick="clickDay(\'day_Старт\')">{label}</button>'
    else:
        main_btn_html = '<button class="main-btn-thanks" onclick="clickDay(\'day_Спасибо\')">🙏 Спасибо</button>'

    sorted_all = sorted(players, key=lambda p: p['number'])
    order_nums = [p['number'] for p in order]
    bars_html = _build_bars_html(sorted_all, order_nums, speaker_idx, phase, remaining, fmt_num, fmt_full, show_roles)
    nom_grid_html = _build_nom_grid(sorted_all, day, fmt_grid)
    nom_summary_html = _build_nom_summary(players, fmt_num, fmt_full)
    fouls_grid_html = _build_fouls_grid(sorted_all, day, fmt_grid)

    roles_label = "🙈 Скрыть роли" if show_roles else "👁️ Показать роли"

    components.html(f"""
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:transparent; font-family:-apple-system,sans-serif; }}
        .wrap {{ display:flex; flex-direction:column; padding:10px 8px; gap:8px; }}
        .header {{ text-align:center; }}
        .header .icon {{ font-size:56px; }}
        .header .title {{ font-size:22px; font-weight:bold; color:#fff; }}

        .timer-row {{
            display:flex; align-items:center; justify-content:center; gap:12px;
            padding:4px 0;
        }}
        .timer-small-btn {{
            width:44px; height:44px; border-radius:50%;
            background:#262730; border:1px solid #555; color:#ccc;
            font-size:18px; cursor:pointer; display:flex;
            align-items:center; justify-content:center;
        }}
        .timer-small-btn:active {{ transform:scale(0.9); }}
        .timer-num {{
            font-size:120px; font-weight:bold; color:{timer_color};
            min-width:160px; text-align:center; line-height:1;
        }}

        .main-btn-start {{
            width:100%; height:52px; border-radius:12px;
            font-size:16px; font-weight:bold; cursor:pointer;
            border:none; background:linear-gradient(135deg,#27ae60,#219a52); color:#fff;
        }}
        .main-btn-thanks {{
            width:100%; height:52px; border-radius:12px;
            font-size:16px; font-weight:bold; cursor:pointer;
            border:none; background:linear-gradient(135deg,#e67e22,#d35400); color:#fff;
        }}
        .main-btn-special {{
            width:100%; height:56px; border-radius:12px;
            font-size:17px; font-weight:bold; cursor:pointer;
            border:none; color:#fff;
            animation: pulseBtn 2s ease-in-out infinite;
        }}
        @keyframes pulseBtn {{
            0%   {{ background:linear-gradient(135deg,#DAA520,#B8860B); box-shadow:0 0 15px rgba(218,165,32,0.5); }}
            50%  {{ background:linear-gradient(135deg,#8e44ad,#6c3483); box-shadow:0 0 15px rgba(142,68,173,0.5); }}
            100% {{ background:linear-gradient(135deg,#DAA520,#B8860B); box-shadow:0 0 15px rgba(218,165,32,0.5); }}
        }}
        [class^="main-btn"]:active {{ transform:scale(0.95); }}

        .speaker-label {{ text-align:center; padding:4px 0; }}
        .speaker-current {{ font-size:18px; font-weight:bold; color:#fff; }}
        .speaker-next {{ font-size:14px; color:#888; margin-top:2px; }}
        .divider {{ border-top:1px solid #333; width:100%; margin:4px 0; }}

        .bar {{
            height:44px; display:flex; align-items:center;
            padding:0 8px; margin:2px 0; border-radius:6px;
            font-size:18px; font-weight:bold; position:relative;
            overflow:hidden; color:#fff;
        }}
        .bar-fill {{
            position:absolute; left:0; top:0; bottom:0;
            border-radius:6px; z-index:0;
            transition: width 0.9s linear;
        }}
        .bar-content {{
            position:relative; z-index:1; width:100%;
            display:grid;
            grid-template-columns: 28px 44px 28px 1fr auto;
            align-items:center;
            gap:4px;
        }}
        .bar-col-status {{ text-align:center; font-size:16px; }}
        .bar-col-num {{ text-align:center; color:#ccc; }}
        .bar-col-emoji {{ text-align:center; font-size:16px; }}
        .bar-col-nick {{ text-align:left; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
        .bar-col-role {{ text-align:right; font-size:13px; color:#888; font-weight:normal; padding-right:4px; }}
        .bar-col-fouls {{ text-align:right; min-width:20px; }}
        .bar-dead {{ background:#111; color:#555; }}
        .bar-dead .bar-content {{ text-decoration:line-through; }}
        .bar-waiting {{ background:#1a1a3d; }}
        .bar-done {{ background:#1a2e1a; }}
        .bar-speaking {{ background:#1a3a1a; }}

        .grid {{ display:flex; flex-wrap:wrap; gap:4px; }}
        .grid-btn {{
            flex:0 0 18%; height:44px; border-radius:6px;
            font-size:22px; font-weight:bold; cursor:pointer;
            border:1px solid #555; background:#262730; color:#ccc;
        }}
        .grid-btn:active {{ transform:scale(0.95); }}
        .grid-btn.dead {{ background:#111; color:#444; border-color:#333; cursor:default; }}
        .grid-btn.selected {{ background:#1a3a1a; border-color:#4CAF50; color:#fff; }}
        .grid-btn.foul-btn {{ border-color:#666; }}
        .grid-btn.foul-max {{ background:#3a1a1a; border-color:#662222; color:#ff4444; }}

        .section-title {{ font-size:20px; font-weight:bold; color:#aaa; padding:4px 0; }}
        .nom-summary {{
            font-size:28px; color:#ccc; padding:8px 12px;
            background:#1a1a2e; border-radius:6px; margin:4px 0;
            line-height:1.2;
        }}

        .btn-row {{ display:flex; gap:8px; width:100%; }}
        .btn {{
            flex:1; height:48px; border-radius:12px;
            font-size:15px; font-weight:bold; cursor:pointer;
            border:none; display:flex; align-items:center; justify-content:center;
        }}
        .btn:active {{ transform:scale(0.95); }}
        .btn:hover {{ filter:brightness(1.15); }}
        .btn-gray {{ background:#262730; color:#ccc; border:1px solid #555; }}
        .btn-gold {{
            background:linear-gradient(135deg,#DAA520,#B8860B); color:#fff;
            box-shadow:0 0 12px rgba(218,165,32,0.4);
        }}
        .btn-roles {{
            width:100%; height:40px; border-radius:10px;
            background:#1a1a2e; border:1px solid #444; color:#888;
            font-size:13px; font-weight:bold; cursor:pointer;
        }}
        .btn-roles:active {{ transform:scale(0.95); }}
    </style>

    <div class="wrap">
        <div class="header">
            <div class="icon">☀️</div>
            <div class="title">День {day}</div>
        </div>

        <div class="timer-row">
            <button class="timer-small-btn" onclick="clickDay('day_Сброс')">🔄</button>
            <div class="timer-num" id="timerNum">{remaining}</div>
            <button class="timer-small-btn" onclick="clickDay('day_ТПауза')">⏸️</button>
        </div>

        {main_btn_html}

        <div class="speaker-label">
            <div class="speaker-current">{current_label}</div>
            <div class="speaker-next">{next_label}</div>
        </div>

        <div class="divider"></div>
        {bars_html}
        <div class="divider"></div>

        <div class="section-title">🗳️ Выставление на голосование</div>
        <div class="grid">{nom_grid_html}</div>
        {nom_summary_html}

        <div class="divider"></div>

        <div class="section-title">⚠️ Фолы</div>
        <div class="grid">{fouls_grid_html}</div>

        <div class="divider"></div>

        <button class="btn-roles" onclick="clickDay('day_Роли')">{roles_label}</button>
    </div>

    <script>
    function clickDay(text) {{
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
    """, height=_calc_day_height(players, all_done, st.session_state.get("nominees")))

    # === Скрытые ST-кнопки ===
    if st.button("day_Старт", key="day_start"):
        st.session_state.day_phase = "speaking"
        st.session_state.timer_start_time = time.time()
        st.session_state.timer_duration = 60
        st.session_state.timer_paused = False
        st.rerun()

    if st.button("day_Спасибо", key="day_thanks"):
        st.session_state.timer_start_time = None
        st.session_state.timer_paused = False
        st.session_state.day_phase = "idle"
        st.session_state.current_speaker += 1
        st.session_state.timer_duration = 60
        st.session_state.timer_paused_remaining = 60
        st.rerun()

    if st.button("day_Сброс", key="day_reset"):
        if phase == "speaking":
            st.session_state.timer_start_time = time.time()
            st.session_state.timer_duration = 60
            st.session_state.timer_paused = False
        st.rerun()

    if st.button("day_ТПауза", key="day_tpause"):
        if phase == "speaking":
            if st.session_state.timer_paused:
                st.session_state.timer_paused = False
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_duration = st.session_state.timer_paused_remaining
            else:
                st.session_state.timer_paused = True
                st.session_state.timer_paused_remaining = _get_remaining()
                st.session_state.timer_start_time = None
        st.rerun()

    sorted_all = sorted(players, key=lambda p: p['number'])
    for p in sorted_all:
        if st.button(f"day_nom_{p['number']}", key=f"day_nom_{p['number']}"):
            if not all_done and speaker_idx < len(order) and p['status'] == 'alive':
                by_num = order[speaker_idx]['number']
                st.session_state.nominees[by_num] = p['number']
                st.session_state.game_log.append(f"День {day}: -{by_num}- → -{p['number']}-")
            st.rerun()

    for p in sorted_all:
        if st.button(f"day_foul_{p['number']}", key=f"day_foul_{p['number']}"):
            if p['status'] != 'dead' and p['fouls'] < 4:
                p['fouls'] += 1
            st.rerun()

    if st.button("day_НикогоНочь", key="day_noone"):
        st.session_state.game_log.append(f"День {day}: никого")
        _reset_day()
        go("game_night")
        st.rerun()

    if st.button("day_Голосование", key="day_vote"):
        st.session_state.vote_voters = {}
        st.session_state.vote_step = 0
        _reset_day()
        go("game_vote")
        st.rerun()

    if st.button("day_Роли", key="day_roles"):
        st.session_state.show_roles = not st.session_state.get("show_roles", False)
        st.rerun()

    if phase == "speaking" and not st.session_state.timer_paused and st.session_state.timer_start_time:
        _run_day_live()

    components.html("""
    <script>
    (function() {
        function hide() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(b => {
                if ((b.textContent || '').startsWith('day_')) {
                    const w = b.closest('div[data-testid="stButton"]');
                    if (w) w.style.cssText = 'height:0!important;min-height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;opacity:0!important;position:absolute!important;pointer-events:none!important;';
                }
            });
        }
        setTimeout(hide, 50);
        setTimeout(hide, 200);
        setTimeout(hide, 500);
        setTimeout(hide, 1000);
    })();
    </script>
    """, height=0)


def _build_bars_html(sorted_all, order_nums, speaker_idx, phase, remaining, fmt_num, fmt_full, show_roles):
    html = ""
    for p in sorted_all:
        foul_dots = "❗" * p['fouls'] if p['fouls'] > 0 else ""
        num_str = f"-{p['number']}-"
        nick = p['nickname']
        emoji = role_emoji(p['role']) if show_roles and p.get('role') else ""
        role_word = f"({p['role']})" if show_roles and p.get('role') else ""

        if p['status'] == 'dead':
            html += (
                f'<div class="bar bar-dead">'
                f'<div class="bar-content" style="opacity:0.5;text-decoration:line-through;">'
                f'<span class="bar-col-status">💀</span>'
                f'<span class="bar-col-num">{num_str}</span>'
                f'<span class="bar-col-emoji">{emoji}</span>'
                f'<span class="bar-col-nick">{nick}</span>'
                f'<span class="bar-col-role">{role_word}</span>'
                f'</div></div>'
            )
            continue

        pos = order_nums.index(p['number']) if p['number'] in order_nums else 999

        if pos < speaker_idx:
            status_icon = "✅"
            bar_class = "bar-done"
            fill_html = '<div class="bar-fill" style="width:100%;background:rgba(76,175,80,0.2);"></div>'
        elif pos == speaker_idx:
            bar_class = "bar-speaking"
            if phase == "speaking":
                status_icon = "🗣️"
                if st.session_state.get("timer_start_time"):
                    elapsed = time.time() - st.session_state.timer_start_time
                    total = st.session_state.get("timer_duration", 60)
                    current_pct = min(100, int((elapsed / max(total, 1)) * 100))
                    fill_html = f'<div class="bar-fill" id="speakerFill" style="width:{current_pct}%;background:rgba(76,175,80,0.5);"></div>'
                elif st.session_state.get("timer_paused"):
                    rem = st.session_state.get("timer_paused_remaining", 60)
                    paused_pct = min(100, int(((60 - rem) / 60) * 100))
                    fill_html = f'<div class="bar-fill" id="speakerFill" style="width:{paused_pct}%;background:rgba(255,165,0,0.4);"></div>'
                else:
                    fill_html = '<div class="bar-fill" id="speakerFill" style="width:0%;background:rgba(76,175,80,0.5);"></div>'
            else:
                status_icon = "➡️"
                fill_html = '<div class="bar-fill" id="speakerFill" style="width:0%;background:rgba(76,175,80,0.5);"></div>'
        else:
            status_icon = ""
            bar_class = "bar-waiting"
            fill_html = ""

        html += (
            f'<div class="bar {bar_class}">'
            f'{fill_html}'
            f'<div class="bar-content">'
            f'<span class="bar-col-status">{status_icon}</span>'
            f'<span class="bar-col-num">{num_str}</span>'
            f'<span class="bar-col-emoji">{emoji}</span>'
            f'<span class="bar-col-nick">{nick}</span>'
            f'<span class="bar-col-role">{role_word} {foul_dots}</span>'
            f'</div></div>'
        )

    return html

def _build_nom_grid(sorted_all, day, fmt_grid):
    nominated_nums = list(st.session_state.get("nominees", {}).values())
    html = ""
    for p in sorted_all:
        is_dead = p['status'] == 'dead'
        is_nom = p['number'] in nominated_nums
        label = fmt_grid(p)
        if is_dead:
            html += f'<button class="grid-btn dead" disabled>{label}</button>'
        elif is_nom:
            html += f'<button class="grid-btn selected" onclick="clickDay(\'day_nom_{p["number"]}\')">🗳️{label}</button>'
        else:
            html += f'<button class="grid-btn" onclick="clickDay(\'day_nom_{p["number"]}\')">{label}</button>'
    return html


def _build_nom_summary(players, fmt_num, fmt_full):
    nominees = st.session_state.get("nominees", {})
    if not nominees:
        return ""
    grouped = {}
    for by_n, who_n in nominees.items():
        grouped.setdefault(who_n, []).append(by_n)
    html = ""
    for who_n, by_list in grouped.items():
        who_p = next((x for x in players if x['number'] == who_n), None)
        by_strs = []
        for bn in by_list:
            bp = next((x for x in players if x['number'] == bn), None)
            by_strs.append(fmt_num(bp) if bp else f"-{bn}-")
        who_str = fmt_full(who_p) if who_p else f"-{who_n}-"
        html += f'<div class="nom-summary">🗳️ <b>{who_str}</b> ← {", ".join(by_strs)}</div>'
    return html


def _build_fouls_grid(sorted_all, day, fmt_grid):
    html = ""
    for p in sorted_all:
        is_dead = p['status'] == 'dead'
        foul_dots = "❗" * p['fouls'] if p['fouls'] > 0 else ""
        at_max = p['fouls'] >= 4
        label = fmt_grid(p)
        if is_dead:
            html += f'<button class="grid-btn dead" disabled>{label}</button>'
        elif at_max:
            html += f'<button class="grid-btn foul-max" disabled>🚫{label}</button>'
        else:
            html += f'<button class="grid-btn foul-btn" onclick="clickDay(\'day_foul_{p["number"]}\')">{foul_dots}{label}</button>'
    return html


def _calc_day_height(players, all_done, nominees):
    n = len(players)
    h = 500
    h += n * 50          # bars стали выше
    h += 70 + (n // 5 + 1) * 52   # nom grid
    if nominees:
        h += len(set(nominees.values())) * 80  # nom summary крупнее
    else:
        h += 80
    h += 70 + (n // 5 + 1) * 52   # fouls grid
    if all_done:
        h += 70
    h += 60
    h += 150
    return h



def _reset_day():
    st.session_state.day_phase = "idle"
    st.session_state.timer_start_time = None
    st.session_state.timer_duration = 60
    st.session_state.timer_paused = False
    st.session_state.timer_paused_remaining = 60


def _run_day_live():
    start = st.session_state.timer_start_time
    total = st.session_state.timer_duration
    if not start:
        return

    while True:
        elapsed = time.time() - start
        sec = max(0, total - int(elapsed))
        pct = min(100, int((elapsed / max(total, 1)) * 100))

        if sec > 10:
            color = "#fff"
        elif sec > 5:
            color = "#ff8c00"
        else:
            color = "#ff2222"

        components.html(f"""
        <script>
        (function() {{
            var pd = window.parent.document;
            var frames = pd.querySelectorAll('iframe');
            for (var f of frames) {{
                try {{
                    var doc = f.contentDocument || f.contentWindow.document;
                    var num = doc.getElementById('timerNum');
                    var fill = doc.getElementById('speakerFill');
                    if (num) {{
                        num.textContent = '{sec}';
                        num.style.color = '{color}';
                    }}
                    if (fill) {{
                        fill.style.width = '{pct}%';
                    }}
                    if (num) break;
                }} catch(e) {{}}
            }}
        }})();
        </script>
        """, height=0)

        if sec <= 10 and sec > 0:
            play_sound_html(METRONOME_SOUND)
        if sec == 0:
            play_sound_html(WHISTLE_SOUND)
            time.sleep(1.5)
            break

        time.sleep(1)


def _get_remaining():
    if st.session_state.get("timer_paused"):
        return st.session_state.get("timer_paused_remaining", 60)
    if st.session_state.get("timer_start_time") is None:
        return st.session_state.get("timer_duration", 60)
    elapsed = time.time() - st.session_state.timer_start_time
    return max(0, st.session_state.timer_duration - int(elapsed))


# ====== VOTING ======
def screen_game_vote():
    game = st.session_state.game
    players = game['players']
    day = st.session_state.day_number
    alive = get_alive()
    nominees = st.session_state.nominees
    unique_nominated = list(set(nominees.values()))

    st.markdown(
        f'<div style="text-align:center;padding:20px 0 5px;">'
        f'<p style="font-size:80px;margin:0;">🗳️</p>'
        f'<p style="font-size:22px;font-weight:bold;color:#fff;">'
        f'Голосование — День {day}</p></div>',
        unsafe_allow_html=True
    )

    nom_html = ""
    for nom in unique_nominated:
        p = next(pp for pp in players if pp['number'] == nom)
        nom_html += (
            f'<div style="display:inline-block;text-align:center;margin:0 12px;">'
            f'<p style="font-size:48px;font-weight:bold;margin:0;color:#ff8844;">{p_num(p)}</p>'
            f'<p style="font-size:14px;color:#aaa;margin:0;">{p_name(p)}</p></div>'
        )
    st.markdown(f'<div style="text-align:center;padding:10px 0;">{nom_html}</div>', unsafe_allow_html=True)
    st.markdown("---")

    if day == 1 and len(unique_nominated) == 1:
        st.warning("⚠️ Первый день: единственная кандидатура НЕ исключается!")
        if st.button("🌙 К ночи", use_container_width=True):
            st.session_state.game_log.append(f"День {day}: единственная кандидатура")
            go("game_night"); st.rerun()
        return

    if day > 1 and len(unique_nominated) == 1:
        nom_num = unique_nominated[0]
        nom_p = next(p for p in players if p['number'] == nom_num)
        st.info(f"{p_num(nom_p)} {p_name(nom_p)} — исключён")
        nom_p['status'] = 'dead'
        st.session_state.eliminated_today = [nom_num]
        st.session_state.game_log.append(f"День {day}: Исключён #{nom_num}")
        go("game_last_word"); st.rerun()
        return

    if "vote_step" not in st.session_state: st.session_state.vote_step = 0
    if "vote_voters" not in st.session_state: st.session_state.vote_voters = {}
    for nom in unique_nominated:
        if nom not in st.session_state.vote_voters: st.session_state.vote_voters[nom] = []

    step = st.session_state.vote_step
    all_voted_prev = set()
    for i, nom in enumerate(unique_nominated):
        if i < step: all_voted_prev.update(st.session_state.vote_voters.get(nom, []))

    st.markdown("### Очередь:")
    for i, nom in enumerate(unique_nominated):
        p = next(pp for pp in players if pp['number'] == nom)
        cnt = len(st.session_state.vote_voters.get(nom, []))
        if i == step:
            st.markdown(
                f'<div style="background:#2d1a4e;padding:8px 16px;border-radius:8px;'
                f'margin:4px 0;font-size:18px;font-weight:bold;color:white;">'
                f'▶️ {p_num(p)} {p_name(p)} — {cnt} гол.</div>',
                unsafe_allow_html=True
            )
        elif i < step:
            st.markdown(
                f'<div style="background:#3d3520;padding:6px 16px;border-radius:8px;'
                f'margin:4px 0;font-size:16px;color:#ccc;">'
                f'✅ {p_num(p)} {p_name(p)} — {cnt} гол.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="background:#1a1a3d;padding:6px 16px;border-radius:8px;'
                f'margin:4px 0;font-size:16px;color:#888;">'
                f'{p_num(p)} {p_name(p)}</div>',
                unsafe_allow_html=True
            )

    st.markdown("---")

    if step < len(unique_nominated):
        nom_num = unique_nominated[step]
        nom_p = next(p for p in players if p['number'] == nom_num)

        if step == len(unique_nominated) - 1:
            remaining_v = [a for a in alive if a['number'] not in all_voted_prev]
            st.session_state.vote_voters[nom_num] = [a['number'] for a in remaining_v]

            st.markdown("### 📊 Результаты голосования")

            all_results = {}
            for nom in unique_nominated:
                all_results[nom] = st.session_state.vote_voters.get(nom, [])
            max_votes = max(len(v) for v in all_results.values())

            for nom in unique_nominated:
                p_nom = next(pp for pp in players if pp['number'] == nom)
                voters = all_results[nom]
                cnt = len(voters)
                is_max = cnt == max_votes

                if is_max:
                    bg = "#4a1a1a"; border = "3px solid #cc0000"; num_color = "#ff4444"; badge = " 💀"
                else:
                    bg = "#1a1a3d"; border = "1px solid #333"; num_color = "#ff8844"; badge = ""

                voter_tags = []
                for v_num in sorted(voters):
                    vp = next(pp for pp in players if pp['number'] == v_num)
                    voter_tags.append(f'<span style="background:#333;padding:2px 8px;'
                                      f'border-radius:4px;margin:2px;font-size:14px;'
                                      f'color:#ccc;">{p_num(vp)}</span>')
                voters_html = " ".join(voter_tags) if voter_tags else '<span style="color:#666;">—</span>'

                st.markdown(
                    f'<div style="background:{bg};border:{border};border-radius:12px;'
                    f'padding:16px;margin:8px 0;">'
                    f'<div style="display:flex;align-items:center;gap:12px;">'
                    f'<span style="font-size:48px;font-weight:bold;color:{num_color};">'
                    f'{p_num(p_nom)}{badge}</span>'
                    f'<div>'
                    f'<p style="font-size:20px;color:#fff;margin:0;font-weight:bold;">'
                    f'{p_name(p_nom)}</p>'
                    f'<p style="font-size:24px;color:#ff8844;margin:0;font-weight:bold;">'
                    f'{cnt} голосов</p>'
                    f'</div></div>'
                    f'<div style="margin-top:8px;">{voters_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            st.markdown("---")
            if st.button("📊 Итоги", use_container_width=True, key="vote_results"):
                _do_vote_results(players, unique_nominated, day)
        else:
            st.markdown(
                f'<div style="text-align:center;padding:10px;">'
                f'<p style="font-size:24px;font-weight:bold;color:white;">'
                f'За исключение {p_num(nom_p)} {p_name(nom_p)}</p></div>',
                unsafe_allow_html=True
            )
            voted_for = st.session_state.vote_voters.get(nom_num, [])
            st.write(f"Голосов: **{len(voted_for)}**")

            sorted_all = sorted(players, key=lambda p: p['number'])
            n = len(sorted_all)
            rows = math.ceil(n / GRID_COLS)
            for r in range(rows):
                cols = st.columns(GRID_COLS)
                for c in range(GRID_COLS):
                    idx = r * GRID_COLS + c
                    if idx >= n: break
                    voter = sorted_all[idx]
                    with cols[c]:
                        is_dead = voter['status'] == 'dead'
                        in_prev = voter['number'] in all_voted_prev
                        is_sel = voter['number'] in voted_for
                        disabled = is_dead or in_prev
                        if is_sel:
                            label = f"✅{p_num(voter)}"
                        else:
                            label = p_num(voter)
                        if st.button(label, key=f"vt_{step}_{voter['number']}", disabled=disabled, use_container_width=True):
                            if is_sel: st.session_state.vote_voters[nom_num].remove(voter['number'])
                            else: st.session_state.vote_voters[nom_num].append(voter['number'])
                            st.rerun()

            if st.button("➡️ Далее", use_container_width=True, key="vote_next"):
                st.session_state.vote_step += 1; st.rerun()


def _do_vote_results(players, unique_nominated, day):
    results = {nom: len(st.session_state.vote_voters.get(nom, [])) for nom in unique_nominated}
    max_v = max(results.values())
    winners = [n for n, v in results.items() if v == max_v]

    if len(winners) > 1:
        st.session_state.catastrophe_tied = winners
        st.session_state.game_log.append(f"День {day}: Автокатастрофа")
        st.session_state.vote_step = 0
        go("game_vote_catastrophe"); st.rerun()
    else:
        num = winners[0]
        next(pp for pp in players if pp['number'] == num)['status'] = 'dead'
        st.session_state.eliminated_today = [num]
        st.session_state.game_log.append(f"День {day}: Исключён #{num}")
        st.session_state.vote_step = 0
        go("game_last_word"); st.rerun()


def screen_game_vote_catastrophe():
    game = st.session_state.game
    players = game['players']
    day = st.session_state.day_number
    tied = st.session_state.get('catastrophe_tied', [])

    if "cat_speaker_idx" not in st.session_state: st.session_state.cat_speaker_idx = 0
    if "cat_phase" not in st.session_state: st.session_state.cat_phase = "idle"
    if "cat_timer_start" not in st.session_state: st.session_state.cat_timer_start = None
    if "cat_timer_duration" not in st.session_state: st.session_state.cat_timer_duration = 30
    if "cat_timer_paused" not in st.session_state: st.session_state.cat_timer_paused = False
    if "cat_timer_paused_remaining" not in st.session_state: st.session_state.cat_timer_paused_remaining = 30

    st.markdown(
        '<div style="text-align:center;padding:20px 0 5px;">'
        '<p style="font-size:80px;margin:0;">💥</p>'
        '<p style="font-size:22px;font-weight:bold;color:#fff;">Автокатастрофа!</p></div>',
        unsafe_allow_html=True
    )

    nom_html = ""
    for num in tied:
        p = next(pp for pp in players if pp['number'] == num)
        nom_html += (
            f'<div style="display:inline-block;text-align:center;margin:0 12px;">'
            f'<p style="font-size:48px;font-weight:bold;margin:0;color:#ff8844;">{p_num(p)}</p>'
            f'<p style="font-size:14px;color:#aaa;margin:0;">{p_name(p)}</p></div>'
        )
    st.markdown(f'<div style="text-align:center;padding:10px 0;">{nom_html}</div>', unsafe_allow_html=True)
    st.markdown("---")

    speaker_idx = st.session_state.cat_speaker_idx
    phase = st.session_state.cat_phase
    all_done = speaker_idx >= len(tied)
    prev_voters = st.session_state.get('vote_voters', {})

    if all_done:
        st.success("✅ Все высказались!")
        _render_cat_bars(players, tied, prev_voters, speaker_idx)
        st.markdown("---")
        if st.button("🗳️ Переголосовать", use_container_width=True, key="cat_revote"):
            _reset_cat()
            st.session_state.vote_voters = {}; st.session_state.vote_step = 0
            go("game_vote"); st.rerun()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❌ Исключить всех", use_container_width=True, key="cat_elim"):
                for num in tied:
                    next(pp for pp in players if pp['number'] == num)['status'] = 'dead'
                st.session_state.eliminated_today = tied
                st.session_state.game_log.append(f"День {day}: Исключены все")
                _reset_cat(); go("game_last_word"); st.rerun()
        with c2:
            if st.button("✅ Оставить всех", use_container_width=True, key="cat_keep"):
                st.session_state.game_log.append(f"День {day}: Оставлены все")
                _reset_cat(); go("game_night"); st.rerun()
        return

    current_num = tied[speaker_idx]
    current_p = next(pp for pp in players if pp['number'] == current_num)
    is_last = speaker_idx == len(tied) - 1

    if phase == "idle":
        if is_last:
            st.markdown(f'<div style="background:#2d1a4e;color:#fff;padding:12px 16px;border-radius:8px;font-size:18px;font-weight:bold;margin:8px 0;">🔒 Последний: {p_num(current_p)} {p_name(current_p)}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:#2d1a4e;color:#fff;padding:12px 16px;border-radius:8px;font-size:18px;font-weight:bold;margin:8px 0;">🗣️ 30 сек: {p_num(current_p)} {p_name(current_p)}</div>', unsafe_allow_html=True)
    else:
        st.info(f"🗣️ Говорит: **{p_num(current_p)} {p_name(current_p)}**")

    col_reset, col_timer, col_pause = st.columns([1, 3, 1])
    with col_reset:
        if phase == "speaking":
            if st.button("🔄", key="cat_btn_reset", use_container_width=True):
                st.session_state.cat_timer_start = time.time()
                st.session_state.cat_timer_duration = 30
                st.session_state.cat_timer_paused = False; st.rerun()
    with col_pause:
        if phase == "speaking":
            if st.session_state.cat_timer_paused:
                if st.button("▶️", key="cat_btn_unpause", use_container_width=True):
                    st.session_state.cat_timer_paused = False
                    st.session_state.cat_timer_start = time.time()
                    st.session_state.cat_timer_duration = st.session_state.cat_timer_paused_remaining; st.rerun()
            else:
                if st.button("⏸️", key="cat_btn_pause", use_container_width=True):
                    st.session_state.cat_timer_paused = True
                    st.session_state.cat_timer_paused_remaining = _get_cat_remaining()
                    st.session_state.cat_timer_start = None; st.rerun()
    with col_timer:
        timer_display = st.empty()

    remaining = _get_cat_remaining()
    _draw_cat_timer(timer_display, remaining)

    if phase == "idle":
        if st.button(f"▶️ Старт {p_num(current_p)} {p_name(current_p)}", use_container_width=True, key="cat_main"):
            st.session_state.cat_phase = "speaking"
            st.session_state.cat_timer_start = time.time()
            st.session_state.cat_timer_duration = 30
            st.session_state.cat_timer_paused = False; st.rerun()
    else:
        if st.button("🙏 Спасибо", use_container_width=True, key="cat_main"):
            st.session_state.cat_timer_start = None
            st.session_state.cat_timer_paused = False
            st.session_state.cat_phase = "idle"
            st.session_state.cat_speaker_idx += 1; st.rerun()

    live_zone = st.empty()
    _render_cat_bars_live(live_zone, players, tied, prev_voters, speaker_idx)

    if phase == "speaking" and not st.session_state.cat_timer_paused and st.session_state.cat_timer_start:
        _run_cat_timer_loop(timer_display, live_zone, players, tied, prev_voters, speaker_idx)


def _get_cat_remaining():
    if st.session_state.get("cat_timer_paused"):
        return st.session_state.get("cat_timer_paused_remaining", 30)
    if st.session_state.get("cat_timer_start") is None:
        return st.session_state.get("cat_timer_duration", 30)
    elapsed = time.time() - st.session_state.cat_timer_start
    return max(0, st.session_state.cat_timer_duration - int(elapsed))


def _draw_cat_timer(ph, sec):
    total = st.session_state.get("cat_timer_duration", 30)
    progress = min(100, int(((total - sec) / max(total, 1)) * 100))
    color = "white" if sec > 10 else "red"
    ph.markdown(f'''
    <div style="text-align:center;">
        <p style="font-size:72px;font-weight:bold;margin:0;color:{color};line-height:1;">{sec}</p>
        <div style="background:#333;border-radius:6px;height:8px;margin:4px 20px;">
            <div style="background:#4CAF50;width:{progress}%;height:100%;border-radius:6px;"></div>
        </div>
    </div>''', unsafe_allow_html=True)


def _render_cat_bars(players, tied, prev_voters, speaker_idx):
    html = _build_cat_bars_html(players, tied, prev_voters, speaker_idx)
    st.markdown(html, unsafe_allow_html=True)


def _render_cat_bars_live(container, players, tied, prev_voters, speaker_idx):
    html = _build_cat_bars_html(players, tied, prev_voters, speaker_idx)
    container.markdown(html, unsafe_allow_html=True)


def _build_cat_bars_html(players, tied, prev_voters, speaker_idx):
    phase = st.session_state.get("cat_phase", "idle")
    html_parts = []
    for i, num in enumerate(tied):
        p = next(pp for pp in players if pp['number'] == num)
        voters_for = prev_voters.get(num, [])
        voter_tags = []
        for v_num in sorted(voters_for):
            vp = next((pp for pp in players if pp['number'] == v_num), None)
            if vp: voter_tags.append(p_num(vp))
        voters_str = ", ".join(voter_tags) if voter_tags else ""
        votes_info = f" ({len(voters_for)} гол: {voters_str})" if voters_str else f" ({len(voters_for)} гол)"

        if i < speaker_idx:
            progress = 100; bg = "#1a2e1a"; bar_color = "rgba(76,175,80,0.2)"; prefix = ""
        elif i == speaker_idx:
            if phase == "speaking" and st.session_state.get("cat_timer_start"):
                elapsed = time.time() - st.session_state.cat_timer_start
                total = st.session_state.get("cat_timer_duration", 30)
                progress = min(100, int((elapsed / max(total, 1)) * 100))
            elif phase == "speaking" and st.session_state.get("cat_timer_paused"):
                rem = st.session_state.get("cat_timer_paused_remaining", 30)
                progress = min(100, int(((30 - rem) / 30) * 100))
            else:
                progress = 0
            bg = "#1a3a1a"; bar_color = "rgba(76,175,80,0.5)"; prefix = "▶️ "
        else:
            progress = 0; bg = "#1a1a3d"; bar_color = "transparent"; prefix = ""

        html_parts.append(
            f'<div style="height:48px;display:flex;align-items:center;padding:4px 12px;'
            f'margin:3px 0;border-radius:6px;font-size:15px;font-weight:bold;'
            f'position:relative;overflow:hidden;background:{bg};color:white;">'
            f'<div style="position:absolute;left:0;top:0;bottom:0;width:{progress}%;'
            f'background:{bar_color};border-radius:6px;z-index:0;"></div>'
            f'<div style="position:relative;z-index:1;width:100%;">'
            f'<span>{prefix}{p_bar_text(p)}</span>'
            f'<span style="float:right;font-size:12px;color:#aaa;">{votes_info}</span>'
            f'</div></div>'
        )
    return "\n".join(html_parts)


def _run_cat_timer_loop(timer_display, live_zone, players, tied, prev_voters, speaker_idx):
    start = st.session_state.cat_timer_start
    total = st.session_state.cat_timer_duration
    if not start: return
    while True:
        elapsed = time.time() - start
        sec = max(0, total - int(elapsed))
        _draw_cat_timer(timer_display, sec)
        html = _build_cat_bars_html(players, tied, prev_voters, speaker_idx)
        live_zone.markdown(html, unsafe_allow_html=True)
        if sec <= 10 and sec > 0: play_sound_html(METRONOME_SOUND)
        if sec == 0: play_sound_html(WHISTLE_SOUND)
        time.sleep(2)
        break



def _reset_cat():
    st.session_state.cat_speaker_idx = 0
    st.session_state.cat_phase = "idle"
    st.session_state.cat_timer_start = None
    st.session_state.cat_timer_duration = 30
    st.session_state.cat_timer_paused = False
    st.session_state.cat_timer_paused_remaining = 30



def _get_lw_remaining():
    if st.session_state.get("lw_timer_start") is None:
        return st.session_state.get("lw_timer_duration", 30)
    elapsed = time.time() - st.session_state.lw_timer_start
    return max(0, st.session_state.lw_timer_duration - int(elapsed))

def _run_lw_timer(timer_ph):
    start = st.session_state.lw_timer_start
    total = st.session_state.lw_timer_duration
    if start is None: return
    while True:
        elapsed = time.time() - start
        sec = max(0, total - int(elapsed))
        progress = min(100, int(((total - sec) / max(total, 1)) * 100))
        color = "white" if sec > 10 else "red"
        timer_ph.markdown(f'''
            <div style="text-align:center;">
                <p style="font-size:72px;font-weight:bold;margin:0;color:{color};line-height:1;">{sec}</p>
                <div style="background:#333;border-radius:6px;height:8px;margin:4px 40px;">
                    <div style="background:#4CAF50;width:{progress}%;height:100%;border-radius:6px;"></div>
                </div>
            </div>''', unsafe_allow_html=True)
        if sec <= 10 and sec > 0: play_sound_html(METRONOME_SOUND)
        if sec == 0: play_sound_html(WHISTLE_SOUND)
        time.sleep(2)
        break


def _finish_last_word(day):
    st.session_state.lw_timer_start = None
    st.session_state.lw_timer_duration = 30
    st.session_state.lw_phase = "idle"
    st.session_state.lw_current_idx = 0
    st.session_state.lw_done_list = []
    if st.session_state.get('best_move_targets'):
        st.session_state.game_log.append(
            f"Лучший ход: {st.session_state.best_move_targets}"
        )
    go("game_night")



def screen_game_last_word():
    game = st.session_state.game
    players = game['players']
    day = st.session_state.day_number
    eliminated = st.session_state.get('eliminated_today', [])

    if "lw_current_idx" not in st.session_state: st.session_state.lw_current_idx = 0
    if "lw_timer_start" not in st.session_state: st.session_state.lw_timer_start = None
    if "lw_timer_duration" not in st.session_state: st.session_state.lw_timer_duration = 30
    if "lw_phase" not in st.session_state: st.session_state.lw_phase = "idle"
    if "lw_done_list" not in st.session_state: st.session_state.lw_done_list = []

    st.markdown(
        '<div style="text-align:center;padding:20px 0 5px;">'
        '<p style="font-size:80px;margin:0;">💀</p>'
        '<p style="font-size:22px;font-weight:bold;color:#fff;">Последнее слово</p></div>',
        unsafe_allow_html=True
    )

    for i, num in enumerate(eliminated):
        p = next(pp for pp in players if pp['number'] == num)
        is_current = i == st.session_state.lw_current_idx
        is_done = num in st.session_state.lw_done_list
        if is_done:
            st.markdown(f'<div style="text-align:center;padding:6px;opacity:0.5;"><span style="font-size:20px;color:#888;">✅ {p_num(p)} {p_name(p)}</span></div>', unsafe_allow_html=True)
        elif is_current:
            st.markdown(f'<div style="text-align:center;padding:6px;"><span style="font-size:20px;color:#ff8844;font-weight:bold;">▶️ {p_num(p)} {p_name(p)}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:center;padding:6px;"><span style="font-size:20px;color:#666;">{p_num(p)} {p_name(p)}</span></div>', unsafe_allow_html=True)

    st.markdown("---")

    current_idx = st.session_state.lw_current_idx
    all_said = current_idx >= len(eliminated)

    if not all_said:
        current_num = eliminated[current_idx]
        current_p = next(pp for pp in players if pp['number'] == current_num)
        phase = st.session_state.lw_phase

        st.markdown(
            f'<div style="text-align:center;padding:20px 0;">'
            f'<p style="font-size:120px;font-weight:bold;margin:0;color:#cc0000;line-height:1;">{p_num(current_p)}</p>'
            f'<p style="font-size:32px;color:#ccc;margin:4px 0;">{p_name(current_p)}</p></div>',
            unsafe_allow_html=True
        )

        col_reset, col_timer, col_pause = st.columns([1, 3, 1])
        with col_reset:
            if phase == "speaking":
                if st.button("🔄", key="lw_reset", use_container_width=True):
                    st.session_state.lw_timer_start = time.time()
                    st.session_state.lw_timer_duration = 30; st.rerun()
        with col_pause:
            pass
        with col_timer:
            timer_ph = st.empty()

        remaining = _get_lw_remaining()
        total = st.session_state.lw_timer_duration
        progress = min(100, int(((total - remaining) / max(total, 1)) * 100))
        color = "white" if remaining > 10 else "red"
        timer_ph.markdown(f'''
        <div style="text-align:center;">
            <p style="font-size:72px;font-weight:bold;margin:0;color:{color};line-height:1;">{remaining}</p>
            <div style="background:#333;border-radius:6px;height:8px;margin:4px 40px;">
                <div style="background:#4CAF50;width:{progress}%;height:100%;border-radius:6px;"></div>
            </div>
        </div>''', unsafe_allow_html=True)

        if phase == "idle":
            if st.button(f"▶️ Старт {p_num(current_p)} {p_name(current_p)}", use_container_width=True, key="lw_start"):
                st.session_state.lw_phase = "speaking"
                st.session_state.lw_timer_start = time.time()
                st.session_state.lw_timer_duration = 30;
                st.rerun()
        elif phase == "speaking":
            if st.button("🙏 Спасибо", use_container_width=True, key="lw_thanks"):
                st.session_state.lw_done_list.append(current_num)
                st.session_state.lw_current_idx += 1
                st.session_state.lw_phase = "idle"
                st.session_state.lw_timer_start = None;
                st.rerun()

        if phase == "speaking" and st.session_state.lw_timer_start is not None:
            _run_lw_timer(timer_ph)

    if all_said or st.session_state.lw_done_list:
        st.markdown("---")

        if all_said:
            st.success("✅ Все сказали последнее слово!")

        if day == 1:
            st.markdown("---")
            st.markdown("### 🎯 Лучший ход (до 3 игроков)")
            if "best_move_targets" not in st.session_state:
                st.session_state.best_move_targets = []

            sorted_all = sorted(players, key=lambda p: p['number'])
            n = len(sorted_all)
            rows = math.ceil(n / GRID_COLS)
            for r in range(rows):
                cols = st.columns(GRID_COLS)
                for c in range(GRID_COLS):
                    idx = r * GRID_COLS + c
                    if idx >= n: break
                    ap = sorted_all[idx]
                    with cols[c]:
                        is_dead = ap['status'] == 'dead'
                        is_sel = ap['number'] in st.session_state.best_move_targets
                        label = f"🎯{p_num(ap)}" if is_sel else p_num(ap)
                        if st.button(label, key=f"bm_{ap['number']}", disabled=is_dead, use_container_width=True):
                            if is_sel:
                                st.session_state.best_move_targets.remove(ap['number'])
                            elif len(st.session_state.best_move_targets) < 3:
                                st.session_state.best_move_targets.append(ap['number'])
                            st.rerun()

            if st.session_state.best_move_targets:
                names = [
                    f"{p_num(next(x for x in players if x['number'] == bn))} {p_name(next(x for x in players if x['number'] == bn))}"
                    for bn in st.session_state.best_move_targets]
                st.success(f"🎯 {', '.join(names)}")

        if all_said:
            st.markdown("---")
            if st.button("🌙 Далее → Ночь", use_container_width=True, key="lw_to_night"):
                _finish_last_word(day);
                st.rerun()

