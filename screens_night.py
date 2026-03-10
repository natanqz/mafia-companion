import streamlit as st
import streamlit.components.v1 as components
import json
import math
import time
from datetime import datetime
from shared import (
    load_db, save_db, get_player, go, get_alive,
    sync_music, role_emoji,
    play_timer_sound, stop_timer_sound,
    p_num, p_name, p_bar_text
)

GRID_COLS = 5


def screen_game_night():
    sync_music()
    game = st.session_state.game
    players = game['players']
    day = st.session_state.day_number



    st.markdown(
        f'<div style="text-align:center;padding:20px 0 5px;">'
        f'<p style="font-size:80px;margin:0;">🌙</p>'
        f'<p style="font-size:22px;font-weight:bold;color:#fff;">Ночь {day}</p></div>',
        unsafe_allow_html=True
    )
    sync_music()
    st.markdown("---")

    if "night_kill" not in st.session_state: st.session_state.night_kill = None
    if "don_check" not in st.session_state: st.session_state.don_check = None
    if "sheriff_check" not in st.session_state: st.session_state.sheriff_check = None
    if "night_tab" not in st.session_state: st.session_state.night_tab = None

    sorted_all = sorted(players, key=lambda p: p['number'])
    n = len(sorted_all)

    current_tab = st.session_state.night_tab

    # === 3 кнопки-вкладки ===
    c1, c2, c3 = st.columns(3)
    with c1:
        sheriff_label = "⭐ Шериф" + (" ✅" if st.session_state.sheriff_check else "")
        if current_tab == "sheriff":
            sheriff_label = "🔽 " + sheriff_label
        if st.button(sheriff_label, key="tab_sheriff", use_container_width=True):
            st.session_state.night_tab = None if current_tab == "sheriff" else "sheriff"
            st.rerun()
    with c2:
        don_label = "🎩 Дон" + (" ✅" if st.session_state.don_check else "")
        if current_tab == "don":
            don_label = "🔽 " + don_label
        if st.button(don_label, key="tab_don", use_container_width=True):
            st.session_state.night_tab = None if current_tab == "don" else "don"
            st.rerun()
    with c3:
        mafia_label = "🔫 Мафия" + (" ✅" if st.session_state.night_kill else "")
        if current_tab == "mafia":
            mafia_label = "🔽 " + mafia_label
        if st.button(mafia_label, key="tab_mafia", use_container_width=True):
            st.session_state.night_tab = None if current_tab == "mafia" else "mafia"
            st.rerun()

    st.markdown("---")

    # === Содержимое открытой вкладки ===
    if current_tab == "sheriff":
        st.markdown("### ⭐ Шериф проверяет")
        _night_grid(sorted_all, n, "sheriff_check", "sc", skip_role="Шериф", emoji_sel="⭐")

        if st.session_state.sheriff_check:
            checked = next((p for p in players if p['number'] == st.session_state.sheriff_check), None)
            if checked:
                is_mafia = checked['role'] in ['Мафия', 'Дон']
                if is_mafia:
                    st.markdown(
                        f'<div style="text-align:center;padding:20px;background:#111;'
                        f'border-radius:12px;margin:10px 0;border:2px solid #333;">'
                        f'<p style="font-size:64px;margin:0;">👎</p>'
                        f'<p style="font-size:36px;font-weight:bold;color:#ff4444;">'
                        f'#{checked["number"]} {checked["nickname"]}</p>'
                        f'<p style="font-size:28px;color:#66ff66;">✅ МАФИЯ!</p></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="text-align:center;padding:20px;background:#4a1a1a;'
                        f'border-radius:12px;margin:10px 0;border:2px solid #662222;">'
                        f'<p style="font-size:64px;margin:0;">👍</p>'
                        f'<p style="font-size:36px;font-weight:bold;color:#ccc;">'
                        f'#{checked["number"]} {checked["nickname"]}</p>'
                        f'<p style="font-size:28px;color:#ff6666;">❌ Мирный</p></div>',
                        unsafe_allow_html=True
                    )

    elif current_tab == "don":
        st.markdown("### 🎩 Дон проверяет")
        _night_grid(sorted_all, n, "don_check", "dc", skip_role="Дон", emoji_sel="🎩")

        if st.session_state.don_check:
            checked = next((p for p in players if p['number'] == st.session_state.don_check), None)
            if checked:
                is_sheriff = checked['role'] == 'Шериф'
                if is_sheriff:
                    st.markdown(
                        f'<div style="text-align:center;padding:20px;background:#4a1a1a;'
                        f'border-radius:12px;margin:10px 0;border:2px solid #662222;">'
                        f'<p style="font-size:64px;margin:0;">👌</p>'
                        f'<p style="font-size:36px;font-weight:bold;color:#ff8888;">'
                        f'#{checked["number"]} {checked["nickname"]}</p>'
                        f'<p style="font-size:28px;color:#66ff66;">✅ ШЕРИФ!</p></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="text-align:center;padding:20px;background:#4a1a1a;'
                        f'border-radius:12px;margin:10px 0;border:2px solid #662222;">'
                        f'<p style="font-size:64px;margin:0;">👤</p>'
                        f'<p style="font-size:36px;font-weight:bold;color:#ccc;">'
                        f'#{checked["number"]} {checked["nickname"]}</p>'
                        f'<p style="font-size:28px;color:#ff6666;">❌ Не шериф</p></div>',
                        unsafe_allow_html=True
                    )

    elif current_tab == "mafia":
        st.markdown("### 🔫 Мафия стреляет")

        # Заметка ведущего
        mafia_notes = st.session_state.get('mafia_notes', '')
        if mafia_notes:
            st.markdown(
                f'<div style="background:#2a1a1a;padding:10px 16px;border-radius:8px;'
                f'margin:8px 0;border-left:4px solid #cc0000;">'
                f'<p style="font-size:12px;color:#888;margin:0;">📝 Заметка:</p>'
                f'<p style="font-size:16px;color:#fff;margin:4px 0;white-space:pre-wrap;">'
                f'{mafia_notes}</p></div>',
                unsafe_allow_html=True
            )

        _night_grid(sorted_all, n, "night_kill", "nk", skip_role=None, emoji_sel="🔫")

        if st.session_state.night_kill:
            target = next((p for p in players if p['number'] == st.session_state.night_kill), None)
            if target:
                st.markdown(
                    f'<div style="text-align:center;padding:10px;">'
                    f'<p style="font-size:28px;color:#ff4444;font-weight:bold;">'
                    f'🔫 #{target["number"]} {target["nickname"]}</p></div>',
                    unsafe_allow_html=True
                )

    st.markdown("---")


    # Кнопка утро
    if st.button("🌅 Наступает утро", use_container_width=True, key="to_morning"):
        kill = st.session_state.night_kill
        if kill:
            p = next(pp for pp in players if pp['number'] == kill)
            p['status'] = 'dead'
            st.session_state.game_log.append(f"Ночь {day}: Убит #{kill} ({p['nickname']})")
        else:
            st.session_state.game_log.append(f"Ночь {day}: Промах")
        if st.session_state.don_check:
            st.session_state.game_log.append(f"Ночь {day}: Дон проверил #{st.session_state.don_check}")
        if st.session_state.sheriff_check:
            st.session_state.game_log.append(f"Ночь {day}: Шериф проверил #{st.session_state.sheriff_check}")
        st.session_state.night_kill_result = kill
        st.session_state.night_kill = None
        st.session_state.don_check = None
        st.session_state.sheriff_check = None
        st.session_state.night_tab = None
        go("game_morning"); st.rerun()

