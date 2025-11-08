import streamlit as st

from utils.session_manager import require_login, get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation

st.set_page_config(page_title="📚 학습 - 독서", page_icon="📚", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()
set_current_page('learning_reading')

st.title("📚 학습 - 독서")
st.caption("예측→읽기→요약→감상 단계로 글의 핵심을 파악해요.")

with st.container(border=True):
    st.subheader("대화")
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])

    prompt = st.chat_input("책/글 제목과 궁금한 점을 적어주세요… 예: 소나기의 주제")
    if prompt:
        add_message('user', prompt)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='reading',
            grade=user.get('grade'),
            is_teacher=False,
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            cat_row = get_category_by_name('reading')
            if cat_row and user:
                save_conversation(
                    user_id=user['id'],
                    category_id=cat_row['id'],
                    user_message=prompt,
                    ai_response=full_text,
                    session_id=get_current_session_id(),
                    is_private=False
                )
            st.rerun()

col1, col2 = st.columns(2)
with col1:
    if st.button("대화 지우기"):
        clear_messages()
        st.rerun()
with col2:
    st.caption("주제·주장·근거, 글 구조, 표현(비유/상징)을 함께 살펴봐요.")