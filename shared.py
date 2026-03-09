import streamlit as st
import json
import os
import time
import base64
import streamlit.components.v1 as components


# ---- SETTINGS ----
DB_FILE = 'mafia_db.json'
MUSIC_FOLDER = os.path.join(os.path.dirname(__file__), "music")
SOUNDS_FOLDER = os.path.join(os.path.dirname(__file__), "sounds")
METRONOME_SOUND = "metronome.mp3"
WHISTLE_SOUND = "whistle.mp3"

# ---- STYLES ----
def inject_styles():
    st.markdown("""
    <style>
    /* Фиксированная минимальная ширина контента */
    .stMainBlockContainer, [data-testid="stMainBlockContainer"] {
        min-width: 700px !important;
    }
    .stMain, [data-testid="stMain"] {
        overflow-x: auto !important;
    }

    div.stButton > button {
        height: 40px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        margin: 2px;
    }
    .big-timer {
        font-size: 96px;
        text-align: center;
        font-weight: bold;
        margin: 0;
        padding: 10px;
    }
    .player-bar {
        height: 40px;
        display: flex;
        align-items: center;
        padding: 4px 12px;
        margin: 2px 0;
        border-radius: 6px;
        font-size: 16px;
        font-weight: bold;
        position: relative;
        overflow: hidden;
    }
    .player-bar .progress-fill {
        position: absolute;
        left: 0; top: 0; bottom: 0;
        background: rgba(76, 175, 80, 0.3);
        z-index: 0;
        border-radius: 6px;
    }
    .player-bar .content {
        position: relative;
        z-index: 1;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .player-row-dead {
        height: 20px;
        display: flex;
        align-items: center;
        padding: 2px 8px;
        margin: 1px 0;
        border-radius: 4px;
        font-size: 12px;
        opacity: 0.4;
        text-decoration: line-through;
    }
    .counter-bar {
        position: sticky; top: 0; background: #1a1a1a;
        padding: 10px; z-index: 100; text-align: center;
        font-size: 24px; font-weight: bold; color: white;
        border-bottom: 2px solid #444;
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



def background_music(filename, loop=True):
    """Фоновая музыка"""
    fn_full = os.path.join(MUSIC_FOLDER, filename)
    if not os.path.exists(fn_full):
        st.warning(f"Файл не найден: {fn_full}")
        return

    size_mb = os.path.getsize(fn_full) / (1024 * 1024)

    if size_mb > 2:
        # Большой файл — через st.audio (проще, но обрывается при rerun)
        audio_bytes = open(fn_full, 'rb').read()
        st.audio(audio_bytes, format='audio/mp3', autoplay=True, loop=loop)
    else:
        # Маленький файл — через JS (не обрывается при rerun)
        audio_bytes = open(fn_full, 'rb').read()
        b64 = base64.b64encode(audio_bytes).decode()
        loop_js = "audio.loop = true;" if loop else ""
        components.html(f"""
        <script>
        (function() {{
            var existing = window.parent.document.getElementById('bg_music');
            if (existing) {{
                if (existing.dataset.file === '{filename}') return;
                existing.pause();
                existing.remove();
            }}
            var audio = document.createElement('audio');
            audio.id = 'bg_music';
            audio.dataset.file = '{filename}';
            audio.src = 'data:audio/mp3;base64,{b64}';
            {loop_js}
            audio.volume = 0.3;
            audio.play();
            window.parent.document.body.appendChild(audio);
        }})();
        </script>
        """, height=0)

def stop_background_music():
    """Остановить фоновую музыку"""
    components.html("""
    <script>
    (function() {
        var audio = window.parent.document.getElementById('bg_music');
        if (audio) { audio.pause(); audio.remove(); }
    })();
    </script>
    """, height=0)

# ---- DATABASE ----
def load_db():
    if not os.path.exists(DB_FILE):
        return {"players": [], "games": [], "last_composition": []}
    with open(DB_FILE, 'r', encoding='utf8') as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def get_player(db, pid):
    return next((p for p in db['players'] if p['id'] == pid), None)

def get_play_count(db, pid):
    p = get_player(db, pid)
    if p and 'history' in p:
        return len(p['history'])
    return 0

# ---- SOUND ----
def play_sound_html(fn):
    fn_full = os.path.join(SOUNDS_FOLDER, fn)
    if not os.path.exists(fn_full):
        return
    audio_bytes = open(fn_full, 'rb').read()
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(
        f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
        unsafe_allow_html=True
    )



def music_player():
    files = [f for f in os.listdir(MUSIC_FOLDER) if f.endswith(".mp3")]
    if not files:
        return
    if "current_track" not in st.session_state:
        st.session_state.current_track = files[0]
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.session_state.current_track = st.selectbox(
            "🎵", files,
            index=files.index(st.session_state.current_track) if st.session_state.current_track in files else 0,
            key="***HIDDEN***"
        )
    with col2:
        if st.button("▶️", key="music_play", use_container_width=True):
            fn = os.path.join(MUSIC_FOLDER, st.session_state.current_track)
            if os.path.exists(fn):
                st.audio(open(fn, 'rb').read(), format="audio/mp3")
    with col3:
        if st.button("⏹️", key="music_stop", use_container_width=True):
            pass

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
    """Номер игрока с эмодзи роли если включено"""
    if st.session_state.get("show_roles") and p.get('role'):
        return f"{role_emoji(p['role'])}#{p['number']}"
    return f"#{p['number']}"


def p_name(p):
    """Имя игрока с ролью если включено"""
    if st.session_state.get("show_roles") and p.get('role'):
        return f"{p['nickname']} ({role_emoji(p['role'])} {p['role']})"
    return p['nickname']


def p_bar_text(p):
    """Текст для прогресс-бара: эмодзи + номер + имя"""
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