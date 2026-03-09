import streamlit as st
import math
import time
from shared import (
    go, get_alive, get_speaker_order,
    play_sound_html, METRONOME_SOUND, WHISTLE_SOUND, sync_music,
    run_timer_no_block, role_emoji, p_num, p_name, p_bar_text
)

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

    st.header(f"☀️ День {day}")

    if all_done:
        st.success("✅ Все высказались!")
        live_zone = st.empty()
        _draw_player_bars(live_zone, players, order, speaker_idx)
        st.markdown("---")
        if st.session_state.nominees:
            st.markdown("**Выставлены:**")
            _render_nominees_summary(players)
        _render_bottom_buttons(day)
        st.markdown("---")
        _render_fouls(players, day)
        st.markdown("---")
        st.checkbox("👁️ Показывать роли", value=st.session_state.get("show_roles", False),
                    key="show_roles_cb", on_change=_toggle_roles)
        return

    current = order[speaker_idx]
    is_last = speaker_idx == len(order) - 1

    if current['fouls'] >= 4:
        st.error(f"🚫 {p_num(current)} {p_name(current)} — 4 фола!")
        if st.button("⏭️ Пропустить", use_container_width=True): _next_speaker(); st.rerun()
        _render_static_players(players, order, speaker_idx)
        return

    if phase == "idle":
        if speaker_idx == 0:
            st.markdown(f'<div style="background:#2d1a4e;color:#fff;padding:12px 16px;border-radius:8px;font-size:18px;font-weight:bold;margin:8px 0;">📢 Открывает стол: {p_num(current)} {p_name(current)}</div>', unsafe_allow_html=True)
        elif is_last:
            st.markdown(f'<div style="background:#2d1a4e;color:#fff;padding:12px 16px;border-radius:8px;font-size:18px;font-weight:bold;margin:8px 0;">🔒 Закрывает стол: {p_num(current)} {p_name(current)}</div>', unsafe_allow_html=True)
        else:
            st.info(f"🗣️ Минута для: **{p_num(current)} {p_name(current)}**")
    else:
        st.info(f"🗣️ Говорит: **{p_num(current)} {p_name(current)}**")

    col_reset, col_timer, col_pause = st.columns([1, 3, 1])
    with col_reset:
        if phase == "speaking":
            if st.button("🔄", key="btn_reset", use_container_width=True):
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_duration = 60
                st.session_state.timer_paused = False; st.rerun()
    with col_pause:
        if phase == "speaking":
            if st.session_state.timer_paused:
                if st.button("▶️", key="btn_unpause", use_container_width=True):
                    st.session_state.timer_paused = False
                    st.session_state.timer_start_time = time.time()
                    st.session_state.timer_duration = st.session_state.timer_paused_remaining; st.rerun()
            else:
                if st.button("⏸️", key="btn_pause", use_container_width=True):
                    st.session_state.timer_paused = True
                    st.session_state.timer_paused_remaining = _get_remaining()
                    st.session_state.timer_start_time = None; st.rerun()
    with col_timer:
        timer_display = st.empty()
    remaining = _get_remaining()
    _draw_timer_only(timer_display, remaining)

    if phase == "idle":
        if st.button(f"▶️ Старт {p_num(current)} {p_name(current)}", use_container_width=True, key="main_btn"):
            st.session_state.day_phase = "speaking"
            st.session_state.timer_start_time = time.time()
            st.session_state.timer_duration = 60
            st.session_state.timer_paused = False; st.rerun()
    else:
        if st.button("🙏 Спасибо", use_container_width=True, key="main_btn"):
            st.session_state.timer_start_time = None
            st.session_state.timer_paused = False
            st.session_state.day_phase = "idle"
            _next_speaker(); st.rerun()

    live_zone = st.empty()
    _draw_player_bars(live_zone, players, order, speaker_idx)

    def _render_static_players(all_players, order, speaker_idx):
        """Статичная отрисовка (без live_zone)"""
        _draw_player_bars(st.empty(), all_players, order, speaker_idx)

    st.markdown("---")
    _render_nominations(players, order, speaker_idx, day)
    st.markdown("---")
    _render_fouls(players, day)
    st.markdown("---")
    st.checkbox("👁️ Показывать роли", value=st.session_state.get("show_roles", False),
                key="show_roles_cb", on_change=_toggle_roles)

    if phase == "speaking" and not st.session_state.timer_paused and st.session_state.timer_start_time:
        _run_live_loop(timer_display, live_zone, players, order, speaker_idx)