def _night_grid(sorted_all, n, state_key, key_prefix, skip_role=None, emoji_sel="🔫"):
    """Сетка для ночных действий"""
    rows = math.ceil(n / GRID_COLS)
    for r in range(rows):
        cols = st.columns(GRID_COLS)
        for c in range(GRID_COLS):
            idx = r * GRID_COLS + c
            if idx >= n: break
            p = sorted_all[idx]
            with cols[c]:
                is_dead = p['status'] == 'dead'
                is_skip = skip_role and p['role'] == skip_role
                is_sel = getattr(st.session_state, state_key, None) == p['number']

                if is_dead:
                    label = f"#{p['number']}"
                    st.button(label, key=f"{key_prefix}_{p['number']}", disabled=True, use_container_width=True)
                elif is_skip:
                    label = f"#{p['number']}"
                    st.button(label, key=f"{key_prefix}_{p['number']}", disabled=True, use_container_width=True)
                else:
                    label = f"{emoji_sel}#{p['number']}" if is_sel else f"#{p['number']}"
                    if st.button(label, key=f"{key_prefix}_{p['number']}", use_container_width=True):
                        if is_sel:
                            st.session_state[state_key] = None
                        else:
                            st.session_state[state_key] = p['number']
                        st.rerun()


def screen_game_morning():
    sync_music()
    game = st.session_state.game
    players = game['players']
    day = st.session_state.day_number
    killed = st.session_state.get('night_kill_result')

    if "morning_timer_start" not in st.session_state: st.session_state.morning_timer_start = None
    if "morning_timer_duration" not in st.session_state: st.session_state.morning_timer_duration = 30
    if "morning_phase" not in st.session_state: st.session_state.morning_phase = "idle"

    st.markdown(
        f'<div style="text-align:center;padding:20px 0 5px;">'
        f'<p style="font-size:80px;margin:0;">🌅</p>'
        f'<p style="font-size:22px;font-weight:bold;color:#fff;">Результат ночи {day}</p></div>',
        unsafe_allow_html=True
    )

    # Проверка победы
    alive_players = get_alive()
    mafia_alive = len([p for p in alive_players if p['role'] in ['Мафия', 'Дон']])
    civil_alive = len([p for p in alive_players if p['role'] not in ['Мафия', 'Дон']])
    if mafia_alive == 0:
        st.session_state.game_winner = "мирные"; go("game_end"); st.rerun()
    elif mafia_alive >= civil_alive:
        st.session_state.game_winner = "мафия"; go("game_end"); st.rerun()

    if killed:
        p = next(pp for pp in players if pp['number'] == killed)
        st.markdown(
            f'<div style="text-align:center;padding:30px 0;">'
            f'<p style="font-size:120px;font-weight:bold;margin:0;color:#cc0000;line-height:1;">#{p["number"]}</p>'
            f'<p style="font-size:32px;color:#ccc;margin:4px 0;">{p["nickname"]}</p></div>',
            unsafe_allow_html=True
        )

        # Таймер + прогресс бар
        remaining = _get_morning_remaining()
        total = st.session_state.morning_timer_duration
        progress = min(100, int(((total - remaining) / max(total, 1)) * 100))
        color = "white" if remaining > 10 else "red"

        timer_ph = st.empty()
        timer_ph.markdown(f'''
        <div style="text-align:center;">
            <p style="font-size:72px;font-weight:bold;margin:0;color:{color};line-height:1;">{remaining}</p>
            <div style="background:#333;border-radius:6px;height:8px;margin:4px 40px;">
                <div style="background:#4CAF50;width:{progress}%;height:100%;border-radius:6px;"></div>
            </div>
        </div>''', unsafe_allow_html=True)

        phase = st.session_state.morning_phase

        if phase == "idle":
            # Кнопки: Старт | День
            c1, c2 = st.columns(2)
            with c1:
                if st.button("▶️ Старт 30 сек", key="mt_start", use_container_width=True):
                    st.session_state.morning_timer_start = time.time()
                    st.session_state.morning_timer_duration = 30
                    st.session_state.morning_phase = "speaking"
                    play_timer_sound(30)
                    st.rerun()
            with c2:
                if st.button(f"☀️ День {day + 1}", key="mt_skip", use_container_width=True):
                    _go_next_day(day); st.rerun()


        elif phase == "speaking":
            # Кнопка: Спасибо
            if st.button("🙏 Спасибо", key="mt_thanks", use_container_width=True):
                st.session_state.morning_timer_start = None
                st.session_state.morning_phase = "done"
                st.rerun()

        elif phase == "done":
            # Кнопка: День
            if st.button(f"☀️ День {day + 1}", use_container_width=True, key="mt_next"):
                _go_next_day(day); st.rerun()

        # Живой таймер
        if phase == "speaking" and st.session_state.morning_timer_start is not None:
            _run_morning_timer(timer_ph)

    else:
        st.markdown(
            '<div style="text-align:center;padding:30px 0;">'
            '<p style="font-size:80px;margin:0;">😌</p>'
            '<p style="font-size:24px;color:#ccc;">Никто не погиб!</p></div>',
            unsafe_allow_html=True
        )
        st.markdown("---")
        if st.button(f"☀️ День {day + 1}", use_container_width=True, key="no_kill_next"):
            _go_next_day(day); st.rerun()


