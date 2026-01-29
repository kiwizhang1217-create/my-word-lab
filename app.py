import streamlit as st
import pandas as pd
import os
import base64
from gtts import gTTS
import streamlit.components.v1 as components

# --- 1. 页面配置 ---
st.set_page_config(page_title="极速自动背单词", layout="wide")

# --- 2. 核心功能函数 ---
def load_data():
    if os.path.exists("my_words.xlsx"):
        df = pd.read_excel("my_words.xlsx")
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    return pd.DataFrame()

def get_audio_base64(text):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("speech.mp3")
        with open("speech.mp3", "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

# --- 3. 初始化状态 ---
df_all = load_data()
if 'current_idx' not in st.session_state: st.session_state.current_idx = 0
if 'mistakes' not in st.session_state: st.session_state.mistakes = []

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("🎒 学习中心")
    unit_col = 'unit' if 'unit' in df_all.columns else None
    units = sorted(list(set(df_all[unit_col].astype(str)))) if unit_col else []
    selected_unit = st.radio("选择单元", ["全部单词"] + units)
    show_mistakes = st.toggle("🔍 错词复习")

current_pool = st.session_state.mistakes if show_mistakes else (
    df_all.to_dict('records') if selected_unit == "全部单词" 
    else df_all[df_all[unit_col] == selected_unit].to_dict('records')
)

if not current_pool:
    st.warning("词库为空！")
    st.stop()

word_item = current_pool[st.session_state.current_idx % len(current_pool)]
target_word = str(word_item.get('en', '')).lower().strip()
audio_b64 = get_audio_base64(target_word)

# --- 5. 增强 HTML/JS 组件 (模拟点击跳转) ---
custom_component = f"""
<div id="root">
    <div class="word-wrapper">
        <div id="input-container"></div>
        <div id="meaning-box">
            <span class="pos">{word_item.get('type', word_item.get('词性', ''))}</span>
            <span class="cn">{word_item.get('cn', word_item.get('中文', ''))}</span>
            <span class="speaker-icon" onclick="playAudio()">🔊</span>
        </div>
        <div class="phonetic">{word_item.get('phonetic', '')}</div>
        <audio id="word-audio" src="data:audio/mp3;base64,{audio_b64}"></audio>
    </div>
</div>

<style>
    body {{ background-color: #f0f4f2; font-family: sans-serif; display: flex; justify-content: center; }}
    .word-wrapper {{ 
        text-align: center; background: white; padding: 40px; border-radius: 35px; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.06); width: 95%; max-width: 800px; margin-top: 20px;
    }}
    #input-container {{ display: flex; justify-content: center; gap: 12px; margin-bottom: 30px; height: 120px; align-items: center; }}
    .letter-box {{
        width: 65px; height: 85px; border: 2px solid #d1d9d6; border-bottom: 6px solid #bdc3c7;
        border-radius: 12px; font-size: 42px; font-weight: 800; text-align: center;
        outline: none; transition: all 0.2s; box-shadow: 0 6px 12px rgba(0,0,0,0.05);
    }}
    .correct {{ border-bottom-color: #27ae60 !important; background-color: #e8f5e9 !important; color: #27ae60 !important; }}
    .wrong {{ border-bottom-color: #e74c3c !important; background-color: #fdf2f2 !important; color: #e74c3c !important; }}
    #meaning-box {{ margin-top: 20px; font-size: 36px; font-weight: 900; color: #1a2a3a; display: flex; align-items: center; justify-content: center; gap: 15px; }}
    .pos {{ color: #27ae60; background: #e8f5e9; padding: 4px 12px; border-radius: 10px; font-size: 24px; }}
    .speaker-icon {{ cursor: pointer; font-size: 32px; }}
    .phonetic {{ color: #7f8c8d; font-size: 22px; margin-top: 10px; font-style: italic; }}
</style>

<script>
    const target = "{target_word}";
    const container = document.getElementById('input-container');
    const boxes = [];
    const audio = document.getElementById('word-audio');

    function playAudio() {{ audio.currentTime = 0; audio.play(); }}

    for (let i = 0; i < target.length; i++) {{
        const input = document.createElement('input');
        input.type = 'text';
        input.maxLength = 1;
        input.className = 'letter-box';
        container.appendChild(input);
        boxes.push(input);

        input.addEventListener('input', (e) => {{
            if (e.target.value && i < target.length - 1) boxes[i+1].focus();
            checkWord();
        }});

        input.addEventListener('keydown', (e) => {{
            if (e.key === 'Backspace' && !e.target.value && i > 0) boxes[i-1].focus();
        }});
    }}
    setTimeout(() => boxes[0].focus(), 200);

    function checkWord() {{
        const current = boxes.map(b => b.value).join('').toLowerCase();
        if (current.length === target.length) {{
            if (current === target) {{
                boxes.forEach(b => b.classList.add('correct'));
                // 【自动化跳转核心】
                // 在父窗口查找那个带有 "下一题" 文字的按钮并点击它
                setTimeout(() => {{
                    const buttons = window.parent.document.querySelectorAll('button');
                    const nextBtn = Array.from(buttons).find(el => el.innerText.includes('下一题'));
                    if (nextBtn) nextBtn.click();
                }}, 800);
            }} else {{
                boxes.forEach(b => b.classList.add('wrong'));
            }}
        }} else {{
            boxes.forEach(b => b.classList.remove('wrong', 'correct'));
        }}
    }}
</script>
"""

# --- 6. 渲染 HTML 组件 ---
components.html(custom_component, height=520)

# --- 7. 辅助控制 (这些按钮是 JS 触发跳转的依据) ---
st.divider()
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    if st.button("⬅️ 上一题", use_container_width=True):
        st.session_state.current_idx -= 1
        st.rerun()
with c2:
    if st.button("🔊 播放语音", use_container_width=True):
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{audio_b64}">', unsafe_allow_html=True)
with c3:
    # 这个按钮非常重要！JS 拼对后会通过查找 "下一题" 这几个字来点击它
    if st.button("下一题 ➡️", type="primary", use_container_width=True):
        st.session_state.current_idx += 1
        st.rerun()