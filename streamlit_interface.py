"""
Interactive Podcast Hub – Interactive Chat + User Input
======================================================
Hosts’ messages play automatically at their original timestamps *and*
listeners can jump in at any moment via a chat input box.



Run with:
    streamlit run interactive_podcast_app.py
"""

from __future__ import annotations
import streamlit as st
import json, time, pathlib
from typing import List, Dict

st.set_page_config(page_title="PodCrashers", layout="wide")
PLAY_SPEED = 1.0  # 1 = realtime; bump to 2.0 for 2× speed

# ─────── Session State ───────
state = st.session_state
state.setdefault("notes", [])               # saved notes
state.setdefault("chat_started", False)     # flag
state.setdefault("start_time", None)        # wall‑clock when playback began
state.setdefault("host_idx", 0)             # next host line to reveal
state.setdefault("history", [])             # accumulated chat bubbles

# ─────── Load chat.json (once) ───────
chat_path = pathlib.Path("chat.json")
if "chat" not in state:
    if chat_path.exists():
        raw = json.loads(chat_path.read_text())
        def _sec(ts: str) -> float:
            parts = ts.split(":")
            h, m, s = (0, *parts) if len(parts) == 2 else parts
            return int(h)*3600 + int(m)*60 + float(s)
        state.chat = sorted([
            {"time": _sec(u["start_time"]), "speaker": u["speaker"], "text": u["text"]}
            for u in raw.get("utterances", [])
        ], key=lambda x: x["time"])
    else:
        state.chat = []

# Assign emoji avatars per speaker
avatars = ["🎤", "🎙️", "🎧", "📣", "🔊", "🎼", "📻", "🗣️"]
if "avatar_map" not in state:
    uniq = list(dict.fromkeys(msg["speaker"] for msg in state.chat))
    state.avatar_map = {spk: avatars[i % len(avatars)] for i, spk in enumerate(uniq)}

# ─────── Layout ───────
st.title("🎙️ PodCrashers – Interactive Hub")
chat_col, player_col = st.columns([3, 1])

# -------- Player --------

def display_list_podcasts():
    # placeholder function to simulate podcast list retrieval from the database
    """Returns a list of podcast Names."""
    return ["Podcast A", "Podcast B", "Podcast C"]

def display_list_episodes(podcast_name: str):
    # placeholder function to simulate episode list retrieval for a given podcast
    """Returns a list of episode Names for the given podcast."""
    return [f"{podcast_name} Episode 1", f"{podcast_name} Episode 2"]

with player_col:
    st.subheader("🎵 Player")
    option = st.selectbox(
    "What podcast would you like to listen to?",
    display_list_podcasts(),
    index=None,
    placeholder="Select a podcast...",
)
    if option:
        episode = st.selectbox(
            "Select an episode:",
            display_list_episodes(option),
            index=None,
            placeholder="Select an episode...",
        )

    uploaded = st.file_uploader("Upload", type=["mp3", "wav", "ogg"])
    if uploaded:
        st.audio(uploaded, format="audio/mp3")
    else:
        st.info("Selecet a podcast from the list or upload your own.")

# -------- Live Chat --------
with chat_col:
    st.subheader("💬 Live Chat")
    chat_container = st.container()

    # 1️⃣  Kick‑off button (only before start)
    if not state.chat_started:
        if st.button("Start Chat"):
            state.chat_started = True
            state.start_time = time.time()
            state.host_idx = 0
            state.history.clear()

    # 2️⃣  Reveal new host messages based on elapsed time
    if state.chat_started and state.host_idx < len(state.chat):
        elapsed = (time.time() - state.start_time) * PLAY_SPEED
        while state.host_idx < len(state.chat) and state.chat[state.host_idx]["time"] <= elapsed:
            msg = state.chat[state.host_idx]
            avatar = state.avatar_map.get(msg["speaker"], "🎤")
            state.history.append(({"role": "assistant", "avatar": avatar,
                                   "content": f"**{msg['speaker']}:** {msg['text']}"}))
            state.host_idx += 1
            

    # 3️⃣  Render full history each run
    for bubble in state.history:
        with chat_container.chat_message(bubble["role"], avatar=bubble["avatar"]):
            st.write(bubble["content"])
            st.divider()

    # 4️⃣  User input (always available once chat started)
    if state.chat_started:
        user_msg = st.chat_input(placeholder="Your message", key="listener_input", max_chars=200)
        if user_msg:
            state.history.append({"role": "user", "avatar": "🙋", "content": user_msg})
            st.rerun()

    if not state.chat_started and not state.chat:
        st.warning("chat.json missing or empty.")

# -------- Notes --------
def update_user_notes():
    """
    AIRFLOW TRIGGER:
    Update the user notes from the session state into the postgres instance.
    """

def update_interruptions():
    """
    AIRFLOW TRIGGER:
    Update the user interruptions from the session state into the postgres instance.
    """