def _get_morning_remaining():
    if st.session_state.get("morning_timer_start") is None:
        return st.session_state.get("morning_timer_duration", 30)
    elapsed = time.time() - st.session_state.morning_timer_start
    return max(0, st.session_state.morning_timer_duration - int(elapsed))


def _run_morning_timer(timer_ph):
    start = st.session_state.morning_timer_start
    total = st.session_state.morning_timer_duration
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

        time.sleep(2)
        break


def _go_next_day(day):
    st.session_state.morning_timer_start = None
    st.session_state.morning_timer_duration = 30
    st.session_state.morning_phase = "idle"
    st.session_state.day_number = day + 1
    st.session_state.current_speaker = 0
    st.session_state.nominees = {}
    st.session_state.day_phase = "idle"
    st.session_state.timer_start_time = None
    go("game_day")




def screen_game_end():
    game = st.session_state.game
    players = game['players']
    winner = st.session_state.get('game_winner', '???')

    if winner == "мафия":
        emoji = "🖤"; title = "Победа Мафии!"; color = "#cc0000"
    else:
        emoji = "❤️"; title = "Победа Мирных!"; color = "#4CAF50"

    st.markdown(
        f'<div style="text-align:center;padding:30px 0;">'
        f'<p style="font-size:100px;margin:0;">{emoji}</p>'
        f'<p style="font-size:28px;font-weight:bold;color:{color};">'
        f'{title}</p></div>',
        unsafe_allow_html=True
    )

    st.markdown("### Итоги:")
    sorted_all = sorted(players, key=lambda p: p['number'])
    for p in sorted_all:
        status = "💀" if p['status'] == 'dead' else "✅"
        st.write(f"{status} {p_num(p)} {p_name(p)} | Фолов: {p['fouls']}")

    if st.session_state.game_log:
        with st.expander("📋 Хроника"):
            for ev in st.session_state.game_log: st.write(f"- {ev}")

    st.markdown("---")
    if st.button("💾 Сохранить и выйти", use_container_width=True):
        db = load_db()
        game_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mode": game['mode'], "winner": winner,
            "players": [{"number": p['number'], "nickname": p['nickname'],
                          "role": p['role'], "status": p['status'], "fouls": p['fouls']} for p in players],
            "log": st.session_state.game_log
        }
        db['games'].append(game_record); save_db(db)
        st.session_state.game = None; st.session_state.game_log = []
        go("main_menu"); st.rerun()