def _render_nominees_summary(all_players):
    grouped = {}
    for by_n, who_n in st.session_state.nominees.items():
        grouped.setdefault(who_n, []).append(by_n)
    for who_n, by_list in grouped.items():
        who_p = next((x for x in all_players if x['number'] == who_n), None)
        by_strs = []
        for bn in by_list:
            bp = next((x for x in all_players if x['number'] == bn), None)
            by_strs.append(p_num(bp) if bp else f"#{bn}")
        who_str = p_num(who_p) if who_p else f"#{who_n}"
        st.write(f"**{who_str}** — выставлен: {', '.join(by_strs)}")


def _get_remaining():
    if st.session_state.get("timer_paused"):
        return st.session_state.get("timer_paused_remaining", 60)
    if st.session_state.get("timer_start_time") is None:
        return st.session_state.get("timer_duration", 60)
    elapsed = time.time() - st.session_state.timer_start_time
    return max(0, st.session_state.timer_duration - int(elapsed))


def _draw_timer_only(ph, sec):
    color = "white" if sec > 10 else "red"
    ph.markdown(f'<p style="font-size:80px;text-align:center;font-weight:bold;margin:0;padding:0;color:{color};line-height:1;">{sec}</p>', unsafe_allow_html=True)


def _draw_player_bars(container, all_players, order, speaker_idx):
    phase = st.session_state.get("day_phase", "idle")
    sorted_all = sorted(all_players, key=lambda p: p['number'])
    order_nums = [p['number'] for p in order]
    html = []
    for p in sorted_all:
        foul_dots = "❗" * p['fouls'] if p['fouls'] > 0 else ""
        if p['status'] == 'dead':
            html.append(f'<div style="height:32px;display:flex;align-items:center;padding:2px 12px;margin:2px 0;border-radius:6px;background:#111;color:#555;font-size:14px;text-decoration:line-through;">{p_bar_text(p)} 💀<span style="margin-left:auto;">{foul_dots}</span></div>')
            continue

        pos = order_nums.index(p['number']) if p['number'] in order_nums else 999

        if pos < speaker_idx:
            progress = 100; bg = "#1a2e1a"; bar_color = "rgba(76,175,80,0.2)"; prefix = ""
        elif pos == speaker_idx:
            if phase == "speaking" and st.session_state.timer_start_time:
                elapsed = time.time() - st.session_state.timer_start_time
                total = st.session_state.timer_duration
                progress = min(100, int((elapsed / max(total, 1)) * 100))
            elif phase == "speaking" and st.session_state.get("timer_paused"):
                rem = st.session_state.get("timer_paused_remaining", 60)
                progress = min(100, int(((60 - rem) / 60) * 100))
            else:
                progress = 0
            bg = "#1a3a1a"; bar_color = "rgba(76,175,80,0.5)"; prefix = ""
        else:
            progress = 0; bg = "#1a1a3d"; bar_color = "transparent"; prefix = ""

        html.append(f'''<div style="height:40px;display:flex;align-items:center;padding:4px 12px;margin:2px 0;border-radius:6px;font-size:16px;font-weight:bold;position:relative;overflow:hidden;background:{bg};color:white;">
            <div style="position:absolute;left:0;top:0;bottom:0;width:{progress}%;background:{bar_color};border-radius:6px;z-index:0;"></div>
            <div style="position:relative;z-index:1;width:100%;display:flex;justify-content:space-between;">
                <span>{prefix}{p_bar_text(p)}</span><span>{foul_dots}</span>
            </div></div>''')
    container.markdown("\n".join(html), unsafe_allow_html=True)


def _run_live_loop(timer_display, live_zone, all_players, order, speaker_idx):
    start = st.session_state.timer_start_time
    total = st.session_state.timer_duration
    if not start: return
    while True:
        elapsed = time.time() - start
        sec = max(0, total - int(elapsed))
        _draw_timer_only(timer_display, sec)
        _draw_player_bars(live_zone, all_players, order, speaker_idx)
        if sec <= 10 and sec > 0: play_sound_html(METRONOME_SOUND)
        if sec == 0: play_sound_html(WHISTLE_SOUND); break
        time.sleep(1)


