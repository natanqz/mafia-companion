import streamlit as st
import json
import os
import time
import base64
import requests
import streamlit.components.v1 as components


# ---- SETTINGS ----
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "db.json")
MUSIC_FOLDER = os.path.join(os.path.dirname(__file__), "music")
SOUNDS_FOLDER = os.path.join(os.path.dirname(__file__), "sounds")
METRONOME_SOUND = "metronome.mp3"
WHISTLE_SOUND = "whistle.mp3"
GIST_FILENAME = "mafia_db.json"
TIMER_60_SOUND = "timer_60.mp3"
TIMER_30_SOUND = "timer_30.mp3"


# ---- GIST DB ----
def _gist_headers():
    token = st.secrets.get("GIST_TOKEN", "")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def _gist_url():
    gist_id = st.secrets.get("GIST_ID", "")
    return f"https://api.github.com/gists/{gist_id}"

def load_db():
    try:
        r = requests.get(_gist_url(), headers=_gist_headers(), timeout=5)
        if r.status_code == 200:
            content = r.json()['files'][GIST_FILENAME]['content']
            return json.loads(content)
    except:
        pass
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"players": [], "games": [], "last_composition": []}

def save_db(db):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    try:
        requests.patch(
            _gist_url(),
            headers=_gist_headers(),
            json={"files": {GIST_FILENAME: {"content": json.dumps(db, ensure_ascii=False, indent=2)}}},
            timeout=5
        )
    except:
        pass

def get_player(db, pid):
    return next((p for p in db['players'] if p['id'] == pid), None)

def get_play_count(db, pid):
    p = get_player(db, pid)
    if p and 'history' in p:
        return len(p['history'])
    return 0


