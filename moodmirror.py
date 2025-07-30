import streamlit as st
import datetime
import requests
import random
import time
import base64
from streamlit_drawable_canvas import st_canvas

# Configures appearance of streamlit app page
st.set_page_config(page_title="MoodMirror 🎨", layout="centered")

# CSS controls how app looks and feels
st.markdown("""
    <style>
        :root {
            color-scheme: dark;
        }
        html, body, .main {
            background-color: #121212;
            font-family: 'Segoe UI', sans-serif;
            color: #ffffff;
        }
        .center {
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        .title {
            font-size: 2.8rem;
            text-align: center;
            font-weight: 700;
            color: #f97316;
            margin-bottom: 0.3rem;
        }
        .subtitle {
            font-size: 1.3rem;
            color: #f97316;
            text-align: center;
            margin-bottom: 2rem;
        }
        .entry {
            font-size: 1rem;
            padding: 12px 16px;
            border-radius: 10px;
            background-color: #1e1e1e;
            color: #e0e0e0;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2);
            margin-bottom: 12px;
        }
        .quote {
            font-size: 1.4rem;
            font-weight: 600;
            color: #f97316;
            margin-top: 24px;
        }
        .color-game {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            margin: 2rem 0;
            padding: 1rem;
            border-radius: 10px;
            background-color: #1e1e1e;
        }
        .tarot-card {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #333;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        .tarot-title {
            font-size: 1.5rem;
            text-align: center;
            margin-bottom: 1rem;
            color: #ff6b6b;
        }
        .tarot-message {
            font-size: 1.2rem;
            text-align: center;
            color: #e0e0e0;
        }
        .stRadio > div {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 10px;
        }
        .stress-hub {
            margin: 2rem 0;
            padding: 1.5rem;
            background-color: #1e1e1e;
            border-radius: 10px;
            border: 1px solid #333;
        }
    </style>
""", unsafe_allow_html=True)

HF_API_TOKEN = "HUGGING_FACE_API_TOKEN"

if 'entries' not in st.session_state:
    st.session_state.entries = []
if 'paintings' not in st.session_state:
    st.session_state.paintings = []
if 'color_score' not in st.session_state:
    st.session_state.color_score = 0

# Displays title and subtitle
st.markdown('<div class="title">🪞 MoodMirror</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Log your mood daily. After 7 days, receive a custom painting based on your emotions.</div>',
    unsafe_allow_html=True)

# Handles the input for todays entry and mood
today = datetime.date.today()
entry_text = st.text_input("📝 Today's Journal (one line):")
mood = st.selectbox("🧠 Mood",
                    ["😊 Happy", "😔 Sad", "😐 Neutral", "😠 Angry", "😰 Anxious"])
allow_multiple = st.toggle("Allow multiple entries today", value=False)

# Checks if an entry has already been submitted today
already_logged_today = any(e["date"] == str(today)
                           for e in st.session_state.entries)

if already_logged_today and not allow_multiple:
    st.warning("You've already logged today's mood.")
elif st.button("Submit Entry"):
    st.session_state.entries.append({
        "date": str(today),
        "entry": entry_text,
        "mood": mood
    })
    st.success("✅ Mood logged for today!")

# Displays the last 7 mood entries
st.write("### 🗒️ Past Entries")
for e in st.session_state.entries[-7:]:
    st.markdown(f"""
        <div class="entry">
        📅 <b>{e['date']}</b> | {e['mood']}<br>
        ✍️ <i>{e['entry']}</i>
        </div>
    """, unsafe_allow_html=True)

def summarize_moods(entries):
    moods = [e["mood"].split()[1] for e in entries]
    summary = {}
    for m in moods:
        summary[m] = summary.get(m, 0) + 1
    return summary

def create_prompt(mood_summary):
    parts = [f"{v} {k.lower()} day{'s' if v > 1 else ''}" for k, v in mood_summary.items()]
    return "A dreamy painting inspired by " + ", ".join(parts)

def reflect(summary):
    if not summary:
        return ""
    dominant = max(summary, key=summary.get)
    return f"🧘 Your week leaned towards **{dominant.lower()}**. Let's turn that into a painting."

# Painting Generation Section
if len(st.session_state.entries) >= 7 and len(st.session_state.entries) // 7 > len(st.session_state.paintings):
    st.write("## 🎨 Your Mood Painting")
    mood_summary = summarize_moods(st.session_state.entries[-7:])
    prompt = create_prompt(mood_summary)
    reflection = reflect(mood_summary)

    if reflection:
        st.markdown(f"**{reflection}**")
    st.info(f"🖌️ Prompt: *{prompt}*")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎨 Generate Painting", use_container_width=True):
            with st.spinner("Painting your week... 🎨"):
                headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
                API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
                response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
                
                if response.status_code == 200:
                    st.image(response.content, caption="Your Mood Painting 🎨")
                    st.session_state.paintings.append({
                        "prompt": prompt,
                        "image": response.content,
                        "date": str(today)
                    })
                    st.markdown(
                        '<div class="center"><div class="quote">✨ Keep going, you\'re doing great! 🌟</div></div>',
                        unsafe_allow_html=True)
                else:
                    st.error("Something went wrong with the image generation 😢")
                    st.code(response.text)