def screen_archive():
    db = load_db()
    st.markdown(
        '<div style="text-align:center;padding:20px 0 5px;">'
        '<p style="font-size:80px;margin:0;">📜</p>'
        '<p style="font-size:22px;font-weight:bold;color:#fff;">Архив игр</p></div>',
        unsafe_allow_html=True
    )
    if st.button("⬅️ Назад", use_container_width=True): go("main_menu"); st.rerun()
    if not db['games']: st.info("Пока нет игр"); return
    for g in reversed(db['games']):
        w_emoji = "🖤" if g.get('winner') == 'мафия' else "❤️"
        with st.expander(f"{g['mode']} | {g['date']} | {w_emoji} {g.get('winner', '---')}"):
            for p in g['players']:
                e = "💀" if p['status'] == 'dead' else "✅"
                st.write(f"{e} #{p['number']} {p['nickname']} — {role_emoji(p['role'])} {p['role']}")
            if g.get('log'):
                st.markdown("**Хроника:**")
                for ev in g['log']: st.write(f"- {ev}")


def screen_export_import():
    db = load_db()
    st.markdown(
        '<div style="text-align:center;padding:20px 0 5px;">'
        '<p style="font-size:80px;margin:0;">💾</p>'
        '<p style="font-size:22px;font-weight:bold;color:#fff;">Экспорт / Импорт</p></div>',
        unsafe_allow_html=True
    )
    if st.button("⬅️ Назад", use_container_width=True): go("main_menu"); st.rerun()
    st.download_button("📥 Скачать базу", data=json.dumps(db, indent=2, ensure_ascii=False),
                        file_name="mafia_db.json", use_container_width=True)
    st.markdown("---")
    upl = st.file_uploader("📤 Загрузить базу", type="json")
    if upl:
        try:
            new_db = json.load(upl); save_db(new_db); st.success("✅ Импортировано!")
        except Exception as e: st.error(f"Ошибка: {e}")