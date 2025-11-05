import streamlit as st

from utils.session_manager import require_login, get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id, new_conversation_for_current_page
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, render_new_chat_controls
from ai.deepseek_handler import stream_chat_response
from voice.tts_handler import synthesize_to_file
from database.supabase_manager import get_category_by_name, save_conversation

st.set_page_config(page_title="📚 학습 - 수학", page_icon="📚", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()
set_current_page('learning_math')

st.title("📚 학습 - 수학")

cat = "math"

with st.container(border=True):
    st.subheader("대화")
    last_ai_text = None
    for m in get_messages():
        if m['role'] == 'user':
            st.chat_message("user").write(m['content'])
        else:
            st.chat_message("assistant").write(m['content'])
            last_ai_text = m['content']

    if last_ai_text and st.button("🔊 마지막 AI 답변 듣기"):
        mp3_path = synthesize_to_file(last_ai_text, filename="learn_math_last_ai.mp3")
        if mp3_path:
            st.audio(mp3_path)
        else:
            st.error("Failed to generate audio.")

    prompt = st.chat_input("수학 질문이나 연습을 해보세요...")
    if prompt:
        add_message('user', prompt)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category=cat,
            grade=user.get('grade'),
            is_teacher=(user.get('role') == 'teacher'),
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            cat_row = get_category_by_name(cat)
            if cat_row:
                save_conversation(
                    user_id=user['id'],
                    category_id=cat_row['id'],
                    user_message=prompt,
                    ai_response=full_text,
                    session_id=get_current_session_id(),
                    is_private=False
                )
            st.rerun()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("대화 비우기"):
        clear_messages()
        st.rerun()
with col2:
    st.caption("학년과 역할에 맞춰 말투와 난이도가 조정돼요.")
with col3:
    render_new_chat_controls(page_key='learning_math', category_name='math')