# Stress Hub Section
st.markdown('<div id="stress-hub"></div>', unsafe_allow_html=True)
with st.container():
    st.write("## 🧘‍♀️ Stress Hub")
    st.write("Take a break with these relaxing activities:")
    
    tabs = st.tabs(["🎨 Color Match", "🔮 Mood Tarot", "🌬️ Breathing Exercise"])
    
    with tabs[0]:  # Color Match Game
        st.write("### 🎨 Color Match Challenge")
        color_names = ["🔴 Red", "🟢 Green", "🔵 Blue", "🟡 Yellow", "🟣 Purple", "🟠 Orange"]
        colors = {
            "🔴 Red": "#ff0000",
            "🟢 Green": "#00ff00", 
            "🔵 Blue": "#0000ff",
            "🟡 Yellow": "#ffff00",
            "🟣 Purple": "#800080",
            "🟠 Orange": "#ffa500"
        }
        
        if 'color_game' not in st.session_state:
            st.session_state.color_game = {
                'current_color': random.choice(color_names),
                'text_color': random.choice(color_names),
                'score': 0,
                'last_result': None,
                'correct_answer': None
            }
            while st.session_state.color_game['text_color'] == st.session_state.color_game['current_color']:
                st.session_state.color_game['text_color'] = random.choice(color_names)
        
        st.markdown(
            f'<div class="color-game" style="color:{colors[st.session_state.color_game["text_color"]]}">'
            f'{st.session_state.color_game["current_color"].split()[1]}</div>',
            unsafe_allow_html=True
        )
        
        selected = st.radio("What color is the text?", color_names)
        
        if st.button("Check Answer"):
            if selected == st.session_state.color_game['text_color']:
                st.session_state.color_game['score'] += 1
                st.session_state.color_game['last_result'] = "correct"
                st.success(f"✅ Correct! Score: {st.session_state.color_game['score']}")
            else:
                st.session_state.color_game['last_result'] = "incorrect"
                st.error(f"❌ It was {st.session_state.color_game['text_color'].split()[1]}. Score: {st.session_state.color_game['score']}")
            
            # Generate new colors
            st.session_state.color_game['current_color'] = random.choice(color_names)
            st.session_state.color_game['text_color'] = random.choice(color_names)
            while st.session_state.color_game['text_color'] == st.session_state.color_game['current_color']:
                st.session_state.color_game['text_color'] = random.choice(color_names)
            
            st.rerun()
    
    with tabs[1]:  # Mood Tarot
        st.write("### 🔮 Mood Tarot")
        tarot_messages = [
            "You are stronger than you think. Trust in your resilience.",
            "Joy is coming your way. Stay open to new possibilities.",
            "Your creativity will blossom today. Express yourself freely.",
            "A moment of peace awaits you. Breathe deeply and receive it.",
            "You are exactly where you need to be. Trust the journey.",
            "Your kindness creates ripples of positivity in the world.",
            "Today holds unexpected blessings. Keep your heart open.",
            "You have everything you need within you. Trust yourself.",
            "The universe is conspiring in your favor. Have faith.",
            "Your positive energy attracts wonderful opportunities.",
            "Release what no longer serves you. Make space for joy.",
            "You are a beacon of light. Shine brightly today.",
            "Good things come to those who believe. Keep the faith.",
            "Your challenges are preparing you for something greater.",
            "Today is a gift. Cherish each moment with gratitude."
        ]
        
        if st.button("Draw Your Card"):
            selected_message = random.choice(tarot_messages)
            st.markdown(f"""
                <div class="tarot-card">
                    <div class="tarot-title">✨ Your Card ✨</div>
                    <div class="tarot-message">{selected_message}</div>
                </div>
            """, unsafe_allow_html=True)
    
    with tabs[2]:  # Breathing Exercise
        st.write("### 🌬️ Catch Your Breath")
        breath_option = st.radio(
            "Select your breathing visual:",
            ["🌊 Ocean Waves", "☁️ Sky Gazer", "🌀 Ripple Pond", "🌠 Star Drift"],
            horizontal=True
        )
        
        # YouTube embed codes
        youtube_embeds = {
            "🌊 Ocean Waves": "https://www.youtube.com/embed/WHPEKLQID4U",
            "☁️ Sky Gazer": "https://www.youtube.com/embed/FaU8BkqmXzo",
            "🌀 Ripple Pond": "https://www.youtube.com/embed/FeXP7SxCKKE", 
            "🌠 Star Drift": "https://www.youtube.com/embed/7iqqokBxYIY"
        }
        
        st.components.v1.html(f"""
        <div style="display: flex; justify-content: center;">
            <iframe width="640" height="360" src="{youtube_embeds[breath_option]}?autoplay=1&mute=1&loop=1" 
            frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
        </div>
        """, height=400)
        
        st.write("""
            **Breathing Exercise:**
            - Breathe in slowly for 4 seconds
            - Hold your breath for 4 seconds
            - Exhale slowly for 6 seconds
            - Repeat for 1 minute
        """)

# Painting Archive Section
if st.session_state.paintings:
    st.write("## 🖼️ Your Painting Archive")
    for p in reversed(st.session_state.paintings):
        st.image(p["image"],
                 caption=f"{p['date']} — {p['prompt']}",
                 use_container_width=True)