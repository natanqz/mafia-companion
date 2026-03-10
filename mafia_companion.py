import streamlit as st
from shared import (
    init_state, inject_styles, inject_gold_buttons,
    preload_sounds, inject_audio_controls, _execute_pending_sound
)
from screens_setup import (
    screen_main_menu,
    screen_select_mode,
    screen_select_players,
    screen_assign_roles,
    screen_night_zero,
    screen_players_list,
    screen_edit_player,
)
from screens_game import (
    screen_game_day,
    screen_game_vote,
    screen_game_vote_catastrophe,
    screen_game_last_word,
)
from screens_night import (
    screen_game_night,
    screen_game_morning,
    screen_game_end,
    screen_archive,
    screen_export_import,
)

st.set_page_config(page_title="🎭 Мафия Компаньон", layout="wide")
init_state()
inject_styles()
preload_sounds()
inject_audio_controls()

SCREENS = {
    "main_menu": screen_main_menu,
    "select_mode": screen_select_mode,
    "select_players": screen_select_players,
    "assign_roles": screen_assign_roles,
    "night_zero": screen_night_zero,
    "game_day": screen_game_day,
    "game_vote": screen_game_vote,
    "game_vote_catastrophe": screen_game_vote_catastrophe,
    "game_last_word": screen_game_last_word,
    "game_night": screen_game_night,
    "game_morning": screen_game_morning,
    "game_end": screen_game_end,
    "archive": screen_archive,
    "players_list": screen_players_list,
    "edit_player": screen_edit_player,
    "export_import": screen_export_import,
}

current = st.session_state.screen
if current in SCREENS:
    SCREENS[current]()
else:
    screen_main_menu()

_execute_pending_sound()
inject_gold_buttons()