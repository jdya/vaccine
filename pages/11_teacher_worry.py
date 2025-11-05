#pip install streamlit openai

# ========================================
# 교사용: 고민/멘탈 케어 (비공개, 고도화)
# ========================================

import streamlit as st

from utils.session_manager import require_teacher_or_admin, get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id, new_conversation_for_current_page
from ai.deepseek_handler import generate_chat_response, stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, render_new_chat_controls

st.set_page_config(page_title="🤔 교사 고민", page_icon="🤔", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()
set_current_page('worry')

st.title("🤔 교사 고민 (완전 비공개)")

st.info("이곳의 대화는 비공개 플래그로 저장됩니다. 외부에 공유되지 않도록 설계되었습니다.")

with st.container(border=True):
    st.subheader("대화")
    last_ai = None
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])
        if m['role'] == 'assistant':
            last_ai = m['content']

    prompt = st.chat_input("편하게 고민을 이야기해 주세요. 함께 해결의 실마리를 찾아볼게요...")
    if prompt:
        add_message('user', prompt)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='worry',
            grade=user.get('grade'),
            is_teacher=True,
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            cat_row = get_category_by_name('worry')
            if cat_row:
                save_conversation(user['id'], cat_row['id'], prompt, full_text, session_id=get_current_session_id(), is_private=True)
            st.rerun()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("대화 지우기"):
        clear_messages()
        st.rerun()
with col2:
    if last_ai:
        st.download_button("🗂️ 위로/조언 다운로드(.txt)", data=last_ai, file_name="worry_support.txt")
with col3:
    render_new_chat_controls(page_key='teacher_worry', category_name='worry')