# ---- STYLES ----
def inject_styles():
    st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        flex-direction: row !important;
        gap: 2px !important;
        overflow: visible !important;
    }
    [data-testid="column"] {
        min-width: 80px !important;
        flex: 1 1 45% !important;
        max-width: 50% !important;
        overflow: visible !important;
    }
    div.stButton > button {
        height: 36px !important;
        min-height: 36px !important;
        font-size: 13px !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        margin: 1px 0 !important;
        padding: 2px 6px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div.stButton {
        margin-top: 2px !important;
        margin-bottom: 2px !important;
    }
    .big-timer {
        font-size: 96px;
        text-align: center;
        font-weight: bold;
        margin: 0;
        padding: 10px;
    }
    .fullscreen-msg {
        width: 100%;
        padding: 60px 20px;
        text-align: center;
        font-size: 72px;
        font-weight: bold;
        border-radius: 16px;
        margin: 20px 0;
    }
    .fs-mafia { background: #000; color: #fff; }
    .fs-civil { background: #cc0000; color: #fff; }
    .fs-sheriff-found { background: #00aa00; color: #fff; }
    .fs-civil-for-don { background: #cc0000; color: #fff; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stHorizontalBlock"] {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        gap: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def inject_gold_buttons(texts=None):
    if texts is None:
        texts = [
            "Спортивная", "Ночь 0", "Наступает Утро", "Голосование", "Итоги", "К ночи",
            "Далее → Ночь", "Далее (", "Далее", "Новая игра",
            "День 2", "День 3", "День 4", "День 5",
            "День 6", "День 7", "День 8", "День 9", "День 10",
        ]
    import json as _json
    keywords_js = _json.dumps(texts)
    components.html(f"""
    <script>
    function applyGold() {{
        const keywords = {keywords_js};
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(btn => {{
            if (btn.dataset.goldApplied) return;
            const text = btn.textContent || '';
            const isGold = keywords.some(kw => text.includes(kw));
            if (isGold) {{
                btn.style.border = '3px solid #DAA520';
                btn.style.boxShadow = '0 0 15px rgba(218, 165, 32, 0.6)';
                btn.dataset.goldApplied = '1';
            }}
        }});
    }}
    setTimeout(applyGold, 300);
    setTimeout(applyGold, 800);
    setTimeout(applyGold, 2000);
    </script>
    """, height=0)


# ---- MUSIC SYSTEM ----
SCREEN_MUSIC = {
    "main_menu": "mus1_start_menu.mp3",
    "select_mode": "mus1_start_menu.mp3",
    "select_players": "mus1_start_menu.mp3",
    "assign_roles": "mus2_assign_roles.mp3",
    "night_zero": "mus3_hello.mp3",
    "game_day": None,
    "game_vote": None,
    "game_vote_catastrophe": None,
    "game_last_word": None,
    "game_morning": None,
    "game_night": "night.mp3",
    "game_end": None,
    "manage_players": None,
    "archive": None,
    "export": None,
}


def sync_music():
    """Управление фоновой музыкой через SCREEN_MUSIC словарь."""
    if not st.session_state.get("music_enabled", True):
        # Музыка выключена — останавливаем если играет
        prev = st.session_state.get("_current_music")
        if prev is not None:
            components.html("""
            <script>
            (function() {
                var pd = window.parent.document;
                var old = pd.getElementById('bg_music');
                if (old) { old.pause(); old.remove(); }
                var audios = pd.querySelectorAll('audio.bg-music');
                audios.forEach(function(a) { a.pause(); a.remove(); });
            })();
            </script>
            """, height=0)
            st.session_state._current_music = None
        return

    scr = st.session_state.get("screen", "")
    track = SCREEN_MUSIC.get(scr)

    prev = st.session_state.get("_current_music")

    if track == prev:
        return

    st.session_state._current_music = track

    if track is None:
        components.html("""
        <script>
        (function() {
            var pd = window.parent.document;
            var old = pd.getElementById('bg_music');
            if (old) { old.pause(); old.remove(); }
            var audios = pd.querySelectorAll('audio.bg-music');
            audios.forEach(function(a) { a.pause(); a.remove(); });
        })();
        </script>
        """, height=0)
        return

    fn = os.path.join(MUSIC_FOLDER, track)
    if not os.path.exists(fn):
        return

    with open(fn, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()

    safe_name = track.replace('.', '_')

    components.html(f"""
    <script>
    (function() {{
        var pd = window.parent.document;

        var old = pd.getElementById('bg_music');
        if (old) {{ old.pause(); old.remove(); }}
        var audios = pd.querySelectorAll('audio.bg-music');
        audios.forEach(function(a) {{ a.pause(); a.remove(); }});

        var a = pd.createElement('audio');
        a.className = 'bg-music';
        a.id = 'bg_music';
        a.dataset.file = '{track}';
        a.src = 'data:audio/mp3;base64,{b64}';
        a.loop = true;
        a.volume = 0;
        a.preload = 'auto';
        pd.body.appendChild(a);

        var playPromise = a.play();
        if (playPromise !== undefined) {{
            playPromise.then(function() {{
                var vol = 0;
                var fi = setInterval(function() {{
                    vol += 0.02;
                    if (vol >= 0.3) {{ vol = 0.3; clearInterval(fi); }}
                    a.volume = vol;
                }}, 50);
            }}).catch(function() {{
                function resumeOnTouch() {{
                    a.play().then(function() {{
                        var vol = 0;
                        var fi = setInterval(function() {{
                            vol += 0.02;
                            if (vol >= 0.3) {{ vol = 0.3; clearInterval(fi); }}
                            a.volume = vol;
                        }}, 50);
                    }}).catch(function(){{}});
                    pd.removeEventListener('touchstart', resumeOnTouch);
                    pd.removeEventListener('click', resumeOnTouch);
                }}
                pd.addEventListener('touchstart', resumeOnTouch);
                pd.addEventListener('click', resumeOnTouch);
            }});
        }}
    }})();
    </script>
    """, height=0)



def _start_music(filename):
    fn_full = os.path.join(MUSIC_FOLDER, filename)
    if not os.path.exists(fn_full):
        return
    with open(fn_full, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    components.html(f"""
    <script>
    (function() {{
        var pd = window.parent.document;
        var old = pd.getElementById('bg_music');
        if (old) {{ old.pause(); old.remove(); }}

        var a = pd.createElement('audio');
        a.id = 'bg_music';
        a.dataset.file = '{filename}';
        a.src = 'data:audio/mp3;base64,{b64}';
        a.loop = true;
        a.volume = 0;
        pd.body.appendChild(a);

        a.play().catch(function() {{
            pd.addEventListener('click', function tryP() {{
                a.play().catch(function(){{}});
                pd.removeEventListener('click', tryP);
            }}, {{once:true}});
        }});

        var vol = 0;
        var fi = setInterval(function() {{
            vol += 0.02;
            if (vol >= 0.3) {{ vol = 0.3; clearInterval(fi); }}
            a.volume = vol;
        }}, 50);
    }})();
    </script>
    """, height=0)


def _fade_out_music():
    components.html("""
    <script>
    (function() {
        var a = window.parent.document.getElementById('bg_music');
        if (!a) return;
        var vol = a.volume;
        var fo = setInterval(function() {
            vol -= 0.02;
            if (vol <= 0) {
                vol = 0;
                clearInterval(fo);
                a.pause();
                a.remove();
            }
            a.volume = Math.max(0, vol);
        }, 50);
    })();
    </script>
    """, height=0)


def _crossfade_music(new_filename):
    fn_full = os.path.join(MUSIC_FOLDER, new_filename)
    if not os.path.exists(fn_full):
        _fade_out_music()
        return
    with open(fn_full, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    components.html(f"""
    <script>
    (function() {{
        var pd = window.parent.document;
        var old = pd.getElementById('bg_music');

        if (old) {{
            var ov = old.volume;
            var fo = setInterval(function() {{
                ov -= 0.02;
                if (ov <= 0) {{
                    clearInterval(fo);
                    old.pause();
                    old.remove();
                }}
                old.volume = Math.max(0, ov);
            }}, 50);
        }}

        var a = pd.createElement('audio');
        a.id = 'bg_music';
        a.dataset.file = '{new_filename}';
        a.src = 'data:audio/mp3;base64,{b64}';
        a.loop = true;
        a.volume = 0;
        pd.body.appendChild(a);

        setTimeout(function() {{
            a.play().catch(function() {{
                pd.addEventListener('click', function tryP() {{
                    a.play().catch(function(){{}});
                    pd.removeEventListener('click', tryP);
                }}, {{once:true}});
            }});
            var nv = 0;
            var fi = setInterval(function() {{
                nv += 0.02;
                if (nv >= 0.3) {{ nv = 0.3; clearInterval(fi); }}
                a.volume = nv;
            }}, 50);
        }}, 500);
    }})();
    </script>
    """, height=0)

# ---- SOUND EFFECTS ----

def preload_sounds():
    """Кеширует base64 звуков в session_state."""
    if st.session_state.get("_timer_sounds_cached"):
        return
    for fn in [TIMER_60_SOUND, TIMER_30_SOUND]:
        fn_full = os.path.join(SOUNDS_FOLDER, fn)
        if os.path.exists(fn_full):
            with open(fn_full, 'rb') as f:
                st.session_state[f"_snd_b64_{fn}"] = base64.b64encode(f.read()).decode()
    st.session_state._timer_sounds_cached = True


def play_timer_sound(duration=60):
    """Ставит флаг — звук запустится после rerun."""
    if not st.session_state.get("timer_sound_enabled", True):
        return
    st.session_state._play_timer_pending = duration



def stop_timer_sound():
    """Ставит флаг на остановку."""
    st.session_state._play_timer_pending = "stop"




def reset_timer_sound(duration=60):
    """Ставит флаг на сброс."""
    if not st.session_state.get("timer_sound_enabled", True):
        return
    st.session_state._play_timer_pending = f"reset_{duration}"


def _execute_pending_sound():
    """Выполняет отложенный звук — вызывать в mafia_companion.py после экрана."""
    pending = st.session_state.get("_play_timer_pending")
    if not pending:
        return
    st.session_state._play_timer_pending = None

    if pending == "stop":
        components.html("""
        <script>
        (function() {
            var pd = window.parent.document;
            var a = pd.getElementById('timer_audio');
            if (a) { a.pause(); a.currentTime = 0; }
        })();
        </script>
        """, height=0)
        return

    if isinstance(pending, str) and pending.startswith("reset_"):
        dur = int(pending.split("_")[1])
    else:
        dur = pending

    fn = TIMER_60_SOUND if dur == 60 else TIMER_30_SOUND
    b64 = st.session_state.get(f"_snd_b64_{fn}")
    if not b64:
        return

    components.html(f"""
    <script>
    (function() {{
        var pd = window.parent.document;
        var old = pd.getElementById('timer_audio');
        if (old) {{ old.pause(); old.remove(); }}
        var a = pd.createElement('audio');
        a.id = 'timer_audio';
        a.src = 'data:audio/mp3;base64,{b64}';
        a.volume = 1.0;
        pd.body.appendChild(a);
        a.play().catch(function(){{}});
    }})();
    </script>
    """, height=0)

def play_sound_html(fn):
    """Оставляем для обратной совместимости — не используется для таймеров."""
    pass


def inject_audio_controls():
    """Две кнопки-иконки в левом верхнем углу: музыка и метроном."""
    music_on = st.session_state.get("music_enabled", True)
    timer_on = st.session_state.get("timer_sound_enabled", True)

    music_icon = "🎵" if music_on else "🔇"
    timer_icon = "⏱️" if timer_on else "🔕"

    music_bg = "#1a3a1a" if music_on else "#3a1a1a"
    timer_bg = "#1a3a1a" if timer_on else "#3a1a1a"
    music_border = "#4CAF50" if music_on else "#662222"
    timer_border = "#4CAF50" if timer_on else "#662222"

    components.html(f"""
    <script>
    (function() {{
        var pd = window.parent.document;

        // Удаляем старые если есть
        var old = pd.getElementById('audio-controls-wrap');
        if (old) old.remove();

        // Создаём контейнер в parent
        var wrap = pd.createElement('div');
        wrap.id = 'audio-controls-wrap';
        wrap.style.cssText = 'position:fixed;top:60px;left:10px;z-index:99999;display:flex;flex-direction:column;gap:6px;';

        var btnMusic = pd.createElement('button');
        btnMusic.id = 'ac-btn-music';
        btnMusic.textContent = '{music_icon}';
        btnMusic.style.cssText = 'width:40px;height:40px;border-radius:50%;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;background:{music_bg};border:2px solid {music_border};-webkit-tap-highlight-color:transparent;';
        btnMusic.onclick = function() {{
            var buttons = pd.querySelectorAll('button');
            for (var b of buttons) {{
                if (b.textContent.includes('ac_Музыка')) {{
                    b.click(); return;
                }}
            }}
        }};

        var btnTimer = pd.createElement('button');
        btnTimer.id = 'ac-btn-timer';
        btnTimer.textContent = '{timer_icon}';
        btnTimer.style.cssText = 'width:40px;height:40px;border-radius:50%;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;background:{timer_bg};border:2px solid {timer_border};-webkit-tap-highlight-color:transparent;';
        btnTimer.onclick = function() {{
            var buttons = pd.querySelectorAll('button');
            for (var b of buttons) {{
                if (b.textContent.includes('ac_Метроном')) {{
                    b.click(); return;
                }}
            }}
        }};

        wrap.appendChild(btnMusic);
        wrap.appendChild(btnTimer);
        pd.body.appendChild(wrap);
    }})();
    </script>
    """, height=0)

    # Скрытые кнопки Streamlit
    if st.button("ac_Музыка", key="ac_music_toggle"):
        st.session_state.music_enabled = not st.session_state.get("music_enabled", True)
        if not st.session_state.music_enabled:
            components.html("""
            <script>
            (function() {
                var pd = window.parent.document;
                var a = pd.getElementById('bg_music');
                if (a) { a.pause(); }
                var audios = pd.querySelectorAll('audio.bg-music');
                audios.forEach(function(el) { el.pause(); });
            })();
            </script>
            """, height=0)
        else:
            st.session_state._current_music = None
        st.rerun()

    if st.button("ac_Метроном", key="ac_timer_toggle"):
        st.session_state.timer_sound_enabled = not st.session_state.get("timer_sound_enabled", True)
        if not st.session_state.timer_sound_enabled:
            stop_timer_sound()
        st.rerun()

    # Прячем ac_ кнопки
    components.html("""
    <script>
    (function() {
        function hide() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(b => {
                if ((b.textContent || '').startsWith('ac_')) {
                    const w = b.closest('div[data-testid="stButton"]');
                    if (w) w.style.cssText = 'height:0!important;min-height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;opacity:0!important;position:absolute!important;pointer-events:none!important;';
                }
            });
        }
        setTimeout(hide, 50);
        setTimeout(hide, 200);
        setTimeout(hide, 500);
    })();
    </script>
    """, height=0)

# ---- NAVIGATION ----
def go(screen):
    st.session_state.screen = screen


# ---- SESSION STATE ----
def init_state():
    defaults = {
        "screen": "main_menu",
        "game": None,
        "day_number": 0,
        "current_speaker": 0,
        "nominees": {},
        "votes": {},
        "vote_voters": {},
        "vote_step": 0,
        "night_actions": {},
        "game_log": [],
        "hide_sensitive": False,
        "edit_player_id": None,
        "selected_pids": [],
        "role_assignment_mode": None,
        "manual_assigned": {},
        "mafia_notes": "",
        "killed_tonight": [],
        "eliminated_today": [],
        "night_phase_step": 0,
        "fullscreen_message": None,
        "best_move_used": False,
        "best_move_targets": [],
        "best_move_morning": [],
        "confirm_auto_roles": False,
        "catastrophe_tied": [],
        "show_roles": False,
        "_current_music": None,
        "music_enabled": True,
        "timer_sound_enabled": True,
        "_timer_sounds_cached": False,
        "_play_timer_pending": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---- HELPERS ----
def calculate_roles(num_players):
    if num_players == 10:
        return {"Дон": 1, "Шериф": 1, "Мафия": 2, "Мирный": 6}
    mafia_count = max(1, num_players // 4)
    civil_count = num_players - mafia_count - 2
    return {"Дон": 1, "Шериф": 1, "Мафия": mafia_count, "Мирный": civil_count}

def get_alive():
    if not st.session_state.game:
        return []
    return [p for p in st.session_state.game['players'] if p['status'] == 'alive']

def get_speaker_order(day, players):
    alive = [p for p in players if p['status'] == 'alive']
    alive_sorted = sorted(alive, key=lambda p: p['number'])
    if not alive_sorted:
        return []
    n_total = len(players)
    if day == 1:
        return alive_sorted
    start_number = ((day - 1) % n_total) + 1
    alive_numbers = sorted([p['number'] for p in alive_sorted])
    opener = None
    for num in alive_numbers:
        if num >= start_number:
            opener = num
            break
    if opener is None:
        opener = alive_numbers[0]
    opener_idx = alive_numbers.index(opener)
    rotated_numbers = alive_numbers[opener_idx:] + alive_numbers[:opener_idx]
    num_to_player = {p['number']: p for p in alive_sorted}
    result = [num_to_player[num] for num in rotated_numbers]
    return result

def role_emoji(role):
    mapping = {
        "Дон": "⭐",
        "Мафия": "👎",
        "Шериф": "🐙",
        "Мирный": "❤️",
    }
    return mapping.get(role, "❓")

def p_num(p):
    if st.session_state.get("show_roles") and p.get('role'):
        return f"{role_emoji(p['role'])}#{p['number']}"
    return f"#{p['number']}"

def p_name(p):
    if st.session_state.get("show_roles") and p.get('role'):
        return f"{p['nickname']} ({role_emoji(p['role'])} {p['role']})"
    return p['nickname']

def p_bar_text(p):
    if st.session_state.get("show_roles") and p.get('role'):
        return f"{role_emoji(p['role'])} ㅤㅤ{p['number']} ㅤㅤ{p['nickname']}"
    return f"#{p['number']}. {p['nickname']}"

def run_timer_no_block(placeholder, duration=60):
    for sec in range(duration, -1, -1):
        if sec > 10:
            color = "white"
        elif sec > 5:
            color = "orange"
        else:
            color = "red"
        placeholder.markdown(
            f'<p class="big-timer" style="color:{color};">{sec}</p>',
            unsafe_allow_html=True
        )
        if sec <= 10 and sec > 0:
            play_sound_html(METRONOME_SOUND)
        if sec == 0:
            play_sound_html(WHISTLE_SOUND)
        time.sleep(1)