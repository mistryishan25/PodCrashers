from __future__ import annotations
import streamlit as st
import json, time, pathlib
from typing import List, Dict
from streamlit_advanced_audio import audix, WaveSurferOptions

st.set_page_config(page_title="PodCrashers", layout="wide")

# ─────── Constants ───────
PLAY_SPEED = 1.0  # 1 = realtime
UPDATE_INTERVAL = 0.1  # Update every 100ms
TIMESTAMP_UNIT = "ms"  # Set to "sec" if your chat.json uses seconds
AUDIO_OFFSET = 0.0    # Positive = audio starts earlier, Negative = audio starts later

# ─────── Session State ───────
state = st.session_state
state.setdefault("chat_started", False)     # flag
state.setdefault("audio_result", None)      # audix playback data
state.setdefault("current_time", 0.0)       # current audio time
state.setdefault("user_messages", [])       # user chat messages
state.setdefault("next_host_idx", 0)        # next host message to reveal
state.setdefault("last_update", 0.0)        # last UI update time

# ─────── Load chat.json (once) ───────
chat_path = pathlib.Path("chat.json")
if "chat" not in state:
    if chat_path.exists():
        raw = json.loads(chat_path.read_text())
        
        # Flexible timestamp conversion
        def convert_timestamp(t: int) -> float:
            if TIMESTAMP_UNIT == "ms":
                return t / 1000.0
            elif TIMESTAMP_UNIT == "sec":
                return float(t)
            else:
                return t  # Fallback to raw value
        
        state.chat = sorted([
            {
                "time": convert_timestamp(u["startTimecode"]),
                "end_time": convert_timestamp(u.get("endTimecode", u["startTimecode"] + 5000)),
                "speaker": u["speaker"],
                "text": u["text"]
            }
            for u in raw.get("transcript", [])
        ], key=lambda x: x["time"])
    else:
        state.chat = []
        st.warning("chat.json not found")

# Add a name for each speaker
if "speaker_map" not in state and state.chat:
    state.speaker_map = {spk: spk for spk in set(msg["speaker"] for msg in state.chat)}

# ─────── Layout ───────
st.title("🎙️ PodCrashers – Interactive Hub")
chat_col, player_col = st.columns([3, 1])

# -------- Player Column --------
def get_podcast_url(podcast_name: str):
    return "https://21963.mc.tritondigital.com/OMNY_DREAMSEQUENCE_PODCAST_P/media-session/4a78a4df-beb7-434a-8a4d-556524a4afb6/d/clips/e73c998e-6e60-432f-8610-ae210140c5b1/73ab9706-937d-4cc0-8bc7-b1a900d9901c/c1e4972c-9df0-4f25-b42d-b1f100e4c4a2/audio/direct/t1727064315/Episode_9.mp3?t=1727064315&starship-rollup=v0_324444414444&starship-episode-id=899d8a14-4cb9-453c-91d8-d2efa8c9607b&in_playlist=6ee041c6-4ac8-45ce-9b6d-b1a900e3b7de&utm_source=Podcast"

def display_list_podcasts():
    return ["Dream Sequence", "Podcast B", "Podcast C"]

def display_list_episodes(podcast_name: str):
    return [f"{podcast_name} Episode 1", f"{podcast_name} Episode 9"]

with player_col:
    st.subheader("🎵 Player")
    
    # Podcast and episode selection
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
        
        if episode:
            audio_url = get_podcast_url(episode)
            state.audio_url = audio_url
            # Reset chat state when new episode starts
            state.next_host_idx = 0
            state.user_messages = []
            state.chat_started = False
            st.success(f"Playing: {episode}")

# -------- Live Chat with Sync --------
with chat_col:
    st.subheader("💬 Synchronized Chat")
    chat_container = st.container(height=500)
    
    # Calculate adjusted current time
    adjusted_time = max(0, state.current_time - AUDIO_OFFSET)
    
    # Update current time from audix
    if state.audio_result:
        state.current_time = state.audio_result.get("currentTime", 0)
        state.chat_started = state.audio_result.get("isPlaying", False)
    
    if state.chat_started:
        st.write(f"**Audio Position:** {adjusted_time:.1f}s (Offset: {AUDIO_OFFSET}s)")
        
        # Reveal new host messages as audio progresses
        while (state.next_host_idx < len(state.chat) and 
               state.chat[state.next_host_idx]["time"] <= adjusted_time):
            state.next_host_idx += 1
        
        # Get all messages to display (revealed host + user messages)
        revealed_messages = state.chat[:state.next_host_idx]
        all_messages = sorted(
            revealed_messages + state.user_messages,
            key=lambda x: x["time"]
        )
        
        # Display messages with highlighting
        for msg in all_messages:
            # Determine if message is active
            is_active = False
            if "end_time" in msg:  # Host message
                is_active = msg["time"] <= adjusted_time < msg["end_time"]
            else:  # User message
                is_active = abs(adjusted_time - msg["time"]) < 2.0
            
            # Display message
            avatar = "🎤" if "speaker" in msg else "🙋"
            role = "assistant" if "speaker" in msg else "user"
            
            with chat_container.chat_message(role, avatar=avatar):
                # Highlight active messages
                if is_active:
                    st.markdown(
                        f'<div style="border-left: 4px solid #4CAF50; padding: 8px;">'
                        f'{msg["text"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(msg["text"])
                
                # Show speaker and timestamp
                caption = f"{msg.get('speaker', 'You')} @ {msg['time']:.1f}s"
                st.caption(caption)
        
        # User input
        user_msg = st.chat_input(placeholder="Your message", key="listener_input", max_chars=200)
        if user_msg:
            state.user_messages.append({
                "text": user_msg,
                "time": adjusted_time
            })
            st.rerun()

# -------- Advanced Audio Player at Bottom --------
if state.get("audio_url"):
    st.subheader("🎵 Advanced Audio Player")
    # Configure audix player
    options = WaveSurferOptions(
        wave_color="#2B88D9",
        progress_color="#b91d47",
        height=100
    )
    state.audio_result = audix(
        state.audio_url,
        wavesurfer_options=options,
        key="audix_player"
    )

# ─────── Real-time Sync Trigger ───────
if state.audio_result and state.audio_result.get("isPlaying", False):
    now = time.time()
    if now - state.last_update > UPDATE_INTERVAL:
        state.last_update = now
        st.rerun()