def _next_speaker():
    st.session_state.current_speaker += 1
    st.session_state.day_phase = "idle"
    st.session_state.timer_start_time = None
    st.session_state.timer_duration = 60
    st.session_state.timer_paused = False
    st.session_state.timer_paused_remaining = 60



def _render_fouls(all_players, day):
    st.markdown("### ⚠️ Фолы")
    sorted_all = sorted(all_players, key=lambda p: p['number'])
    n = len(sorted_all)
    rows = math.ceil(n / GRID_COLS)
    for r in range(rows):
        cols = st.columns(GRID_COLS)
        for c in range(GRID_COLS):
            idx = r * GRID_COLS + c
            if idx >= n: break
            p = sorted_all[idx]
            with cols[c]:
                is_dead = p['status'] == 'dead'
                at_max = p['fouls'] >= 4
                foul_dots = "❗" * p['fouls'] if p['fouls'] > 0 else ""
                if is_dead:
                    label = f"💀{p_num(p)}"
                elif at_max:
                    label = f"🚫{p_num(p)}"
                else:
                    label = f"{p_num(p)}{foul_dots}"
                if st.button(label, key=f"foul_{day}_{p['number']}", disabled=at_max, use_container_width=True):
                    if not is_dead and p['fouls'] < 4:
                        p['fouls'] += 1
                        if p['fouls'] >= 4: st.toast(f"🚫 {p_num(p)} — 4 фола!")
                    st.rerun()


def _render_nominations(all_players, order, speaker_idx, day):
    all_done = speaker_idx >= len(order)
    if not all_done:
        st.markdown("### 🗳️ Выставление на голосование")
        if speaker_idx < len(order):
            current = order[speaker_idx]
            st.caption(f"Выставляет: {p_num(current)} {p_name(current)}")

        sorted_all = sorted(all_players, key=lambda p: p['number'])
        n = len(sorted_all)
        rows = math.ceil(n / GRID_COLS)
        for r in range(rows):
            cols = st.columns(GRID_COLS)
            for c in range(GRID_COLS):
                idx = r * GRID_COLS + c
                if idx >= n: break
                p = sorted_all[idx]
                with cols[c]:
                    is_dead = p['status'] == 'dead'
                    nominated_nums = list(st.session_state.nominees.values())
                    is_nom = p['number'] in nominated_nums
                    if is_dead:
                        st.button(p_num(p), key=f"nom_{day}_{p['number']}", disabled=True, use_container_width=True)
                    else:
                        label = f"{'🗳️' if is_nom else ''}{p_num(p)}"
                        if st.button(label, key=f"nom_{day}_{p['number']}", use_container_width=True):
                            if speaker_idx < len(order):
                                by_num = order[speaker_idx]['number']
                                st.session_state.nominees[by_num] = p['number']
                                st.session_state.game_log.append(f"День {day}: #{by_num} → #{p['number']}")
                            st.rerun()

        if st.session_state.nominees:
            st.markdown("**Выставлены:**")
            _render_nominees_summary(all_players)


def _render_bottom_buttons(day):
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("❌ Никого → Ночь", use_container_width=True, key="btn_no_vote"):
            st.session_state.game_log.append(f"День {day}: никого")
            _reset_day(); go("game_night"); st.rerun()
    with c2:
        if st.session_state.nominees:
            if st.button("🗳️ Голосование", use_container_width=True, key="btn_vote"):
                st.session_state.vote_voters = {}; st.session_state.vote_step = 0
                _reset_day(); go("game_vote"); st.rerun()


def _reset_day():
    st.session_state.day_phase = "idle"
    st.session_state.timer_start_time = None
    st.session_state.timer_duration = 60
    st.session_state.timer_paused = False
    st.session_state.timer_paused_remaining = 60


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
        if sec == 0: play_sound_html(WHISTLE_SOUND); break
        time.sleep(1)


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
        if sec == 0: play_sound_html(WHISTLE_SOUND); break
        time.sleep(1)

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

